# dsh-audit — DeepSeek Harness 插件检验工具（WhaleHarness 出品）

> 我们每天用它审核每一个进入 whaleharness.com 的插件。现在它开源，任何人都能对任何 DSH 插件跑一遍。

## 它检查什么

对任意一个插件 tgz（或 npm 包目录），dsh-audit 执行白箱静态审查：

- 结构：标准发布形态（package.json / cordis.patch.yml / dsh.bundle 声明）、npm 命名与版本规范、重复上架
- 红线（阻止）：
  - subprocess 未声明（raw child_process 而非 dsh.runtime:host 的受控服务）
  - 改宿主源码（install 脚本 patch 宿主 dsh-* 文件）
  - 未声明的外传端点（foreign URL 非豁免 sink）
  - 壳脚本 curl|bash（不可审的安装路径）
- 格式（FORMAT-ISSUE）：缺 bundle.patch / 权限形态 / 供应商保留路径
- 警告：非官方 peer、vendored 库大文件、foreign URL 字面量
- 联合 bundle：patch 引用本包自身或已声明 dependencies 的包=合法（聚合 profile 模式），未声明=阻止

## 用法

python3 review-submission.py path/to/plugin-0.1.0.tgz

输出: ISSUES (blocking) / WARNINGS (manual review) / verdict。

## 为什么可信

- 每个判定都带证据：裁决输出具体到文件行号（如 "patch loads undeclared foreign package 'x'"）。
- 我们自己的五批品鉴（40+ 外部推荐，9 收 31 否）全部过了这套检查+沙箱。
- 它只静态判定"该拦的"，不替代人工语义验收——红线与形态交给它，语义交给鲸。

## 关联件

- whaleharness.com/audit.json — 全生态 2743+ 仓库的公开审计裁定
- whaleharness.com/rankings.json — 推荐度×验证的生态共识榜（每 6h 刷新）
- whale-plugin-dev — 生产者 Skill（教材：怎么写才能过）

---
MIT。由 WhaleHarness 维护。你验，我装。
