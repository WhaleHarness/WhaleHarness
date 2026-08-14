# WhaleHarness 插件审核清单（站方内部流程）

> 每个投稿按此清单逐项执行，全部通过才上架。审核过程公开（投稿箱公开可读）。

## 0. 收件
- 投稿箱：/srv/whaleharness-submissions/submit/<token>/<name>-<version>.tgz
- 只收 .tgz / .tar.gz；5MB 上限；nginx 已强制。

## 1. 结构检查
- [ ] tarball 顶层是 package/ 目录（npm 格式）
- [ ] package.json 含 name、version、dsh.bundle.patch 指向 cordis.patch.yml
- [ ] cordis.patch.yml 只 insert 自己包名的行，不碰其他 id
- [ ] 包名不与现有插件冲突

## 2. 依赖审计
- [ ] peerDependencies 只列 @deepseek-ai/* 官方包，版本范围写 ^0.1.0-rc.6
- [ ] 无新增非官方 npm 依赖（需要新依赖的：人工评估来源、体积、许可证）
- [ ] 源码中无 fetch/http 外传、无 eval、无子进程（child_process）调用
- [ ] 无读取 DSH 凭据/敏感路径的代码（.credentials、~/.ssh 等）

## 3. 本地验证（DSH_HOME=dsh-test-home）
- [ ] dsh plugin --profile headless add -w <tarball 本地路径> 成功且 bundles reconcile
- [ ] dsh --profile whaletest --dump-config 出现插件行
- [ ] boot 无错误（web profile 起 3999 端口，HTTP 200）
- [ ] headless 端到端：真实调用插件工具，输出符合预期

## 4. 行为检查
- [ ] 工具输出不包含误导内容、不冒充站方
- [ ] 返回链接使用 https://whaleharness.com
- [ ] 错误路径有明确报错，不崩溃

## 5. 上架
- [ ] 打包命名 <name>-<version>.tgz，上传 /srv/whaleharness/plugins/
- [ ] shasum -a 256 写入 plugins.json 对应条目
- [ ] 首页卡片信息（description/tool/install）更新
- [ ] chmod -R a+rX /srv/whaleharness；curl https 全项 200 + sha256 核对

## 退回
- 未通过项写成一段退回原因，公开贴在投稿箱同目录 REVIEW-<name>.md
