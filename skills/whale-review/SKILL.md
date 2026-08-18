---
name: whale-review
description: WhaleHarness plugin review procedure: static checks, verification loop, publish or public rejection. Load when reviewing a submission to whaleharness.com.
license: MIT
---

# WhaleHarness 插件审核流程

## 自动检查（tools/review-submission.py）

- 结构：npm 格式（package/ 前缀）、package.json 完整、dsh.bundle.patch = ./cordis.patch.yml
- 身份：包名/版本格式、与站上重名检测（对 dist/plugins.json）
- 边界：cordis.patch.yml 只 insert 自己包名的行
- 依赖：peerDependencies 只 @deepseek-ai/*（其他 → 警告人工评估）
- 红线（一票否决）：child_process / eval / 外网请求（非本站）/ 敏感路径 / 外链字面量
- DSH boot 杀手：参数 schema 的 required: false（DSL 拒绝，boot 报错）
- 注释剥离后扫描（注释里的字样不算违规）

## 手动验证环（全部通过才上架）

1. DSH_HOME=dsh-test-home dsh plugin --profile headless add -w <tarball>
2. dsh --profile headless --dump-config | grep <包名>  （行必须出现）
3. boot web profile 起 3999 端口：HTTP 200 零错误（抓 register 类错误——缺 output 声明会在这里炸）
4. headless 端到端：模型真实调用工具，输出符合预期

## 上架 / 退回

- 上架：tarball → dist/plugins/ → shasum -a 256 → 写 plugins.json → scp 部署 → agent.json 重新生成
- 退回：REVIEW-<name>.md 写阻塞项 + 修改建议 + 优点记录 → 公开贴投稿箱同目录 → GitHub Discussions 汇总
- 口诀：审核是公开记录，不是私下判断
