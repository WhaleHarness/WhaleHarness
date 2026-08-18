#!/bin/bash
# 精选上架管道:外部 curated 插件的唯一上架入口(参数化 source 溯源)。
# 用法: bash deploy/publish_curated.sh <src_dir> <entry.json> [--dry-run]
# 与 publish_plugin.sh 的分工:自家插件走 publish_plugin.sh(source 固定 WhaleHarness/WhaleHarness);
# 外部精选插件走本管道——source.repo/source.commit 由 entry.json 注入,保留外部仓库溯源。
# 纪律:商店资产(plugins.json/tarball/短链)只有 publish_plugin.sh 与本管道写;审计管道只写审计产物;
#       本管道不改裁决尺子(review-submission.py 原样调用),不动审计管道。
# entry.json 必填: description, description_en, source.repo(owner/name), source.commit(7-40 位 hex)
# entry.json 可选: name(默认=源码 package.json name 的 unscoped basename), tool(默认空),
#                  dsh_compat(默认 ^0.1.0-rc.6)。version 一律取源码 package.json,防漂移。
set -euo pipefail
cd "$(dirname "$0")/.."

SRC=$1
ENTRY=$2
DRY=0
for a in "$@"; do [ "$a" = "--dry-run" ] && DRY=1; done

if [ -z "$SRC" ] || [ -z "$ENTRY" ]; then
  echo "用法: bash deploy/publish_curated.sh <src_dir> <entry.json> [--dry-run]"
  echo "  entry.json 必填: description, description_en, source.repo(owner/name), source.commit(hex)"
  exit 1
fi
[ -f "$SRC/package.json" ] || { echo "src 目录无 package.json: $SRC"; exit 1; }
[ -f "$ENTRY" ] || { echo "条目文件不存在: $ENTRY"; exit 1; }

# 校验 entry 并读出 ASCII 字段(source 溯源)到 shell 变量;中文字段只在 manifest 步骤由 python 读。
read -r NAME VERSION REPO COMMIT < <(python3 - "$ENTRY" "$SRC" <<'PYEOF'
import json, sys, re
entry = json.load(open(sys.argv[1]))
src = json.load(open(sys.argv[2] + '/package.json'))
for k in ('description', 'description_en', 'source'):
    if k not in entry or not entry[k]:
        sys.exit('entry 缺字段: ' + k)
repo = str(entry['source'].get('repo', ''))
commit = str(entry['source'].get('commit', ''))
if not re.match(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$', repo):
    sys.exit('source.repo 格式错: ' + repr(repo) + ' (应为 owner/name)')
if not re.match(r'^[0-9a-f]{7,40}$', commit):
    sys.exit('source.commit 格式错: ' + repr(commit) + ' (应为 7-40 位 hex)')
name = str(entry.get('name') or src['name'].split('/')[-1])
if not re.match(r'^[a-z0-9][a-z0-9-]*$', name):
    sys.exit('store name 格式错: ' + repr(name) + ' (应为小写字母数字连字符, 可用 entry.name 覆盖)')
print(name, src['version'], repo, commit)
PYEOF
)

COMMIT12=$(printf '%.12s' "$COMMIT")

if [ "$DRY" = "1" ]; then
  TGZ="/tmp/publish_curated_dry/$NAME-$VERSION.tgz"
  mkdir -p /tmp/publish_curated_dry
else
  TGZ="dist/plugins/$NAME-$VERSION.tgz"
fi

echo "[1/7] 可复现打包 $NAME $VERSION (source: $REPO @ $COMMIT12)"
bash deploy/build_tgz.sh "$SRC" "$TGZ"

echo "[2/7] 静态审查(review-submission.py 原样, REJECT 即停)"
python3 tools/review-submission.py "$TGZ" --manifest dist/plugins.json | tee /tmp/publish_curated_review.txt || true
if grep -q "verdict: REJECT" /tmp/publish_curated_review.txt && ! grep -q "already in the store" /tmp/publish_curated_review.txt; then
  echo "审查 REJECT,发布中止"; exit 1
fi

echo "[3/7] manifest 条目(source.repo/commit 从 entry 注入)"
SHA=$(shasum -a 256 "$TGZ" | cut -d' ' -f1)
SHA12=$(printf '%.12s' "$SHA")
python3 - "$SHA" "$ENTRY" "$SRC" "$DRY" "$NAME" "$VERSION" "$REPO" "$COMMIT" <<'PYEOF'
import json, sys
sha, entry_path, src_path, dry, name, version, repo, commit = sys.argv[1:9]
dry = dry == '1'
entry = json.load(open(entry_path))
tarball = '/plugins/' + name + '-' + version + '.tgz'
item = {
    'name': name,
    'version': version,
    'tool': entry.get('tool', ''),
    'description': entry['description'],
    'tarball': tarball,
    'install': 'dsh plugin --profile web add -w https://whaleharness.com' + tarball + '?src=install',
    'sha256': sha,
    'dsh_compat': entry.get('dsh_compat', '^0.1.0-rc.6'),
    'description_en': entry['description_en'],
    'source': {'repo': repo, 'commit': commit,
               'build': 'reproducible: deploy/build_tgz.sh, epoch=mtime-of-oldest-file'},
}
if dry:
    print('DRY-RUN 条目(未写 manifest, 未部署):')
    print(json.dumps(item, ensure_ascii=False, indent=1))
    print('>>> source.repo=' + repo + '  source.commit=' + commit + '  (注入自 entry, 非硬编码)')
    sys.exit(0)
p = 'dist/plugins.json'
d = json.load(open(p))
found = False
for i, e in enumerate(d['plugins']):
    if e['name'] == name:
        d['plugins'][i] = item
        found = True
        break
if not found:
    d['plugins'].append(item)
json.dump(d, open(p, 'w'), ensure_ascii=False, indent=1)
print('manifest ' + ('updated' if found else 'appended') + ': ' + name + ' ' + version + ' repo=' + repo + ' commit=' + commit[:12] + ' sha=' + sha[:12])
PYEOF

if [ "$DRY" = "1" ]; then
  echo "DRY-RUN 到此为止:未改 dist/plugins.json、未重生成短链、未部署、未清缓存。"
  exit 0
fi

echo "[4/7] 重生成短链"
python3 deploy/gen_p_short.py

echo "[5/7] 部署 VPS(tar 单流)+nginx"
COPYFILE_DISABLE=1 tar czf /tmp/publish_curated.tgz -C dist plugins/$NAME-$VERSION.tgz plugins.json
COPYFILE_DISABLE=1 tar czf /tmp/publish_curated_inc.tgz -C deploy whaleharness-p-short.inc
scp -F /tmp/moby-ssh.cfg /tmp/publish_curated.tgz wh:/tmp/publish_curated.tgz
scp -F /tmp/moby-ssh.cfg /tmp/publish_curated_inc.tgz wh:/tmp/publish_curated_inc.tgz
ssh -F /tmp/moby-ssh.cfg wh 'cd /srv/whaleharness && tar xzf /tmp/publish_curated.tgz 2>/dev/null; tar xzf /tmp/publish_curated_inc.tgz -C /tmp 2>/dev/null; cp /tmp/whaleharness-p-short.inc /etc/nginx/whaleharness-p-short.inc; chmod 644 /srv/whaleharness/plugins.json /srv/whaleharness/plugins/*.tgz; nginx -t && systemctl reload nginx'

echo "[6/7] sync-listings(派生文件同步)+CF 清缓存"
ssh -F /tmp/moby-ssh.cfg wh 'cd /srv/whaleharness && python3 /opt/whaleharness-audit/tools/sync-listings.py --base /srv/whaleharness --out /srv/whaleharness && chmod 644 /srv/whaleharness/agent.json /srv/whaleharness/llms.txt /srv/whaleharness/sitemap.xml'
CF_TOKEN=$(cat cf.txt)
curl -s --max-time 20 -X POST 'https://api.cloudflare.com/client/v4/zones/8792301b0a58d9bff1140a16c868efc6/purge_cache' -H "Authorization: Bearer $CF_TOKEN" -H 'Content-Type: application/json' -d '{"purge_everything":true}' > /dev/null

echo "[7/7] 线上验证"
sleep 2
TCODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "https://whaleharness.com/plugins/$NAME-$VERSION.tgz")
LCODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "https://whaleharness.com/p/$NAME")
read -r MSHA MSRC < <(curl -s --max-time 10 "https://whaleharness.com/plugins.json" | python3 -c "import json,sys; d=json.load(sys.stdin); e=[x for x in d['plugins'] if x['name']=='$NAME'][0]; print(e['sha256'], e['source']['repo'])")
MSHA12=$(printf '%.12s' "$MSHA")
echo "tarball HTTP $TCODE | 短链 HTTP $LCODE | 线上 source.repo=$MSRC | sha 头 12 位 本地=$SHA12 线上=$MSHA12"
[ "$TCODE" = "200" ] && [ "$MSHA12" = "$SHA12" ] && [ "$MSRC" = "$REPO" ] && echo "发布完成: $NAME $VERSION (repo $REPO @ $COMMIT12)" || echo "验证失败,检查上表"
