# WhaleHarness 轮次日志（持久记忆）

> 作用：跨轮次的唯一事实来源。每轮结束更新。**禁用 butler_remember 等需批准的持久化工具**（会卡住自动流程），记忆只写这个文件 + README.md。

## 纪律（用户要求）
- 不让用户插手：不使用需要批准的写入工具；一切状态落 workspace 文件。
- 每轮结束：更新本文件 + todo，然后结束轮次让 goal 自动继续。

## Round 1 — 开站（完成）
- 站点上线 http://whaleharness.store（python http.server + systemd，后已被 nginx 替代）
- 2 插件（whale-praise、whale-fortune）+ 2 skills（whale-brand、whale-marketing）真实验证：boot + headless 端到端工具调用 + skill catalog
- 招募 PM/文案/渠道 3 个 AGENT；收到 ROADMAP.md、copy-x/long、invite、plan
- 关键坑（详见 README）：dsh plugin add 必须 -w；cordis 具名导出 {apply,inject,name}；参数 schema 不能 required:false

## Round 2 — HTTPS + 契约（完成）
- nginx + Let's Encrypt：https://whaleharness.store，http 301；/healthz 上线
- 全站 URL https + install 命令带 ?src=install；线上重装端到端验证通过
- P1 契约：plugins.json 加 sha256 + dsh_compat；新增 plugins.schema.json
- 首页加 OG meta、分享文案按钮、oracle 抽签、sha256 展示；robots.txt + sitemap.xml
- 踩坑：scp 上传文件权限 600 → nginx 403，上传后必须 chmod -R a+rX /srv/whaleharness
- 渠道 AGENT 派发 day2/3 任务（copy-b.md 渠道素材、copy-dm.md 短帖、plan.md 标记完成）

## Round 3 — 投稿机制 + 直播间 + 物料沉淀（完成）
- Store 策略（用户授权自主决定）：策展审核制。投稿箱 = nginx 公开 PUT 端点 /submit/<token>/<name>-<version>.tgz（5MB、只收 tgz/tar.gz、公开可读、审核透明）；审核清单 docs/REVIEW.md；提交页 /submit.html
- 直播间（用户提示「直播写插件」）：/live.html 异步文字直播，第 0 集=开站实录（真实过程），第 1 集预告=下个插件全程直播开发
- /press.html：5 份推广物料沉淀页（python 脚本 deploy/gen_press.py 从 marketing/*.md 生成）
- 渠道 AGENT 交付 copy-b.md（X/HN/Reddit 素材）、copy-dm.md（群聊/README 短帖），plan.md 已更新
- 修正遗留：plugins.json baseUrl/fallbackUrl → store（渠道 AGENT 指出）
- 坑：nginx location 正则含 {8,32} 必须加引号（{ 被当块边界）；heredoc 不加引号会被 bash 展开 $

## Round 4 — whale-submit 插件（DSH 内投稿）+ 第 1 集直播（完成）
- 新插件 whale-submit v0.1.0 上线：whale_submit 工具，会话内打包本地插件目录 PUT 到公开投稿箱
- 实现要点：手写极简 tar（ustar，纯 Buffer，遵守自家 child_process 红线）；名称/版本校验；5MB 上限；fetch PUT
- 端到端验证：headless 会话真实调用，把 whale-praise 源码投进线上投稿箱（5 文件 7680 字节），站方回读结构正确
- 第 1 集直播实录发布 /live.html；submit.html 增加「在 DSH 里投稿」章节
- 投稿箱清理 cron 已装（/etc/cron.d/whaleharness：每周清非 tarball + 30 天过期）
- GitHub PR 通道：无 GitHub 账号，记入 ROADMAP.md 待办（诚实处理，不假装有）

## Round 5 — whale-status 插件 + 第 2 集直播 + 度量修正（完成）
- 新插件 whale-status v0.1.0 上线：whale_status 工具，站点体检（HTTPS/DNS/TLS 剩余天数/全部 tarball sha256 完整性）
- 全 Node 内置模块（fetch/dns/tls/crypto），零依赖；schema 坑：type 数组 ["string","null"] 不被 DSL 支持
- 端到端一次通过：HTTP 200、证书 89 天、3 插件 sha256 全 ✓；上架后 4 插件
- 第 2 集直播实录发布；选题理由：PM 候选 websearch/todo/shell 均与 DSH 内置重复，选「吃自己狗粮」的体检工具
- plan.md 度量段改 nginx access.log（实测：UV 40、下载 8、PUT 3、src=install 2）
- 投稿箱测试文件已清理
- 派发 AGENT 第二轮任务：文案 round2.md（5ed87de3）、渠道 review1.md + 二周计划（e82599a6）

## Round 6 — whale-brand-check 插件 + 第 3 集直播（完成）
- 新插件 whale-brand-check v0.1.0 上线：whale_brand_check 工具，按 whale-brand 语调给文案体检
- 确定性检查：禁用词/感叹号密度/海洋比喻/链接缺失/首段铺垫；100 分制，80 可发 60 小改 <60 回炉
- 端到端：坏文案 0 分回炉（禁用词全抓），真物料 90 分可发（不误杀）
- 第 3 集直播实录发布；选题理由：狗粮叙事第三集——用它审 AGENT 写的推广文案
- 文案 AGENT 交付 round2.md（直播间/whale-submit/whale-status/导览 6 条短帖），press 页重新生成（6 sections）
- 渠道 AGENT review1.md 仍在产出（e82599a6）
- 站上 5 插件 + 2 skills

## Round 7 — 真实渠道推广启动（完成）
- 批评收到：此前只有物料没有投放。本轮转向真实渠道。
- LobsterMail 已关停（410，2026-08-17 停服）→ 换 mail.tm 收件箱 whaleharness@emalupe.com（lobster/mailbox.json + check-mail.mjs 轮询脚本），供用户申请 GitHub 用
- HN：注册账号 whaleharness 成功（lobster/hn.cookies），发帖被新号限流（showlim/toonew）——每日尝试一次，解除即发 Show HN；帖子标题已备好
- Reddit：captcha 挡路，curl 自动化不可行
- Bing IndexNow：4 个 URL 已提交（202），key 文件上线
- 邮箱监控：等 GitHub 验证邮件

## HN 发帖命令（限流解除后执行）
FNID=$(curl -s -b hn.cookies -c hn.cookies -A "$UA" https://news.ycombinator.com/submit | grep -oE 'name="fnid" value="[^"]+"' | head -1 | sed 's/.*value="//;s/"//')
curl -s -b hn.cookies -c hn.cookies -A "$UA" -X POST https://news.ycombinator.com/r --data-urlencode "fnid=$FNID" --data-urlencode 'fnop=submit-page' --data-urlencode 'title=WhaleHarness: a plugin store for DeepSeek Harness' --data-urlencode 'url=https://whaleharness.store'

## Round 8 — i18n（完成）
- 用户提醒：向英语社区推广但站点全中文，转化断点。
- plugins.json 全部条目加 description_en（5 插件 + 2 skills）
- index.html 重写为中英双语：I18N dict（zh/en 各 16 key 对齐已校验）、navigator.language 默认 + localStorage 记忆 + 右上角切换按钮、箴言双语各 6 条、OG meta 改英文
- submit/live/press 加英文 tagline
- 部署验证：4 页 200，dict 无缺 key
- 日常：邮箱空（GitHub 验证码未到）；HN 仍 toonew（继续每日一投）

## Round 9 — 物料口径统一 + sitemap 更新（进行中）
- 渠道 AGENT 指出文案物料仍 2 插件口径 → 派文案 AGENT（142256ea）按 5 插件最新口径重写全部 6 份物料
- sitemap.xml 重新生成（12 URL：4 页面 + 2 数据 + 5 插件 tarball + 2 skills tarball）上线，IndexNow 重新推送 202
- 例行：邮箱空；HN 仍 toonew；com DNS 仍旧 IP

## Round 10 — 英文技术长文（完成）
- /blog.html 上线：双语（EN/ZH 切换）技术文《Shipping a DSH Plugin: Format, Pitfalls, Verification》
- 内容 = 一手经验：bundle 三件套、三个真实炸 boot 的坑（-w / named exports / required:false）、四步验证环、发布流程
- 定位：SEO 长尾资产 + HN/dev.to 投放素材
- 首页导航加 Blog；sitemap 加 blog.html；IndexNow 已推 202
- 文案 AGENT 物料重写仍在进行（copy-*.md 尚未更新）

## Round 11 — 插件装进用户真实 DSH（完成）
- 经用户批准（escalate），4 个插件（whale-praise/fortune/submit/status）装进用户真实 web profile，bundles 已 reconcile，下次 boot 生效——用户日常会话将真实使用本站产品
- 文案 AGENT 完成全部 6 份物料重写（5 插件口径 + HTTPS + ?src=install），press 页重新生成上线
- nginx 日志确认：尚无搜索引擎爬虫到访（IndexNow 已推，等 Bing）

## Round 12 — 公开数据仪表盘（完成）
- /stats.html + /stats.json 上线：每 15 分钟 cron（/etc/cron.d/whaleharness-stats）从 nginx 日志真实聚合 UV/安装/投稿/爬虫/下载分布
- 品牌含义：不编数的透明运营（whale-marketing 度量纪律的产品化）
- 发现第一个外部访客（腾讯云 IP 拉 plugins.json）
- dev.to 注册被 captcha 挡（记录，不再撞墙）
- HN 仍 toonew

## 当前待办（Round 13+）
- [ ] 收集渠道 AGENT review1.md + 二周计划，落 day8-14 执行
- [ ] whaleharness.com DNS 生效后：certbot --expand 加 com 域名；全站 URL 切换 com
- [ ] 第 4 集直播选题：第一份真实投稿 / com 迁移 / 周报生成器
- [ ] GitHub 账号到位后建 PR 投稿通道（见 ROADMAP.md）
- [ ] 持续展开推广活动（AGENT 团队持续作业）

## 团队花名册
- PM: e93239d9（ROADMAP.md）
- 文案: 142256ea（copy-x/long、invite）
- 渠道: 3e3efb74（plan.md，day2/3 任务进行中）
- 已停用重复组: b45b5702、ee687a17、07f3862b
