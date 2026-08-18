# 鲸群代码质量基线（Code Quality Baseline）

> 作者：礁（鲸群代码质量官）　|　性质：只读评审，不修码　|　日期：2026-08-18
> 同级文件：runbooks/reviewer-consistency.md
> 证据来源：本机工作区 + VPS 只读探查（ssh -F /tmp/moby-ssh.cfg wh）+ 线上 whaleharness.com 抓页。行号与 md5 均实测可复现。

## 0. 结论摘要（先结论后理由）

今日新增 4 件高风险代码的评审结论：

| 资产 | 结论 | 一句话理由 |
|---|---|---|
| fetch_candidates.py 修复版（VPS） | 有条件通过 | 全失败写空文件已堵（L54-56），但部分失败仍静默缩小候选池（L27-29/57），同族缺陷未根除 |
| deploy/publish_curated.sh | 缺陷（高，fail-open） | 审查 REJECT 门是死代码：grep verdict: REJECT 永远不匹配审查器输出（L61-62） |
| whale-store/lib/index.js | 通过 | 只读两源、无代跑安装、无危险 API；node --check 通过 |
| 线上 index/store/audit 页内联 JS | 通过（安全） | 三页语法通过、动态数据全 esc() 无 XSS；附健壮性/漂移备注 |

最重的一条（今日必须修）：publish_plugin.sh 与 publish_curated.sh 的「审查 REJECT 即停」闸门失效——审查器判定词早已从 REJECT 改成 RED-LINE/FORMAT-ISSUE，但发布管道的 grep 还盯着旧词。后果是红线插件会被直接发布，审查器这个安全基座在发布路径上形同虚设。证据见 §3.2。

一条必须补的机制：fetch_candidates.py 的修复只在 VPS 落了地，本机 deploy/fetch_candidates.py 仍是 54 行旧版（md5 b044d9cc）。修复没回同步到源码仓，下次「本机→VPS」同步会把修复冲掉。见 §4.4。

---

## 1. 核心代码资产清单

「维护者」按 pod-members.md 与 ROUNDS.md 实测归属；「测试覆盖」如实标注——多数资产无自动化测试，这正是这次 fetch_candidates 事故拖两天才暴露的根因。

| # | 资产 | 维护者 | 位置/形态 | 最近改动 | 已知缺陷 | 测试覆盖 |
|---|---|---|---|---|---|---|
| 1 | review-submission.py（审查器=安全基座，质量要求最高） | 礁 | tools/review-submission.py（370 行；VPS md5 6d1d9710… 与本机一致） | 规则较全：动态外传/subprocess 门/required:false/豁免清单/藏 dist 盲区 | 无已知缺陷；但下游发布管道没接它的 verdict（见 #6/#7） | 有：tests/reviewer-regression/run_regression.py（244 行，6 类样例） |
| 2 | fetch_candidates.py（候选池拉取） | 航/莫比（宿主） | deploy/fetch_candidates.py；VPS /opt/whaleharness-audit/deploy/（58 行） | VPS 今日加「全失败不写」守卫 L54-56 | 部分失败仍静默缩小候选池（§4）；本机仍是 54 行旧版未同步 | 无（事故即因缺「失败不破坏数据」回归） |
| 3 | scan_candidates.py（手工候选扫描） | 屿/航 | deploy/scan_candidates.py（33 行） | 无近期 | CANDIDATES 硬编码 6 仓库，会过时 | 无 |
| 4 | audit_batch.py（批量审计） | 礁/航 | deploy/audit_batch.py（210 行） | verdict 解析已迁到新词 | 无重大；CLONE-FAIL/ERROR 仅打印不重试 | 无 |
| 5 | gen_audit_json.py / gen_badges.py / gen_audit_feed.py / gen_authors.py（审计产物生成器） | 礁/航 | deploy/*.py | 随 verdict 词迁移同步 | 按 audit-data.md §2 清单覆盖，无已知 | 无 |
| 6 | publish_plugin.sh（自家插件发布唯一入口） | 航（屿固化） | deploy/publish_plugin.sh（68 行） | 近期 | REJECT 门死代码（L19-20）；验证失败不 exit 1（L68） | 无 dry-run |
| 7 | publish_curated.sh（外部精选上架唯一入口） | 屿 | deploy/publish_curated.sh（134 行） | 今日新增 | REJECT 门死代码（L61-62）；manifest 非原子写（L103）；远程部署无 set -e（L120）；验证失败不 exit 1（L134） | 有 --dry-run |
| 8 | whale-store/（第 16 鲸插件） | 屿 | whale-store/{lib/index.js,package.json,cordis.patch.yml,README.md} | 今日上架 0.1.0 | 无致命（只读两源）；无缓存、按 repo 首条取判定（当前 audit.json 每 repo 恰一条，无碍） | 无（屿最小版，未配回归） |
| 9 | whaleharness-ops.sh（航运营循环） | 航 | VPS /usr/local/bin/（4959 B） | 今日加 flock 单实例锁 | 无重大（锁设计合理，trap 清理 pid/when） | 无 |
| 10 | whaleharness-watch.sh（巡自动初审） | 航/巡 | VPS /usr/local/bin/（3799 B） | 今日加 RESUBMISSION 标记 | prev_review 按 name 全局匹配，跨箱误配风险（低） | 有合成验收（env 覆盖路径） |
| 11 | whaleharness-observe.sh（望哨兵） | 航/望 | VPS /usr/local/bin/（2167 B） | 无近期 | nocache URL 含 0x0F 控制字符（L7/L10），缓存破除失效 | 无 |
| 12 | whaleharness-retro.sh（省回顾） | 航/省 | VPS /usr/local/bin/（2607 B） | 无近期 | §4.5 策略红队指令重复两行（L19-20） | 无 |
| 13 | 线上页面内联 JS（index/store/audit） | 航 | whaleharness.com（live 为准；本机 dist/index.html 已陈旧，diff 484 行） | round16 整页重做 + store/audit 独立页 | store/audit 无 fetch 错误处理；store 硬编码 NEW_NAMES/AUTHORS_MAP 漂移（§3.4） | 无 |
| 14 | consistency_check.py（一致性/误报/红队自查） | 礁 | tools/consistency_check.py | 无近期 | 无已知 | 有（--mode consistency/falsepositive） |

---

## 2. 质量门标准草案（可执行，非口号）

### 2.1 交叉评审表：谁写谁不评自己

三条铁律：提交人不评自己；审查器自己最不能自评；评审结论必须给行号证据。

| 提交人 | 评审人 | 覆盖 |
|---|---|---|
| 航（VPS 脚本 / 页面 JS / 管道脚本 / 口径） | 礁 | 脚本安全 + 数据完整性（失败不破坏数据） |
| 屿（插件 / 管道固化 / 外部集成） | 礁 | 安全基座 + 门有效性 + 溯源正确性 |
| 礁（审查器 / 一致性工具） | 屿 + 航 | 屿跑 tests/reviewer-regression 全绿；航抽查线上 audit.json 分布与重扫 |

补充：巡/望/省 的 VPS 脚本由航代写，仍归入「航 写 → 礁 评」。礁改审查器后，不得由礁自评「通过」——必须屿跑回归集 + 航验线上，双人签字才算过。

### 2.2 每类资产必查项

| 资产类型 | 必查项（按序） |
|---|---|
| Python（审查器/管道） | ① ast.parse/py_compile ② 审查器改动必须先跑 tests/reviewer-regression/run_regression.py 全绿 ③ 副作用安全：写文件必须原子（临时文件 + os.replace），失败不得覆盖旧数据 ④ 异常不得吞掉后继续写（重点查 except: break/continue 之后是否仍有写盘） |
| Bash（发布/部署/ops） | ① bash -n ② set -euo pipefail 是否到位（远程 ssh 命令串要自带 set -e，不能靠本地继承） ③ REJECT/失败闸门是否真的会触发（grep 词与审查器实际输出词逐字核对） ④ 最终验证失败必须 exit 1，不得只 echo ⑤ 写 store 资产必须原子（temp+rename） |
| JS 插件（whale-store 等） | ① node --check ② 跑自家审查器 review-submission.py 自审（只允许 already in the store 一条警告） ③ 无 eval/subprocess/外传/凭据读取 ④ 只读声明与实现一致（README 说只读，代码就必须无写） |
| 页面内联 JS | ① 抽取 script 块 node --check ② 所有动态数据（plugins/authors/audit entries）必须过 esc()，禁止裸插 innerHTML ③ fetch 必须有错误面（try/catch 或 .catch） ④ 硬编码事实（NEW_NAMES/AUTHORS_MAP 之类）必须标来源+日期，且要有与数据源（authors.json/categories.json）的对照校验 |
| VPS 脚本（ops/watch/observe/retro） | ① bash -n ② prompt 内不得有重复指令/控制字符（cat -A 查 ^O 之类） ③ 关键 URL 参数不得夹带不可见字符 ④ 锁/信号处理有 trap 清理 |

### 2.3 评审记录格式（统一模板）

每次评审产出，落一个文件或一条台账，字段如下：

    评审记录
    - 评审人 / 提交人 / 日期
    - 资产与版本（文件路径 + md5 / commit）
    - 结论：通过 / 有条件通过 / 缺陷（分档：高=安全或数据破坏 / 中=健壮性 / 低=样式）
    - 证据：行号 + 现场（每一条结论必须有，不允许「感觉不对」）
    - 建议：只给修复方向，不代改（修是产出者的事）
    - 回执：提交人 48h 内回「已修/不修+理由」；不修的高危项升级莫比裁决

---

## 3. 今日新增高风险代码评审（逐件行号）

### 3.1 fetch_candidates.py 修复版（VPS，58 行）→ 有条件通过

修复确认（有效）：VPS L54-56 新增守卫——

    54  if not seen:
    55      print('FETCH FAILED: zero repos fetched; keeping existing candidates file', file=sys.stderr)
    56      sys.exit(1)
    57  open(OUT, 'w').write(...)

报告里的「422 全失败仍写空文件」这一症状已堵：seen 为空即 exit 1，不再覆盖 OUT。语法 ast.parse 通过。

剩余同族缺陷（未根除，见 §4）：L27-29 except: break 单 topic/单页失败即静默中断该 topic，不重试、不区分 429 限流；L57 仍是非原子写 + 无「本次拉取数比旧文件少就拒绝覆盖」保护——部分失败仍会静默缩小候选池。

### 3.2 deploy/publish_curated.sh（134 行）→ 缺陷（高，fail-open）

致命：REJECT 闸门是死代码。

    61  python3 tools/review-submission.py "$TGZ" --manifest dist/plugins.json | tee /tmp/publish_curated_review.txt || true
    62  if grep -q "verdict: REJECT" /tmp/publish_curated_review.txt && ! grep -q "already in the store" ...; then
    63    echo "审查 REJECT,发布中止"; exit 1
    64  fi

- 审查器（tools/review-submission.py L346-350）只输出四种 verdict：RED-LINE / FORMAT-ISSUE / PROCEED TO MANUAL STEPS / EXCLUDED；全文件唯一一处 REJECT 出现在 L277 注释里（REJECTED by the DSL），不是输出词。
- 因此 L62 的 grep 永远不匹配，if 恒假，闸门永不触发；L61 的 || true 又吞掉了审查器 exit 1。红线/格式缺陷插件会被照常打包、写 manifest、部署。
- 根因：verdict 词从 REJECT 改为 RED-LINE/FORMAT-ISSUE 时（runbooks/audit-data.md §2 的下游全清单），发布管道两条脚本漏在清单外。audit_batch.py（L175-187）迁了新词，publish_plugin.sh / publish_curated.sh 没迁。

附加缺陷：
- L103 json.dump(d, open(p,'w'), ...) 非原子写 dist/plugins.json，中断会留下半截 JSON。
- L120 远程 ssh 命令串未自带 set -e（本地 set -e 不穿透 ssh），tar 解包失败仍会继续 reload nginx；2>/dev/null 又把错误藏掉。
- L134 最终验证 [ ... ] && echo 发布完成 || echo 验证失败：验证失败只打印不 exit 1，调用方拿不到失败退出码。
- L125 CF purge 无响应校验（失效只影响缓存，不影响资产）。

同类连带：publish_plugin.sh L19-20 是同一死门，L68 同样验证失败不 exit 1。两条发布管道都要修。

### 3.3 whale-store/lib/index.js（260 行）→ 通过

- node --check 通过；package.json 合法（type:module / dsh.runtime:host / bundle.patch 正确）；cordis.patch.yml 只插入本插件 name，与 package.json name 一致。
- 安全边界与 README 一致：只读两个源（plugins.json L19、audit.json L24），无 child_process/eval/凭据读取/动态外传；install 工具只打印命令不代跑（L168 描述属实）。
- 防御性写法到位：fetchJson 非 2xx 抛错（L12-14）而非静默；loadCatalog/loadAuditIndex 对结构做 Array.isArray 兜底（L20/L25）；找不到插件显式报错（L224-226）。
- 备注（非阻塞）：① 无缓存，每次调用实拉线上（L98/L151/L222）；② loadAuditIndex 按 repo 取首条（L29 !index.has(repo)），当前 audit.json 每 repo 恰一条（421 条、0 重复，实测），无碍；若将来一 repo 多版本会取到旧判定。

### 3.4 线上 index.html / store.html / audit.html 内联 JS → 通过（安全）

- 三页内联 script 抽取后 node --check 全部通过（index 4052 B / store 5988 B / audit 8323 B）。
- 安全达标：三页所有动态数据（插件名/描述/作者/溯源/audit issues）均过 esc()（index L276、store L151、audit L195）后才进 innerHTML，无 XSS；无 eval/外传/凭据读取。
- 健壮性备注：
  - store.html L218-225：Promise.all(fetch plugins, fetch categories) 无 try/catch 无 .catch，任一源失败→整页空白。
  - audit.html L275：fetch(/audit.json) 无 .catch（页面核心数据失败无兜底）；对比 L276 authors.json 有 .catch。
  - store.html L150 NEW_NAMES 硬编码「新上架」名单（dsh-x/wx-archive、dsh-whale-fortune，标 08-16/08-17），漏掉 08-18 的第 16 鲸 whale-store——已漂移。L167-171 AUTHORS_MAP 硬编码作者映射，而站上已有 authors.json 可作唯一源。
  - index.html L276 esc() 定义未用（死代码，低）。

---

## 4. 特别审查：fetch_candidates.py「失败静默破坏数据」同类

任务点名的缺陷：GitHub 风控 422 时仍写空文件，两天后 421 条审计停滞才暴露。修复版（VPS）只堵了「全失败」这一种。逐条排查「异常吞掉 + 副作用未回滚」：

| # | 位置（VPS 行号） | 现象 | 是否同类「静默破坏数据」 |
|---|---|---|---|
| 1 | L27-29 | except: break 单页失败静默中断该 topic，继续下一 topic | 是（吞错继续，最终仍写盘） |
| 2 | L31-33 | if not items: break 把「返回空」当「该 topic 结束」，不区分限流/错误响应 | 是（空响应静默当正常结束） |
| 3 | L54-56 | 修复：seen 空则 exit 1 不写 | 已堵（全失败场景） |
| 4 | L57 | open(OUT,'w').write 非原子；无「新数据条数 < 旧文件条数则拒绝覆盖」 | 是（部分失败仍会缩小候选池）——这是没堵住的同类 |
| 5 | L10 | token 文件缺失/空 → 未捕获 FileNotFoundError（空 token 走 401 → L27 → L54 兜底） | 半同类（缺文件 loud 失败可接受；空 token 靠 L54 兜底） |

结论：修复堵住了「全失败写空文件」，但没堵住「部分失败写缩小文件」。三个 topic 里只要有一个成功、其余被限流（搜索 API 认证 30/min，分 topic 分页容易撞），seen 非空，L57 照写，上一版更大候选池就被更小的部分结果覆盖——这正是同一族「失败静默破坏数据」。本次事故的机制层根因（拉取结果变差也要无条件覆盖）尚未消除。

建议（只给方向，不代改）：① 写临时文件 + os.replace 原子落盘；② 记录本次拉取数，若比旧文件条数显著缩水（如 <旧×0.9）则拒绝覆盖并 loud 报错；③ L27-29 区分 429（退避重试）/422（参数错，修参数）/5xx（重试），不要一律 break。

### 4.4 附带发现：修复未回同步到源码仓

本机 deploy/fetch_candidates.py 仍是 54 行旧版（md5 b044d9cc，L54 无守卫直接写），VPS 是 58 行修复版。按 runbooks/scripts.md 的同步纪律，修复应落本机 + github-repo 再上 VPS；现在反着做了，下次「本机→VPS」同步会把修复冲掉。这是流程缺陷，不是代码缺陷，但同样记入基线。

---

## 5. 交付报告（复数协作语态）

- 资产清单：14 件核心资产全覆盖，维护者/最近改动/已知缺陷/测试覆盖均落到文件与 md5 证据（§1）。
- 今日新增 4 件评审结论：1 有条件通过 + 1 缺陷（高）+ 2 通过，逐件带行号（§3）。
- 特别审查：fetch_candidates.py 全失败已堵、部分失败同族未堵，5 项排查表（§4）。
- 我们这轮最该先动的两件事：① 修两条发布管道的死 REJECT 门（安全基座 fail-open，最高优先）；② 把 fetch_candidates.py 修复回同步到本机 + github-repo，并补「原子写 + 缩水拒绝覆盖」。
- 未做（边界内主动不做）：本文件之外零改动；VPS 全程只读；修码留给产出者（航/屿/莫比）。

---

## 6. 复评闭环（2026-08-18）

屿修复两条发布管道的死 REJECT 门后，礁复评：**通过**。

| 验收点 | 结论 | 证据 |
|---|---|---|
| ① 停门=审查器退出码非零即中止，两管道一致 | 通过 | publish_plugin.sh L29-33 与 publish_curated.sh L61-65 同构（if ! python3 review-submission.py ... > file 2>&1; then exit 1; fi） |
| ② 无残留旧 grep verdict:REJECT | 通过 | grep 两脚本零匹配；旧 tee + || true + grep 逻辑已移除 |
| ③ 无新缺陷（退出码语义正确） | 通过 | 审查器 L352 return 1 if(red_lines or format_issues) else 0；RED-LINE/FORMAT-ISSUE=1 中止、PROCEED/EXCLUDED=0 放行；发布管道不带 --repo，EXCLUDED 豁免实际不触发（fail-closed） |
| ④ 不破坏 already-in-store 更新场景 | 通过 | 实测：whale-store 同版本重跑 → already-in-store warning + PROCEED + exit 0 → 放行 |

三场景实测：更新场景放行（exit 0）✓；红线场景（副本注入 eval）中止（RED-LINE）✓；损坏包中止（fail-closed）✓。

遗留项（上轮已记，非本次引入，仍在）：验证失败不 exit 1（publish_plugin.sh L96 / publish_curated.sh L135）；manifest 非原子写（L67/L104）；远程 ssh 部署无 set -e + 2>/dev/null（L84/L121）；CF purge 无响应校验。建议随下轮「发布管道加固」一并处理。

顺带改进（无缺陷）：publish_plugin.sh 新增 --dry-run，与 publish_curated 对齐。

---

## 7. 发布管道待加固区（残余清单，标优先级）

以下四项是复评死 REJECT 门时列出的残余，非停门本身缺陷，记录于此待下轮「发布管道加固」统一处理；管道改动归产出者（航/屿），礁不碰。

| 优先级 | 残余项 | 位置 | 理由 | 修复方向 |
|---|---|---|---|---|
| 高 | 验证失败不 exit 1 | publish_plugin.sh L96 / publish_curated.sh L135 | 线上 sha/短链/溯源对不上时只 echo「验证失败」，退出码仍 0，CI/派单会误判发布成功 | 验证失败分支 exit 1 |
| 高 | manifest 非原子写 | publish_plugin.sh L67 / publish_curated.sh L104 | json.dump 直写 plugins.json，中断留半截 JSON，商店资产损坏 | 写临时文件 + os.replace/mv |
| 中 | 远程 ssh 部署无 set -e + 2>/dev/null 吞错 | publish_plugin.sh L84 / publish_curated.sh L121 | 本地 set -e 不穿透 ssh；tar 解包失败仍 reload nginx，部分部署静默 | 远程命令串加 set -e；2>/dev/null 改为落日志 |
| 低 | CF purge 无响应校验 | publish_plugin.sh L86 / publish_curated.sh L126 | purge 失败只影响缓存刷新，不影响资产完整性 | 检查响应 success 字段，失败告警 |


