#!/bin/bash
# 发布管道:唯一写商店资产的自动化。用法: bash deploy/publish_plugin.sh <插件目录>
# 决策(我点头)→ 此管道全链完成:打包→审查→更新 manifest→短链→部署→清缓存→验证。
# 纪律:商店资产(plugins.json/tarball/短链)只有本管道写;审计管道只写审计产物。
set -euo pipefail
cd "$(dirname "$0")/.."

SRC=$1
if [ -z "$SRC" ]; then echo "用法: bash deploy/publish_plugin.sh <插件目录>"; exit 1; fi
NAME=$(python3 -c "import json; print(json.load(open('$SRC/package.json'))['name'])")
VERSION=$(python3 -c "import json; print(json.load(open('$SRC/package.json'))['version'])")
TGZ="dist/plugins/$NAME-$VERSION.tgz"
COMMIT=$(git -C github-repo log -1 --format=%h 2>/dev/null || echo "uncommitted")

echo "[1/6] 可复现打包 $NAME $VERSION"
bash deploy/build_tgz.sh "$SRC" "$TGZ"

echo "[2/6] 静态审查(REJECT 即停;仅「已在商店」误报放行——那是更新场景)"
python3 tools/review-submission.py "$TGZ" --manifest dist/plugins.json | tee /tmp/publish_review.txt || true
if grep -q "verdict: REJECT" /tmp/publish_review.txt && ! grep -q "already in the store" /tmp/publish_review.txt; then
  echo "审查 REJECT,发布中止"; exit 1
fi

echo "[3/6] 更新 manifest(sha256+commit+install)"
SHA=$(shasum -a 256 "$TGZ" | cut -d' ' -f1)
python3 - "$NAME" "$VERSION" "$TGZ" "$SHA" "$COMMIT" <<'PYEOF'
import json, sys
name, version, tgz, sha, commit = sys.argv[1:6]
p = 'dist/plugins.json'
d = json.load(open(p))
found = False
for e in d['plugins']:
    if e['name'] == name:
        found = True
        e['version'] = version
        e['tarball'] = '/' + tgz.split('/', 1)[1]
        e['install'] = 'dsh plugin --profile web add -w https://whaleharness.com/' + e['tarball'] + '?src=install'
        e['sha256'] = sha
        e['source'] = {'repo': 'WhaleHarness/WhaleHarness', 'commit': commit,
                       'build': 'reproducible: deploy/build_tgz.sh, epoch=mtime-of-oldest-file'}
if not found:
    print('manifest 无此插件条目,发布中止(新插件需先人工写入条目与描述)')
    sys.exit(1)
json.dump(d, open(p, 'w'), ensure_ascii=False, indent=1)
print('manifest updated:', name, version, sha[:12], commit)
PYEOF

echo "[4/6] 重生成短链"
python3 deploy/gen_p_short.py

echo "[5/6] 部署 VPS(tar 单流)+nginx+清缓存"
tar czf /tmp/publish.tgz -C dist plugins/$NAME-$VERSION.tgz plugins.json
tar czf /tmp/publish_inc.tgz -C deploy whaleharness-p-short.inc
scp -F /tmp/moby-ssh.cfg /tmp/publish.tgz wh:/tmp/publish.tgz
scp -F /tmp/moby-ssh.cfg /tmp/publish_inc.tgz wh:/tmp/publish_inc.tgz
ssh -F /tmp/moby-ssh.cfg wh 'cd /srv/whaleharness && tar xzf /tmp/publish.tgz 2>/dev/null; tar xzf /tmp/publish_inc.tgz -C /tmp 2>/dev/null; cp /tmp/whaleharness-p-short.inc /etc/nginx/whaleharness-p-short.inc; chmod 644 /srv/whaleharness/plugins.json /srv/whaleharness/plugins/*.tgz; nginx -t && systemctl reload nginx'
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
