# 审查器开发参考（reviewer-dev.md）

> 与 reviewer-consistency.md 配套：红队 §3 与误报响应引用本文件。v1 重建于 2026-09-06（原引用悬空 404 满月——08-30 省红队指出，09-06 重建）。内容依据=仓库 tools/review-submission.py（权威版 20KB）+audit 四类判定+红队 R1-R5 联想，不编造未实现的策略。

## §1 审核裁决四类（与 audit.json verdict 一致）
- RED-LINE：安全红线——subprocess 未声明 dsh.runtime:host / 敏感路径直读（~/.dsh 凭据等）/ 网络出口未声明 / 许可不兼容 / 安装脚本改宿主。
- FORMAT-ISSUE：形态标准——缺 cordis.patch.yml / dsh.bundle.patch 非 ./cordis.patch.yml / 版本异常 / 打包缺 package/ 前缀 / patch 引用未声明 foreign 包。
- PASS：结构合法+零红线=机器通道候选。
- UNEVALUATED：扫描面外（NO-ROOT-PKG 等）。

## §2 事故响应（误报发生时）
停发 → 修 → 回归 → 灰度 → 重扫 → 主动更正（与 reviewer-consistency.md §4 一致）。

## §5 策略动机表（误伤面对照，红队用）
| 判定 | 策略动机 | 误伤面（对照） | 红队校验 |
|---|---|---|---|
| RED-LINE subprocess | 防「装的不是插件是后门」；声明即解 | 功能型插件的合理 host 子进程（声明 dsh.runtime:host 即转人工审） | R3 成立 |
| RED-LINE 敏感路径 | 凭据必须走官方 ctx credentials 服务，直读=蜜罐失效 | 无（结构性不收，作者改路径即回池） | R5 成立 |
| RED-LINE 网络出口 | 未声明外发=行为不可预期；措辞宜「undeclared network egress of subprocess output」而非定罪化 exfiltration | 需确认 manifest 是否有「网络出口声明字段」让作者可合规——无则补字段（R4 待确认） | R4 前提 |
| FORMAT bad version | 空版本/1.0.15=真格式问题 | **rc/beta 预发布=生态惯例，不应按格式失败**，宜独立类或注明「上架需 release 版」 | **R1 需修** |
| FORMAT 无 dsh 意图 | 公共审计页语义清晰 | **无 cordis/无 dsh 意图仓应标 NOT-A-DSH-PLUGIN/UNEVALUATED，不进 FORMAT 语义**（否则替我们树敌） | **R2 需修** |
| FORMAT 打包缺 package/ | 商店包规范 | 作者可修（一次打包修正） | 成立 |
| PASS | 结构合法+零红线 | 静态 PASS≠真 bundle（结构空证 round94 案例；机器通道以权威审查+构建+四查兜底） | round94-103 已内建 |

## §6 维护记录
- 09-06：v1 重建（此前文件缺失，引用 404）；待办=消息模板统一附「一行修法」+公共审计页区分「投稿裁决」与「目录普查标注」（省 09-06 红队建议）。
