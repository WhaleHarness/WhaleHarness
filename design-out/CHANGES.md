# CHANGES — 设计感落地：首页 + 货架页

> 产出：`design-out/index.html` · `design-out/store.html`（以线上版本为底，功能零丢失，只重做视觉层）。
> 执行规范：`marketing/homepage-design.md`，并超出它——「设计感」= 排版层次 + 留白 + 卡片层级 + 克制动效，不是堆色块。

---

## 一、旧版问题清单（为什么「没设计感」）

1. **单一平面色**：所有卡片同一 `#122841`，页面像表格，没有「背景 → 卡片 → 凹陷区」的三层纵深。
2. **没有排版节奏**：标题 / 正文 / 标签字号差很小，缺 eyebrow/kicker 这一档「超小字宽字距」的层级，首屏没有视觉锚点。
3. **底色是死色**：`#0A1A2F` 纯平铺，「深海」只停留在字面，没有光晕 / 渐深的纵深。
4. **货架卡信息堆叠**：`name / version / tool / category / new / verified` 六个字段全塞进一行 h3，机器字段（source / commit / sha256 / tarball）永远全展开——信息密度高、主次全无，扫读 79+ 卡很累。
5. **分类 chip 选中态弱**：选中只是描边变色，不「一眼看见」。
6. **套装区无区分度**：复用普通卡片，而 `bundles.json` 里现成的 `one_liner`（一键组合命令）被完全闲置。
7. **动效缺位 + 无 focus 态**：hover 只有换底色；键盘 Tab 无可见焦点；CTA 无引导箭头。
8. **header/footer 朴素**：无 sticky、无毛玻璃，语言切换是两个独立描边按钮。

## 二、视觉改了什么（首页 index.html）

| 模块 | 改动 | 为什么 |
| --- | --- | --- |
| 背景 | `body::before` 三层：左上鲸青光晕 + 右上冷蓝光晕 + 自上而下渐深 | 给「深海」真实纵深，克制到只一丁点亮 |
| 头部 | sticky + `backdrop-filter: blur(14px)`；语言切换改为分段控件 | 长页滚动导航不离手；中英切换更聚合 |
| Hero | 新增 eyebrow kicker（小字 + 0.16em 字距 + 短横线）；h1 字距 -0.015em、上限提到 56px | 建立「超小字标签 → 大字标题 → 副标」三层节奏 |
| 数字横幅 | trustline 升级为 stat strip：大数字 `tabular-nums` + 语义色圆点标签 + 右侧脚注 | 数字是首屏重心，一眼抓到且刷新不抖 |
| 场景套装特色区 | Hero 数字横幅与三动作卡之间新增「特色带」：套装小卡（名称 / tagline / 成员数 / 一键装按钮），每卡标「策展初版」；卡片用鲸青描边与导航卡区分层级 | 把 bundles.json 的 `one_liner` 变成首页一键可复制的主动作；特色区是「展示」，导航卡是「下一步」，不堆砌 |
| 三动作卡 | SVG 描边图标、顶部 1px 高光、hover 抬升 -3px + 阴影、CTA 箭头 hover 右滑 | 卡片有「层次」和「可点」反馈；图标是设计师在场的直接信号 |
| 红线徽章 | 圆角胶囊 + 圆点对齐微调 | 保持红色语义，视觉更利落 |
| 页脚 | 双列网格 + 大写小标题 | 与全站 chrome 一致且更规整 |

## 三、视觉改了什么（货架页 store.html）

卡片信息层级**重排**（这是本次最大改动）：

```
旧：一行 h3 塞 6 字段 → 描述 → 作者/溯源/sha256 永远展开 → 命令 → tarball
新：
  ① 名称（大字）+ 徽章（verified 绿 / new 鲸青）      ← 是什么
  ② 工具名 · 分类 · 版本（等宽 tag）                    ← 给 agent 的标识
  ③ 一句话描述                                          ← 干什么
  ④ 安装命令（终端 $ 前缀）+ 一键复制                    ← 怎么装
  ⑤ 溯源（<details> 收起：作者 / source / sha256 / tarball）← 证据链，按需展开
```

- **机器字段收起**：summary 行显示「溯源 + repo@commit 摘要」，点开才见完整 source/sha256/tarball——79+ 卡从「信息墙」变成可扫读的卡片。
- **分类 chip 选中态**：选中 = 实心鲸青填充（深字），非选中描边；每个 chip 带等宽计数徽章。
- **搜索框**：内置放大镜图标 + 聚焦 `box-shadow` 光环。
- **套装区**：独立视觉带（鲸青渐变底 + 描边）；每套一个「一键复制整套」主按钮（消费 `one_liner`），下方 `<details>` 逐个查看单插件命令。
- **安装命令**：终端 `$` 提示符前缀，命令本身 `nowrap` 横向滚动不截断。
- **动效克制**：hover 抬升 + 边框提亮 + 阴影，复制按钮按压微缩，`+ → ×` 的展开指示；全站尊重 `prefers-reduced-motion`。

## 四、规范落地对照（并超出）

- ✅ 深蓝底 + 鲸青唯一海洋色；语义色（绿=verified/PASS、红=红线）只用于徽章/圆点，不铺大色块。
- ✅ `tabular-nums` 用于全部数字（横幅 + 计数）。
- ✅ 8px 网格间距、卡片圆角 12px、命令等宽字体。
- ✅ 对比度：正文 `#9DB2C8` ≥ 7:1，脚注大字场景 ≥ 4.5:1。
- ✅ 触摸目标 ≥ 44px（复制按钮 / chip / 语言切换）。
- **超出规范的增量**：纵深背景、sticky 毛玻璃头部、卡片 SVG 图标与高光、分类实心选中态、机器字段 <details> 收起、套装 one_liner 一键复制、focus-visible 焦点环、reduced-motion 降级。

## 五、功能零丢失确认

- **JS 逻辑 / 数据源 / i18n 全部保留**：`loadNumbers()`（现算 audit.json/plugins.json 长度，无手写数字）、`renderCats / renderStore / renderBundles`、搜索、分类筛选、`AUTHORS_MAP / NEW_NAMES`、语言切换。
- **隐藏指令块 `agent-brief` 字节级与线上一致**（已 diff 校验）。
- **`wh-chrome:lang` 注入块保留**（语言切换按钮事件与 nav/footer i18n 扩展来自它）。
- **两处顺带修正**（非功能删减）：① 货架 `applyLang()` 补调 `renderBundles()`，修语言切换后套装标题不更新的旧 bug；② 显式声明 `BUNDLES` 变量（原为隐式全局）。
- **两处纯视觉 i18n 调整**：首页 CTA 文案去掉内嵌「 →」（箭头改为可动画的 SVG）；新增 eyebrow / 套装区 / 复制整套的 i18n 键。
- **首页新增场景套装区**：`loadBundles()` 现算 bundles.json 渲染套装小卡（名称/tagline/成员数/一键装复制 `one_liner`），成员数由 JS 渲染、零手写；`applyLang()` 补调 `renderBundles()` 保证中英切换。

## 六、验收自查

- [x] 脚本 `node --check` 通过；`agent-brief` JSON 可解析且与线上逐字一致
- [x] 全部必需 DOM id（`n-audited/n-listed/copy-brief/bundle-strip/bundles-sec/q/cats/bundles/count/plugins/lang-*`）齐全
- [x] 全部 `data-i18n` / `data-i18n-ph` 键在 I18N（含 Object.assign 扩展）中有定义
- [x] 标签配平、样式块唯一
- [x] 数字零手写（横幅、计数全部现算）
- [x] 只写 `design-out/` 与 `marketing/homepage-design.md`，未动 `dist/` 与线上

## 七、品牌语言修订（本轮追加，莫总定调）

- 「审核制」在汉语有上对下/审批的负面位差，且是判定者时代旧词——全站对外文案统一改为「验证」口径（英文 `curated` 已准确，不动）。
- Hero 主标题：`审核制插件商店。` → **`每个插件都验证过的商店。`**（副标题「目录收录一切，商店只上架验证过的」本就是验证口径，保留）。
- 货架 eyebrow：`审核制商店 · 沙箱验证` → `验证过的商店`（英文 `curated store · sandbox-verified` 保留）。
- 排查并替换线上全部 5 个含「审核制」页面：index / store / open-letter（`审核制商店`→`验证过的商店`）/ press（×2）/ build-log（`策展审核制`→`策展验证制`）。
- `marketing/homepage-design.md` 文案规范同步修订 4 处（Hero 主标题、用途、为什么这样写、验收对照）。
- 工程术语「审计管道 / audit / 透明审核」保留不改；改的只是对外品牌叙事。
## 八、首页五点修正（莫总移动端目测）

1. **stat strip 移动端平排**：去掉 flex-direction: column，两个数字横排，脚注换行占整行。
2. **「审过」灰点换蓝**：新增 --wh-blue: #5E9FE8（审计蓝），与「上架」鲸青 #4FD1C5 相邻色系，蓝→青呼应审计→上架的漏斗递进，弃用灰 --wh-text-3。
3. **套装区移动端左右滑动**：<640px 时 bundle-strip 改 display:flex + overflow-x:auto + scroll-snap-type:x mandatory，卡片 flex:0 0 78% 露出下一张边作滑动暗示；桌面保留 3 列 grid。追加 scrollbar-width:none + ::-webkit-scrollbar 隐藏滚动条（露边暗示已足够）。
4. **safety 区重设计**：加标题「四条红线」+ 一句人话说明「每个上架插件都过这四关 + 沙箱验证」；四个红线徽章一组；zero-trust/deep-dive 两链接合并为一行「完整安全叙事 →」（指向 zero-trust.html），不再混进徽章。
5. **三动作卡不动**。node --check 通过，功能零丢失（r5/r6 键随 HTML 移除，新增 safety-h/safety-s/safety-more 双语键）。
## 九、footer 重设计 + build-chrome.py 同步建议

### 改了什么
- **for agents 组保留**（6 机器文件）：plugins.json / agent.json / llms.txt / categories.json / audit.json / authors.json，横排不变。
- **for humans 组改三小组**（替代 20+ 平铺）：
  - 逛：货架 store / 审计名录 audit / 投稿 submit / 数据 stats
  - 读：Blog / Deep Dive / Zero Trust / 构建日志 build-log
  - 参与：投稿箱 submissions / 吐槽 feedback / 公开信 open-letter
- **低频页不进 footer（留 sitemap）**：live / press / backendless / audit-fixes / feed（feed.xml 仍存在，RSS 经 head 的 alternate link 被发现，只是不进 footer）。
- **GitHub 移到 footer 底部**（tagline 下一行「GitHub ↗」），是三小组之外的独立外部链接，不混进分组。
- **移动端三小组堆叠**：fg-cols 由 repeat(3,auto) 改 1fr，逛/读/参与 竖排。

### build-chrome.py 同步建议（航执行，单源生成全站 footer）
1. footer 骨架（替换原「给人看的」平铺块）：
   fg（for humans）内嵌 fg-cols，三个 fg-col 各带一个 fg-col-h 小组名 + links 竖排；底部 tagline + 独立 gh 链接。
2. 新增 i18n 键（zh / en 成对）：
   fg-browse 逛/Browse、fg-read 读/Read、fg-join 参与/Contribute；
   f-store 货架/Store、f-audit 审计名录/Audit、f-submit 投稿/Submit、f-stats 数据/Stats、
   f-buildlog 构建日志/Build Log、f-submissions 投稿箱/Submissions、f-feedback 吐槽/Feedback、f-openletter 公开信/Open Letter。
3. 新增 CSS 类：fg-cols / fg-col / fg-col-h / gh（见 design-out/index.html 的 footer 样式区）。
4. 命名一致性提醒：footer 用「审计名录」，nav 仍是「审计」——建议全站统一为一个名（是否 nav 也改「审计名录」由莫总定）。
5. 移动端断点（<640px）：fgrid 1fr 之外，再加 fg-cols 1fr + gap 20px。
## 十、footer 三小组移动端并排（理解更正）

1. **理解更正**：上一轮误把「给人看的太长」当成三动作卡；实为 footer 的 for humans 三小组（逛/读/参与）在移动端上下堆叠过长。
2. **三动作卡已回退**：恢复桌面三列 / 移动端竖排（1fr）；顺带的 hero/stats/safety 收紧一并回退到原值（hero 56/24、stats 32/12、safety 28/48）。
3. **footer 三小组移动端三列并排**：fg-cols 移动端由 1fr（上下堆叠）改 repeat(3,1fr)，逛/读/参与左右并排、每列小组名+链接竖排；桌面 repeat(3,auto) 不变。
4. node --check 通过，功能零丢失。
## 十一、og-image 重做（图文不一致修正）

1. **旧问题**：og-image.png 副标题还是「a pod of plugins in the deep sea」旧叙事，与 og:description「A curated plugin store…」不一致（分享卡=旧口径）。
2. **新文案**（保留深蓝底 + 鲸鱼）：主标题 WhaleHarness + 副标题「A curated plugin store for DeepSeek Harness」（分两行）+ 一行绿色「every plugin verified」+ whaleharness.com；暗色底保证对比。
3. **生成方式（可复现）**：design-out/gen_og.py（Python PIL，1200×630，深蓝渐变 + 左上鲸青光晕 + Apple Color Emoji 鲸鱼 + Helvetica 文字），运行 python3 gen_og.py 即可重出。
4. **部署**：替换站点根 og-image.png；og:description 已是新口径无需改（与 og-image 文案已对齐）。
## 十二、footer 外链区加 dev.to（Agent 友好社区露出）

1. **改动**：footer 底部 tagline 下一行，GitHub 旁并列 dev.to（https://dev.to/whaleharness），两外链用 ext-links 容器并排。
2. **为什么**：能用 API 的就是 Agent 友好——dev.to 是开发者社区露出，与 GitHub 并列外链区。moby@whaleharness.com 已是 dev.to 账号。
3. **build-chrome.py 同步建议（航执行）**：footer 底部的单 gh 链接替换为 ext-links 容器 + 两个 gh 链接（GitHub / dev.to，文字后带 ↗ 表示外链）；CSS 新增 .ext-links（flex + wrap + gap 6px 20px），.gh 去掉 inline-block + margin-top（改由 .ext-links 承载）。
4. node --check 通过，功能零丢失。

## 十三、Hero 副标语拗口修正(琢语感定案)

1. **旧**：「目录收录一切，商店只上架验证过的。」——「上架验证过的」读来宾语悬空、像被截断（琢诊断）。
2. **新**：「目录收录一切，商店只上验证过的。」——去「架」后动词收得利落，与「收录」对仗；保留「验证过的」口径。
3. **范围**：中文共 5 处（hero 副标语 DOM + zh i18n；footer tagline DOM + zh i18n；wh-chrome:lang 注入），英文不动（句法无此问题）。
4. **验证**：部署 + CF 清缓存后线上抓取，新句 5 处、旧句 0 处。
## 十四、全站文案去翻译腔（琢重写案）

1. **病根（用户点出）**：不是措辞拗口，是结构直译——「为 DeepSeek Harness（DSH）／每个插件都验证过的商店。／给 DeepSeek Harness（DSH）的插件站——目录收录一切，商店只上验证过的。」三句换个词就是英语句（for DSH / every plugin is verified in this store / a plugin store for dsh — all in record, on shelf verified only）。「能吃 ≠ 好吃」，中英文都算。
2. **新文案（琢定稿，莫比校准一处）**：
   - 中文 eyebrow「DeepSeek Harness 插件站」；h1「目录里什么都有，商店里只放验证过的。」；sub「想淘就翻目录，想稳就进商店。」；footer「装之前，都有人替你验过。」（琢稿「看过」→莫比改「验过」贴口径）
   - 英文 h1「Everything in the directory. Only verified ones in the store.」；sub「See everything in the directory. Install verified ones from the store.」；footer「Nothing reaches you until it's verified.」
3. **范围**：index.html hero 中英三行 + footer 中英 + meta 共 13 处；build-chrome.py 单源 3 处 → 16 页 footer 全站重生成。
4. **验证**：node --check 抓出 chrome 注入单引号串内 it's 撇号截断（不修则线上 JS 全崩）——转义修复；VPS python3.14 重跑 16 页；线上旧句 0 / 新句 16 页；CF 清缓存。顺手清掉站点根 12 个 ._*.html（AppleDouble scp 残渣）。
## 十五、正文页去翻译腔（琢二批：4 页 8 处）

1. **submit.html**：光天化日之下（贬义联想）→ 摆在明面上；只允许 insert（夹生）→ 只能往里写；低权沙箱+boot（缩略直译）→ 低权限沙箱+真装、真启动、验证工具注册。
2. **submissions.html**：把 tarball PUT 进来 → 把 tarball 传进来（HTTP 方法不当日常动词）。
3. **open-letter.html**：市场（抽象称呼）→ 平台方；你们做入口，我们做认证层，不竞争 → 入口你们来做，认证我们来管，不抢地盘；自动化管道每 6 小时扩量 → 自动化流程每 6 小时还在一批批扩。
4. **zero-trust.html**：公开 PUT 到 → 用 PUT 公开上传到；boot + 端到端 → 启动、端到端。
5. **莫比校准一处**：琢稿「真装、真启动、真调用，验证工具能注册」给原文加了「调用」动作，改回「真装、真启动、验证工具注册」（原句三动作：装 / boot / 注册）。
6. **验证**：部署 + CF 清缓存；线上病句 0、新句全在。
