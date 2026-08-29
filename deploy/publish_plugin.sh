#!/bin/bash
# 发布管道:唯一写商店资产的自动化。用法: bash deploy/publish_plugin.sh <插件目录> [--dry-run]
# 决策(我点头)→ 此管道全链完成:打包→审查→更新 manifest→短链→部署→清缓存→验证。
# 纪律:商店资产(plugins.json/tarball/短链)只有本管道写;审计管道只写审计产物。
# 停门:审查器 review-submission.py 退出码非零(=RED-LINE 或 FORMAT-ISSUE)即中止;PROCEED/EXCLUDED 放行。
set -euo pipefail
cd "$(dirname "$0")/.."

# [0] 双源同步校验:发布前 VPS 线上 plugins.json 必须与本机 dist/plugins.json 一致(防回退)
VPS_PJ=$(mktemp /tmp/vps-plugins.XXXXXX.json)
trap 'rm -f "$VPS_PJ"' EXIT
if ! scp -F /tmp/moby-ssh.cfg wh:/srv/whaleharness/plugins.json "$VPS_PJ" 2>/dev/null; then
  curl -s --max-time 20 "https://whaleharness.com/plugins.json" -o "$VPS_PJ" || { echo "无法拉取 VPS plugins.json,发布中止"; exit 1; }
fi
python3 - "$VPS_PJ" dist/plugins.json <<'PYEOF'
import json, sys
vps, local = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
v, l = vps['plugins'], local['plugins']
vd = {e['name']: e for e in v}
ld = {e['name']: e for e in l}
diffs = []
if len(v) != len(l):
    diffs.append('count: vps=%d local=%d' % (len(v), len(l)))
for name in sorted(set(vd) | set(ld)):
    a, b = vd.get(name), ld.get(name)
    if a is None:
        diffs.append('only-local: %s' % name)
    elif b is None:
        diffs.append('only-vps: %s' % name)
    elif a.get('version') != b.get('version') or a.get('sha256') != b.get('sha256'):
        diffs.append('%s: vps=%s/%s local=%s/%s' % (name, a.get('version'), (a.get('sha256') or '')[:12], b.get('version'), (b.get('sha256') or '')[:12]))
if diffs:
    print('双源同步校验失败(VPS 线上与本机 dist/plugins.json 不一致),发布中止:')
    for d in diffs:
        print('  - ' + d)
    sys.exit(1)
print('双源同步校验通过: %d 款 name/version/sha256 一致' % len(v))
PYEOF

SRC=$1
DRY=0
for a in "$@"; do [ "$a" = "--dry-run" ] && DRY=1; done
if [ -z "$SRC" ]; then echo "用法: bash deploy/publish_plugin.sh <插件目录> [--dry-run]"; exit 1; fi
[ -f "$SRC/package.json" ] || { echo "src 目录无 package.json: $SRC"; exit 1; }
NAME=$(python3 -c "import json; print(json.load(open('$SRC/package.json'))['name'])")
VERSION=$(python3 -c "import json; print(json.load(open('$SRC/package.json'))['version'])")
COMMIT=$(git -C github-repo log -1 --format=%h 2>/dev/null || echo "uncommitted")

if [ "$DRY" = "1" ]; then
  TGZ="/tmp/publish_plugin_dry/$NAME-$VERSION.tgz"
  mkdir -p /tmp/publish_plugin_dry
else
  TGZ="dist/plugins/$NAME-$VERSION.tgz"
fi

echo "[1/6] 可复现打包 $NAME $VERSION"
bash deploy/build_tgz.sh "$SRC" "$TGZ"

echo "[2/6] 静态审查(RED-LINE/FORMAT-ISSUE 即停,以审查器退出码为准)"
if ! python3 tools/review-submission.py "$TGZ" --manifest dist/plugins.json > /tmp/publish_review.txt 2>&1; then
  echo "审查阻塞(RED-LINE/FORMAT-ISSUE,退出码非零),发布中止"
  cat /tmp/publish_review.txt
  exit 1
fi

echo "[3/6] 更新 manifest(sha256+commit+install)"
SHA=$(shasum -a 256 "$TGZ" | cut -d' ' -f1)
python3 - "$NAME" "$VERSION" "$SHA" "$COMMIT" "$DRY" <<'PYEOF'
import json, sys
name, version, sha, commit, dry = sys.argv[1:6]
dry = dry == '1'
tarball = '/plugins/' + name + '-' + version + '.tgz'
source = {'repo': 'WhaleHarness/WhaleHarness', 'commit': commit,
          'build': 'reproducible: deploy/build_tgz.sh, epoch=mtime-of-oldest-file'}
p = 'dist/plugins.json'
d = json.load(open(p))
found = False
for e in d['plugins']:
    if e['name'] == name:
        found = True
        e['version'] = version
        e['tarball'] = tarball
        e['install'] = 'dsh plugin --profile web add -w https://whaleharness.com' + tarball + '?src=install'
        e['sha256'] = sha
        e['source'] = source
if dry:
    if not found:
        print('DRY-RUN: manifest 无此条目(新插件需先人工写入条目与描述),真实运行会中止')
        sys.exit(1)
    updated = [x for x in d['plugins'] if x['name'] == name][0]
    print('DRY-RUN: 将在 manifest 更新条目(未写):')
    print(json.dumps(updated, ensure_ascii=False, indent=1))
    print('>>> source.repo=' + source['repo'] + ' source.commit=' + commit)
    sys.exit(0)
if not found:
    print('manifest 无此插件条目,发布中止(新插件需先人工写入条目与描述)')
    sys.exit(1)
json.dump(d, open(p, 'w'), ensure_ascii=False, indent=1)
print('manifest updated:', name, version, sha[:12], commit)
PYEOF

if [ "$DRY" = "1" ]; then
  echo "DRY-RUN 到此为止:未改 dist/plugins.json、未重生成短链、未部署、未清缓存。"
  exit 0
fi

echo "[4/6] 重生成短链"
python3 deploy/gen_p_short.py

echo "[5/6] 部署 VPS(tar 单流)+nginx+清缓存"
COPYFILE_DISABLE=1 tar czf /tmp/publish.tgz -C dist plugins/$NAME-$VERSION.tgz plugins.json
COPYFILE_DISABLE=1 tar czf /tmp/publish_inc.tgz -C deploy whaleharness-p-short.inc
scp -F /tmp/moby-ssh.cfg /tmp/publish.tgz wh:/tmp/publish.tgz
scp -F /tmp/moby-ssh.cfg /tmp/publish_inc.tgz wh:/tmp/publish_inc.tgz
ssh -F /tmp/moby-ssh.cfg wh 'cd /srv/whaleharness && tar xzf /tmp/publish.tgz 2>/dev/null; tar xzf /tmp/publish_inc.tgz -C /tmp 2>/dev/null; cp /tmp/whaleharness-p-short.inc /etc/nginx/whaleharness-p-short.inc; chmod 644 /srv/whaleharness/plugins.json /srv/whaleharness/plugins/*.tgz; nginx -t && systemctl reload nginx'
ssh -F /tmp/moby-ssh.cfg wh 'cd /srv/whaleharness && python3 /opt/whaleharness-audit/tools/sync-listings.py --base /srv/whaleharness --out /srv/whaleharness && python3 /usr/local/bin/gen-categories.py /srv/whaleharness/plugins.json /srv/whaleharness/plugins > /tmp/categories.json && cp /tmp/categories.json /srv/whaleharness/categories.json && chmod 644 /srv/whaleharness/agent.json /srv/whaleharness/llms.txt /srv/whaleharness/sitemap.xml /srv/whaleharness/categories.json'
CF_TOKEN=$(cat cf.txt)
curl -s --max-time 20 -X POST 'https://api.cloudflare.com/client/v4/zones/8792301b0a58d9bff1140a16c868efc6/purge_cache' -H "Authorization: Bearer $CF_TOKEN" -H 'Content-Type: application/json' -d '{"purge_everything":true}' > /dev/null

echo "[6/6] 线上验证"
sleep 2
TCODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "https://whaleharness.com/plugins/$NAME-$VERSION.tgz")
LCODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "https://whaleharness.com/p/$NAME")
MSHA=$(curl -s --max-time 10 "https://whaleharness.com/plugins.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print([e['sha256'] for e in d['plugins'] if e['name']=='$NAME'][0])")
echo "tarball HTTP $TCODE | 短链 HTTP $LCODE | manifest sha 头 12 位 vs 本地"
echo "$MSHA" | cut -c1-12
echo "$SHA" | cut -c1-12
[ "$TCODE" = "200" ] && [ "$(echo "$MSHA" | cut -c1-12)" = "$(echo "$SHA" | cut -c1-12)" ] && echo "发布完成: $NAME $VERSION (commit $COMMIT)" || echo "验证失败,检查上表"
