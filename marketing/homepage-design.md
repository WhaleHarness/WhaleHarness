# WhaleHarness 首页：人类侧文案与视觉规范

> 用途：whaleharness.com 首页改版「双读者单页面」中**给人类看的半页**——人 10 秒看懂三件事：这是什么（验证过的插件店）/ 规模多大（实时数字）/ 我该干嘛（翻名录·给你的 agent·投稿）。
> 读者：航（执行落地）。本文件是规范，不是实现；所有色值/字号/间距可直接照抄。
> 口径：以 https://whaleharness.com/agent.json 为唯一事实源。数字不写死，全部用占位符。

---

## 0. 口径与占位符（先锁定，再动手）

| 项 | 约定 |
| --- | --- |
| 数字占位符 | <code>{audited}</code> = 审过的公开仓库数（自动审计口径） · <code>{pass}</code> = 通过红线审核数（PASS） · <code>{listed}</code> = 商店在售数 |
| 数字渲染 | 实时渲染。**页面源码任何位置不得出现写死的数字**，文案一律用占位符 |
| 数字关系 | 审过 → 通过 → 上架 是漏斗。通过 ≠ 上架：商店是精选，这条口径必须可见（见 1.2 脚注） |
| 禁营销词 | 不写「最好 / 第一 / 最全 / 唯一 / 领先」及一切最高级 |
| 品牌禁用词 | 赋能、抓手、闭环、颠覆、卷、yyds（whale-brand 纪律） |
| 三打 | verified（验证过）· agent-to-agent（Agent 自装）· 透明（公开可查），三者都是事实描述，不叫卖 |
| 海洋隐喻 | 全页最多一处：配色里的「鲸青」+ 品牌词「鲸群成员 / 船员 / 上船」。文案不额外堆比喻 |

---

## 1. 文案（中英对称，可直接取用）

### 1.1 Hero

**中文**

- 主标题：**每个插件都验证过的商店。**
- 副标题：给 DeepSeek Harness（DSH）的插件站——目录收录一切，商店只上架验证过的。

**English**

- Headline: **A curated plugin store.**
- Subhead: Plugins for DeepSeek Harness (DSH) — the catalog lists everything; the store lists only what passed review.

> 为什么这样写：主标题一句话给结论（「验证过」= 有门槛，「商店」= 是什么），不铺垫；副标题补对象（DSH）与机制（目录 vs 商店）。10 秒内两行读完。

### 1.2 数字横幅（三格，实时渲染）

**中文**

| 数字 | 标签 | 说明 |
| --- | --- | --- |
| <code>{audited}</code> | 审过的公开仓库 | 自动审计，实时更新 |
| <code>{pass}</code> | 通过红线审核 | 静态审查通过（未沙箱验证） |
| <code>{listed}</code> | 商店在售 | 沙箱验证 + 端到端，每条带安装命令与 sha256 |

- 脚注：目录收录一切，商店只上架验证过的——**通过 ≠ 上架**，商店是精选。

**English**

| Number | Label | Note |
| --- | --- | --- |
| <code>{audited}</code> | public repos audited | automated, live |
| <code>{pass}</code> | passed review | static scan passed (not sandbox-verified) |
| <code>{listed}</code> | listed in the store | sandbox-verified end-to-end; one install command + sha256 each |

- Footnote: The catalog lists everything; the store lists only what passed — **passed ≠ listed**, the store curates.

> 为什么这样写：三个数对应用户要的三件事「审过 / PASS / 上架」，标签即口径，不夸大；脚注提前消解「169 通过却 15 上架」的疑问，诚实优先。

### 1.3 三动作卡片

**卡片 1 · 翻名录**

- 中文标题：翻名录
- 中文正文：看验证过的鲸群成员。每个插件一条安装命令、一个 sha256，来源与提交可查。
- English title: Browse the pod
- English body: See the verified pod members. Each ships one install command and a sha256, with source and commit on the record.
- CTA：浏览目录 · Browse the catalog

**卡片 2 · 给你的 agent**

- 中文标题：给你的 agent
- 中文正文：你的 agent 会自己读 agent.json 挑工具。让它打开 whaleharness.com，说出需求。
- 触发语（高亮引用块）：**让你的 agent 打开 whaleharness.com，告诉它你要什么。**
- English title: Give it to your agent
- English body: Your agent reads agent.json and picks its own tools. Point it at whaleharness.com and say what you need.
- Trigger line (highlighted quote): **Tell your agent to open whaleharness.com and say what you need.**

**卡片 3 · 投稿**

- 中文标题：投稿
- 中文正文：把你的插件打包，投到公开投稿箱。审核透明，退回会写明要改哪里。
- English title: Submit a plugin
- English body: Pack your plugin and PUT it to the public submission box. Review is transparent; every rejection lists exactly what to fix.
- CTA：查看投稿流程 · See how to submit

> 为什么这样写：三张卡对应人的三个下一步（翻 / 用 / 投），正文一句一个事实；「给你的 agent」把触发语单独高亮，因为它是唯一的**可直接照抄给 agent 的话**。

### 1.4 「给你的 agent」触发语（独立给全，供复制）

**中文（给人类照抄，对 agent 说）**

<pre>让你的 agent 打开 https://whaleharness.com，告诉它你要什么。
它会自己读 agent.json，找合适的插件，给出安装命令。</pre>

**English (copy-paste for your agent)**

<pre>Tell your agent to open https://whaleharness.com and say what you need.
It reads agent.json, picks its own tools, and gives you the install command.</pre>

---

## 2. 视觉规范

### 2.1 设计原则（3 条，每条给理由）

1. **深色底，一处海洋色**：整页深蓝底 + 唯一强调色「鲸青」。理由：站点受众是开发者，代码/命令在深底上最自然；「深海」定位只靠一个青色呼应，不堆砌海洋元素。
2. **数字第一，文案第二**：横幅数字是首屏视觉重心，字号最大、用等宽数字。理由：人 10 秒里最先扫到的是「规模多大」，数字必须一眼抓到且不跳变。
3. **证据可见**：每个插件条目把 source / commit / sha256 / 安装命令摆在明处。理由：信任来自透明，不来自口号——这些字段就是「验证过」的可见证据。

### 2.2 配色（可直接落地为 CSS 变量）

<pre>:root {
  --wh-bg:            #0A1A2F; /* 页面底色：深海 */
  --wh-surface:       #122841; /* 卡片底 */
  --wh-surface-hover: #183452; /* 卡片悬停 */
  --wh-border:        #1F3A5C; /* 边框/分隔线 */
  --wh-text:          #E8EFF7; /* 主文字（近白） */
  --wh-text-2:        #9DB2C8; /* 次文字/标签 */
  --wh-text-3:        #6B8198; /* 弱说明/脚注 */
  --wh-accent:        #4FD1C5; /* 鲸青：链接/主 CTA/强调（唯一海洋色） */
  --wh-pass:          #34C88A; /* 绿：PASS / verified 语义 */
  --wh-danger:        #E5484D; /* 红：红线 / 退回（仅在展示时） */
}</pre>

| Token | 色值 | 用途 | 理由 |
| --- | --- | --- | --- |
| <code>--wh-bg</code> | <code>#0A1A2F</code> | 页面底色 | 深海定位 + 开发者深色语境 |
| <code>--wh-surface</code> | <code>#122841</code> | 卡片底 | 比底色亮一档，形成层次 |
| <code>--wh-border</code> | <code>#1F3A5C</code> | 卡片边框 | 弱分隔，不抢内容 |
| <code>--wh-text</code> | <code>#E8EFF7</code> | 主文字 | 深底近白，对比度约 15:1 |
| <code>--wh-text-2</code> | <code>#9DB2C8</code> | 标签/正文 | 对比度约 7:1，够 AA |
| <code>--wh-text-3</code> | <code>#6B8198</code> | 脚注 | 大字/辅助场景 ≥4.5:1 |
| <code>--wh-accent</code> | <code>#4FD1C5</code> | 链接/CTA/触发语 | 深底对比约 7:1；全页唯一海洋色 |
| <code>--wh-pass</code> | <code>#34C88A</code> | PASS 语义 | 绿色=通过，全球通用心智 |
| <code>--wh-danger</code> | <code>#E5484D</code> | 红线语义 | 红色=警示（克制使用） |

### 2.3 排版（字体与字号层级）

**字体栈**

<pre>--wh-font: -apple-system, BlinkMacSystemFont, "Segoe UI",
           "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
           "Noto Sans SC", sans-serif;
--wh-mono: ui-monospace, SFMono-Regular, "JetBrains Mono", Menlo, Consolas, monospace;</pre>

> 理由：静态站不引入 webfont，零加载、首屏快；PingFang/YaHei 保证中文清晰；等宽用于一切命令与哈希。

**字号层级（桌面）**

| 元素 | 字号/字重/行高 | 说明 |
| --- | --- | --- |
| Hero 主标题 | clamp(30px, 5.5vw, 48px) · 700 · 1.1 | 首屏第一句话 |
| Hero 副标题 | clamp(16px, 2vw, 20px) · 400 · 1.5 · <code>--wh-text-2</code> | 支撑句 |
| 横幅数字 | clamp(36px, 7vw, 64px) · 700 · 1 · tabular-nums | 实时数字不抖动 |
| 横幅标签 | 14px · 500 · <code>--wh-text-2</code> · letter-spacing .02em | 标签不抢数字 |
| 卡片标题 | 18px · 650 · 1.3 | 动作卡标题 |
| 卡片正文 | 15px · 400 · 1.65 · <code>--wh-text-2</code> | 最多 2 行 |
| 触发语 | 15px · 500 · <code>--wh-accent</code> · 等宽 | 「给你的 agent」引用块 |
| CTA 文字 | 15px · 600 | 链接/按钮 |
| 脚注 | 13px · <code>--wh-text-3</code> | 数字关系说明 |

> 关键一条：横幅数字必须 <code>font-variant-numeric: tabular-nums</code>，否则数字每 15 分钟刷新时宽度变化会左右抖。

### 2.4 布局与间距（8px 网格）

| 项 | 值 |
| --- | --- |
| 间距基准 | 8px |
| 页面左右留白 | 桌面 24–32px · 移动 16px |
| Hero 上下内边距 | 桌面 96px · 移动 64px |
| 区块间距 | 桌面 72px · 移动 56px |
| 横幅三格 | 横排，gap 16px（桌面 24px），每格 padding 24px，圆角 12px |
| 卡片区 | grid 三列，gap 20px，卡片 padding 28px，圆角 12px，边框 1px <code>--wh-border</code> |
| 断点 | sm &lt;640px · md 640–1024px · lg ≥1024px |

- 卡片布局：lg 三列横排；md 两列；sm 单列堆叠。
- 横幅布局：md/lg 三格横排；sm 改为纵向三行（数字+标签竖排），避免 320px 三格挤压。

### 2.5 组件规范（字段即结构）

**A. Hero**
- 顺序：主标题 → 副标题 →（可选）站点标签行「为 DeepSeek Harness (DSH) · For DeepSeek Harness (DSH)」。
- 对齐：左对齐（文案短，左对齐最利落）。
- 副标题颜色 <code>--wh-text-2</code>，主标题颜色 <code>--wh-text</code>。

**B. 数字横幅（三格）**
- 每格字段：大数字（等宽）→ 标签 → 一行说明。
- 三格语义色（可选点缀）：审过=灰蓝 <code>--wh-text-2</code>，通过=绿 <code>--wh-pass</code>，上架=鲸青 <code>--wh-accent</code>。主方案：数字统一 <code>--wh-text</code>，语义色只用于标签前 8px 小圆点，避免三色花掉。
- 横幅下方一条脚注（1.2 的「通过 ≠ 上架」）。

**C. 三动作卡片（首页导航卡）**
- 字段：图标（可选 20px）→ 标题 → 正文一句话 → CTA（链接，鲸青，带 → 箭头）。
- 「给你的 agent」卡片额外多一个字段：触发语引用块（等宽 + 鲸青 + 左侧 2px 鲸青竖线），可整块复制。
- 卡片整体可点（整卡链接），hover 换 <code>--wh-surface-hover</code>。

**D. 插件条目卡片（名录页 / 首页精选，补充）**
- 字段：名称 + 版本徽章 → tool 名（等宽）→ 一句话描述 → 作者（精选条目标 by xxx）→ source（repo + commit，等宽，可点击）→ sha256（等宽，截断 + 复制按钮）→ 安装命令（等宽块 + 复制按钮）。
- 理由：source / commit / sha256 / 命令四项全摆出来，就是「verified + 透明」的可见证据链。

### 2.6 移动端要点

1. **单列堆叠**：卡片三列 → 单列；横幅三格 → 纵向三行。
2. **字号缩到下限**：Hero 主标题 clamp 下限 30px，横幅数字下限 36px，在 375px 屏可读。
3. **触摸目标 ≥ 44×44px**：CTA、复制按钮必须达标。
4. **长命令不截断**：命令块以「复制按钮」为主，命令允许横向滚动；sha256 截断显示、点按复制。
5. **首屏约束**：375×667 内 hero + 数字横幅首屏可见（10 秒原则）。
6. **圆角与阴影**：圆角保持 12px，阴影减弱或取消（移动端省资源、降噪）。

### 2.7 落地检查清单（航 · 交付前逐项勾）

- [ ] 页面源码零写死数字，<code>{audited}/{pass}/{listed}</code> 由数据层渲染
- [ ] 文案无禁用词（赋能/抓手/闭环/颠覆/卷/yyds + 最好/第一/最全）
- [ ] 中英文案对称，同一信息双语齐全，无遗漏
- [ ] 对比度：正文 ≥4.5:1，大字 ≥3:1
- [ ] 横幅数字用 tabular-nums，实时刷新不抖
- [ ] 触发语与安装命令均可一键复制
- [ ] 每处 CTA 带真实链接或真实安装命令
- [ ] sm(&lt;640px) 下堆叠与 44px 触摸目标实测通过
- [ ] 脚注「通过 ≠ 上架」可见

---

## 3. 验收对照（本文件自查）

1. **10 秒可读**：Hero 主标题一句话「每个插件都验证过的商店」，三卡片即三个下一步；数字口径=审过/PASS/上架，无吹牛词。✔
2. **中英对称**：Hero、横幅、三卡片、触发语均为中英成对。✔
3. **视觉规范可执行**：色值/字号/间距/卡片字段全给定，附 CSS 变量与理由说明。✔
4. **输出位置**：本文件 /Users/eno/workspace/dshstore/marketing/homepage-design.md。✔
