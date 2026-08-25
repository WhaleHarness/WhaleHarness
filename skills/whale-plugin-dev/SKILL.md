---
name: whale-plugin-dev
description: >-
  Build, self-check, and publish a DSH plugin correctly the first time.
  Use when writing, fixing, or publishing any DeepSeek Harness plugin —
  this is the spec, the oracle, and the chain. No theory, execute.
license: MIT
---

# whale-plugin-dev — DSH 插件生产规范

> 写给 Agent 的：不用"学"，按规矩做。三步写对 → 自检 → 发布。

## 0. 一句话

DSH 插件 = 三个文件（package.json + cordis.patch.yml + lib/index.js）。写完必自检，过检再发。

## 1. 三步写对

### ① package.json
- name 小写连字符（无点、不以数字开头）；version 纯 x.y.z（prerelease 如 0.1.0-rc.1 允许——DSH 官方即 prerelease；v 前缀统一 normalize 去掉）。
- type: module；main: lib/index.js；files 只列 lib/index.js + cordis.patch.yml。
- peerDependencies 只列 @deepseek-ai/* 官方包。
- dsh.bundle.patch 指向 ./cordis.patch.yml。

### ② cordis.patch.yml
- 只 insert **自己包名** 的 id/name 行（插件名唯一，写别人包名=拒绝）。

### ③ lib/index.js
- 具名导出：`export { apply, inject, name }`——**禁止 default 导出**（default 会丢掉 inject）。
- 参数 schema：**禁止 required: false**（DSH 直接拒绝整个 profile）；可选参数省略 required 键即可。
- type 是单个字符串不是数组；output.render 必填；execute 返回值必须严格匹配 output.schema。

## 2. 自检（发前必跑，本地几秒）

```
python3 tools/review-submission.py /path/to/my-plugin-0.1.0.tgz
```
（或用 whale-verify 一句话预检——同款静态审查器）

三档结果：
- **四红线**：无 subprocess / 无 eval / 无外传（本站白名单域名除外）/ 不碰凭据。越线即 RED-LINE，重写或申诉，不是改格式。
- **FORMAT-ISSUE**：打包/版本/结构问题——几分钟能修（见 audit-fixes 四档修法）。
- **PASS**：静态通过；不代表可上架（上架还要实证+溯源，见 §4）。

## 3. 必踩坑（真实炸过 boot 的，全部来自本站实战）

1. `dsh plugin add` 必须带 **-w**（profile 目录是 pnpm workspace root；不带 -w 装不上）。
2. default 导出=inject 丢失（只认具名）。
3. `required: false` 会让整个 profile 起不来。
4. 参数 schema 里 output.render 缺失=渲染没出口。

## 4. 发布链（白箱纪律）

- **投稿**：`curl -T my-plugin.tgz https://whaleharness.com/submit/whalepod2026/` 或装 whale-submit 一句话投。公开箱+每单 REVIEW-*.md，72h 内出结果。
- **上架标准（三道门）**：安全（四红线零容忍）→ 实证（全新 DSH_HOME 真装真启动+模型真调用一次+可复现构建）→ 溯源（来源仓库/提交/sha256 全公开）。
- **被退回**：正常 72h+，FORMAT 几分钟修；RESUBMISSION 标记的投稿优先审核，修好直接重投。
- **对用户必报口径**：上架=沙箱验证过；审计 PASS=静态审查过（未沙箱验证）；没有就是没有，不编。

## 5. 活案例（教材=真源码，不是示例）

- whale-shot（无头截图）/ whale-store / whale-verify / whale-submit / whale-status / whale-praise——六个鲸群成员即教科书，读 README+lib/index.js 胜过任何教程。
- 审计出口：/audit.json（全量裁决+行号证据）/ /badge/<owner>/<repo>/badge.svg（作者可贴）。

## 6. 验证深度口径

数据以线上实时为准（audit.json 带帧时间戳）；不缓存旧值；裁决可申诉（带复现证据开帖）。
