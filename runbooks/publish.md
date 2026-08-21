# Runbook: 插件发布与更新

## 触发场景
自家插件新版本发布 / 商店插件更新 / 外部投稿上架。

## 步骤

### 1. 前置(源码侧)
- 代码改完 node --check(JS)
- 版本号升级 package.json
- 源码提交 github-repo 并 push(发布管道要读 commit)
- 红线自检:review-submission.py 跑一遍,只允许「already in the store」一条

### 2. 发布(唯一入口)
bash deploy/publish_plugin.sh <插件目录> [--dry-run]
管道自动:打包(可复现)→审查(RED-LINE/FORMAT-ISSUE 即停,以审查器退出码为准)→manifest(sha256+commit+install)→短链→部署→清缓存→线上验证
- 新插件(manifest 无条目):管道会中止,先手工写条目与描述再跑

### 3. 验证输出
管道末行「发布完成: name version (commit)」;tarball 200、短链 302、sha 头 12 位一致

## 精选上架(外部 curated 插件)

外部精选插件(非自家 whale-*)走 publish_curated.sh:source.repo/source.commit 参数化注入,
保留外部仓库溯源(首跑教训:publish_plugin.sh 硬编码 source.repo=WhaleHarness/WhaleHarness 会丢外部溯源)。

### 转化前筛选(预检)

候选仓库 clone 进 curated/<name> 后、写 entry.json 之前,先做 name 预检——同一包的重名镜像只上架一次,
否则 publish_curated.sh 的 manifest 写入会「同名 update」覆盖已上架包条目、把 source.repo 换成镜像仓库
(教训:model-config-sync / ha-orchestrator 撞已上架包的重名镜像):

    python3 -c "import json; store={p['name'] for p in json.load(open('dist/plugins.json'))['plugins']}; cand=json.load(open('curated/<name>/package.json'))['name']; print('DUPLICATE 已在架' if cand in store else 'OK 新名')"

- 输出 DUPLICATE → 重名镜像,跳过本单,不进审查不写 entry。
- 输出 OK → 继续下方「用法」。

### 用法

1. 写条目文件 entry.json(必填 description/description_en/source.repo/source.commit;
   version 一律取源码 package.json,不写入 entry 防漂移):

    {
      "name": "dsh-navbar",
      "tool": "navbar",
      "description": "对话节点导航条...作者 vlln,MIT,原仓库 github.com/vlln/dsh-navbar。",
      "description_en": "...",
      "source": {"repo": "vlln/dsh-navbar", "commit": "6e23640bd60c0157043ae5c29a6d80034287b41b"}
    }

2. 干跑(只打包+审查+打印条目,不改 manifest/不部署):

    bash deploy/publish_curated.sh curated/dsh-navbar /tmp/dsh-navbar-entry.json --dry-run

3. 正式上架:

    bash deploy/publish_curated.sh curated/dsh-navbar /tmp/dsh-navbar-entry.json

管道全链:可复现打包→审查(review-submission.py 原样,RED-LINE/FORMAT-ISSUE 即停)→
两阶段 Docker 沙箱(whaleharness-review-docker.sh:stage1 有网装依赖→stage2 禁网 boot)→
manifest(source 从 entry 注入)→短链→部署→sync-listings→CF 清缓存→线上验证(tarball 200/短链 302/sha 与 source.repo 一致)。

### 沙箱验证(默认两阶段 Docker)
- 验证环默认走 VPS 两阶段 Docker:stage1 有网装依赖(硬依赖 zod/schemastery 也能装)、
  stage2 --network none 禁网 + 只读根 + 蜜罐 boot 验证——硬依赖插件不再被单阶段 nobody 出网限制卡住。
- 单阶段 nobody 脚本(whaleharness-review-sandbox.sh)仅适用于 deps=0 插件,已不作为精选上架默认。

### 分工与纪律
- 自家插件(whale-*):publish_plugin.sh,source 固定 WhaleHarness/WhaleHarness。
- 外部 curated:publish_curated.sh,source 由 entry.json 注入。
- 两条管道都只写商店资产;裁决尺子同一把(review-submission.py);不动审计管道。

## 纪律
- 商店资产(plugins.json/tarball/短链)唯一写者=本管道;审计管道绝不写 plugins.json
- 发布后:github-repo 的 plugins/<name> 保持同步(源码可复现)
- 回访:发布后更新受影响口径(agent.json 数字若静态/航的红宝书若涉及)

## 踩坑记录
- [已修 2026-08-18] 停门曾 grep "verdict: REJECT" 而审查器实际输出 RED-LINE/FORMAT-ISSUE → 死代码 fail-open;
  已改为以审查器退出码为准(非零即停),旧 || true 吞码方案一并废弃(礁评审抓出)
- 短链 tar 解包路径 /tmp/deploy/ 前缀多余 → 实际是 /tmp/whaleharness-p-short.inc
- TS 模板写 bash 脚本的 ${} 转义地狱 → 写文件一律用 write 工具或 heredoc 'EOF' 引号版

## 上架后必做(2026-08-17 立,漂移 5+ 次教训)
- 上架(plugins.json 加条目+部署)后,必须跑 VPS 的 sync-listings.py 同步派生文件:
  agent.json/llms.txt/sitemap.xml/index 新上架行——再清 CF 缓存
- [2026-08-19 补] 还必须跑 VPS 的 gen-categories.py 重生成 categories.json(索引页全店视图分类,
  从 tarball package.json keywords 推导):publish_curated.sh 已在第 6 步 sync-listings 之后一并执行
- 派生文件同步(含 categories.json)是发布流程的一步,不是航的维护兜底;漏一步=漂移一次
