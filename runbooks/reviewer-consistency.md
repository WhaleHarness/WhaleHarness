# Runbook: 审查器质量官 · 事件驱动 + 每周兜底自查（裁决一致性 / 误报率 / 策略红队）

审计赛道的核心价值是「裁决经得起重跑」——用数字证明,不靠自我声明。
三项自查是「事件驱动 + 每周兜底」,不是「等月底」:

- 每次规则变更 → 裁决一致性抽查立即跑（抽 5 干净重跑）
- 每批全量重扫后 → 误报抽查立即跑（抽 5 人工复核）
- 策略红队 → 每周一次（挑 5 判定演作者）
- 每周日（日历兜底）: 查三项有没有积压,没跑就补跑——防积压,不是主节奏

数字进交付报告。

工具: tools/consistency_check.py（复用 deploy/audit_batch.py 的 pack,干净临时目录重跑当前审查器）

## 1. 裁决一致性自查（触发: 每次规则变更后立即跑）

目的: 验证 audit.json 里记录的 verdict 能被「原 repo+version+commit + 当前审查器」重跑复现。

    python3 tools/consistency_check.py --mode consistency --sample 5 --seed <固定种子>

- 从 audit.json 可复现池(PASS/RED-LINE/FORMAT-ISSUE/EXCLUDED)随机抽 5 条
- 干净临时目录 git clone → checkout 记录的 commit → 打包 → 跑当前审查器 → 比对 verdict
- 产出: 一致率 = 一致数 / 5

不一致逐条归因(三选一,写进报告):
- 规则变化: 审查器规则改了,旧记录用旧规则 → 属预期,列入「改判名单」复审
- 数据漂移: 同 commit 内容变化(强制推送/打包差异/依赖变化) → 记录复现条件
- 环境依赖: clone/checkout 失败、GitHub 限流、临时网络 → 标记复现失败,不算不一致

离线自检(验证工具链/开发用,复用本地 curated/audit/<owner>__<repo>;本地 clone 可能非记录 commit,
故仅用于自检,正式一致率数字必须用默认 fresh clone):
    python3 tools/consistency_check.py --mode consistency --sample 5 --use-local-clones

## 2. 误报率量化（触发: 每批全量重扫后立即跑）

目的: 把「误报率」从口头变成数字——RED-LINE 名单抽 5 个做人工复核。

    python3 tools/consistency_check.py --mode falsepositive --sample 5 --seed <固定种子>

- 打印 5 个 RED-LINE 条目: repo@version+commit + 判定理由(issues)+ 源码位置
- 人工读源码核对每条判定理由是否成立,填 [属实/误报]
- 当批误报率 = 误报数 / 5

发现误报: 走 runbooks/reviewer-dev.md 事故响应(停发→修→回归→灰度→重扫→主动更正),
并给莫比修复建议。

## 3. 策略红队自查（触发: 每周一次）

目的: 对抗性自审——扮演愤怒作者,从当前 RED-LINE/FORMAT-ISSUE 名单挑 5 条判定,
专找「我是作者,这条判定我服不了」的理由,检验每条红线的策略动机是否站得住、措辞是否伤人。

    python3 tools/consistency_check.py --mode falsepositive --sample 5 --seed <固定种子>
    (FORMAT-ISSUE 条从 deploy/audit.json 手动挑 5 条)

每条「红队报告」格式:
- 判定: repo@version(commit) + verdict + 判定理由
- 作者反驳(三选,专找不服的理由): ①误伤合法场景 ②理由不成立 ③措辞侮辱性
- 误伤面推演: 这条规则还可能误伤哪些合法写法(对照 runbooks/reviewer-dev.md §5 策略动机表的「误伤面」列)
- 我的裁决: 策略成立 / 需修(需修 → 修复建议 + 走 runbooks/reviewer-dev.md 事故响应)

产出: 一页「红队报告」进交付报告。

## 4. 交付报告字段（三项数字必填）

- 裁决一致性: __ / 5 (__%); 不一致清单: (逐条 + 归因)
- 误报率: 误报 __ / 5 (__%); 误报条目: (repo + 误报理由 + 修复建议)
- 策略红队: 5 条判定中「需修」__ 条; 红队报告: (一页,附作者反驳 + 裁决)
- 回归样例通过率: __ / 6 (python3 tests/reviewer-regression/run_regression.py)
