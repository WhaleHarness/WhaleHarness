# Ecosystem audit, week 5: from PASS to store listing (the machine channel)

> Snapshot frames: `2026-09-01T00:41:46Z` (`/audit.json` and `/authors.json`). The audit runs every 6 hours and the live count is authoritative — numbers below are from these frames; the live files may already be newer. Onboarding status frame: `2026-09-01T06:2xZ`. Written by the WhaleHarness crew, same rules as the store: verifiable numbers only.

## The headline

The 6-hourly pipeline is now at **2,764 audited DSH plugin repos**:

| Verdict | Count |
|---|---|
| PASS | 1,189 |
| FORMAT-ISSUE | 814 |
| RED-LINE | 307 |
| UNEVALUATED | 453 |
| EXCLUDED | 1 |
| **Version-pinned & evaluated** | **2,310** |

**51.5%** of evaluated repos pass, from **2,063 authors**. The store itself is at **180 verified plugins** — every one boot-verified in an isolated sandbox and sha256-pinned.

## Week 5: the machine channel moves

Since the week-4 snapshot (2,757 repos), the pipeline found **7 new repos**. Two of them are clean PASS with zero issues — the next candidates for the machine channel (the store's lane for ingesting good third-party repos directly, as opposed to waiting for a manual submission):

| Candidate | Version | Pinned commit | Audit | Static review |
|---|---|---|---|---|
| [hanzhangzzz/dsh-diagram](https://github.com/hanzhangzzz/dsh-diagram) | 0.3.4 | `4128f2b4c3d6` | PASS, 0 issues | PROCEED (build_tgz.sh + review-submission.py) |
| [HaoyueQin/dsh-better-reasoning-effort](https://github.com/HaoyueQin/dsh-better-reasoning-effort) | 0.3.3 | `bf3e7d88e99e` | PASS, 0 issues | PROCEED (build_tgz.sh + review-submission.py) |

- **dsh-diagram** — turn the article your DSH session already understands into an editable Excalidraw canvas (agent drafts, you refine, autosave, export `.excalidraw`/SVG/PNG). MIT.
- **dsh-better-reasoning-effort** — reasoning-effort and input-modality settings for third-party models, edited right inside the official Models page card, plus a quick effort slider in the model menu. MIT.

Both were **built reproducibly** from their pinned commits (`deploy/build_tgz.sh`, epoch-pinned mtimes, sorted tar, `gzip -n`) and passed the same static reviewer the store uses (`tools/review-submission.py`, exit-0 = proceed). Their sha256 is pinned, ready for listing.

**Honest status (frame `2026-09-01T06:2xZ`):** the two candidates are staged and awaiting the store's isolation-verification gate (REVIEW.md §3 — the VPS Docker sandbox: network-none, read-only root, honeypot credential present, boot must pass and `dump-config` must show the plugin line). That step runs on the store's verification host, not in the public build; nothing is listed until it passes. The store's rule is unchanged: **no boot verification, no listing.**

## The machine channel, transparently

The store has two supply lanes and both end in the same five-step sandboxed review with pinned sha256 (see [docs/REVIEW.md](docs/REVIEW.md)):

1. **Author lane** — anyone PUTs a tarball to the public submission box; the review record is public.
2. **Machine lane** — repos that show up in the ecosystem audit with a clean PASS are ingested from their pinned public commit, built reproducibly, reviewed by the same tooling, then boot-verified in the sandbox.

The machine lane is why the store can carry 180 plugins without waiting for submissions: the ecosystem audit surfaces good repos, and the verification pipeline turns them into listings. The two candidates above are the machine lane's next step.

## The untapped pool: 1,009 PASS repos not listed yet

1,189 repos passed the audit — the store lists 180 plugins, so **roughly 1,000 PASS repos are not listed yet** (the exact overlap varies per frame). If yours is one of them, the hard part is already done: the audit proved the repo version-pinned, buildable and free of red lines.

Two ways in:

- **Self-serve (author lane):** check your repo's verdict at [audit.html](https://whaleharness.com/audit.html) or grep [audit-report.md](https://whaleharness.com/audit-report.md), then PUT a tarball:
  ```
  curl -T your-plugin-0.1.0.tgz https://whaleharness.com/submit/whalepod2026/
  ```
  Reviews are public; rejection notes tell you exactly what to fix. Full loop end to end: [kwawa-return.html](https://whaleharness.com/kwawa-return.html).
- **Machine lane:** keep your repo at a clean PASS (no red lines, format clean — the two fix tiers below are five-minute fixes), and the pipeline may pick it up on its own.

## Why plugins still fail (same frame, fresh numbers)

### Format issues (814 repos): packaging, five-minute fixes

- **618** — `dsh.bundle.patch` must be `./cordis.patch.yml`
- **595** — `cordis.patch.yml` missing
- **160** — patch loads a foreign package
- **124** — bad version string

### Red lines (307 repos): safety

- **247 (80%)** — subprocess usage without a `dsh.runtime:host` declaration
- **50 (16%)** — network exfiltration (sensitive/child_process data passed to a network sink)
- **42 (14%)** — sensitive path access
- **3 (1%)** — eval
- 35 repos trip more than one red-line category

Fix paths: [audit-fixes.html](https://whaleharness.com/audit-fixes.html) · [redline-audit.html](https://whaleharness.com/redline-audit.html) · [zero-trust.html](https://whaleharness.com/zero-trust.html) · line-level evidence in [audit.json](https://whaleharness.com/audit.json) · open letter on verification as a shared trust layer: [open-letter.html](https://whaleharness.com/open-letter.html)

---

# 生态审计第五周：从 PASS 到上架（机器通道）

> 快照帧：`2026-09-01T00:41:46Z`（`/audit.json` 与 `/authors.json`）。审计每 6 小时一轮，线上计数为准；本页数字为快照帧，live 文件可能已更新。上架状态帧：`2026-09-01T06:2xZ`。只写可验证数字。

**大盘**：6 小时一轮的审计管道已审 **2,764 个 DSH 插件仓库**：1,189 PASS · 814 格式问题 · 307 红线 · 453 未评估 · 1 排除（2,310 已钉版本评估，通过率 51.5%），作者榜 2,063 人；商店现有 **180 个验证插件**（沙箱 boot 验证 + sha256 钉死）。

**本周：机器通道动起来了**。相比第四周快照（2,757 仓库），管道新增 **7 个仓库**，其中 **2 个 PASS 且零 issues** —— 机器通道（不等投稿、直接从生态审计摄入好仓库的通道）的下一批候选：

- [hanzhangzzz/dsh-diagram](https://github.com/hanzhangzzz/dsh-diagram) 0.3.4（commit `4128f2b4c3d6`）—— 把会话里已理解的文章变成可继续编辑的 Excalidraw 画布（Agent 出初稿、你在 DSH 内精修、自动保存、导出 .excalidraw/SVG/PNG）。MIT。
- [HaoyueQin/dsh-better-reasoning-effort](https://github.com/HaoyueQin/dsh-better-reasoning-effort) 0.3.3（commit `bf3e7d88e99e`）—— 第三方模型推理档位与输入模态设置，直接在官方 Models 页卡片内编辑，另附模型菜单快速档位滑块。MIT。

两者均已从钉死 commit **可复现构建**（`deploy/build_tgz.sh`：epoch 统一 mtime + 排序 tar + `gzip -n`），并通过商店同一把静态审查尺子（`tools/review-submission.py`，exit 0 = 放行），sha256 已钉死待上架。

**诚实状态（帧 `2026-09-01T06:2xZ`）**：两个候选已打包待过商店的隔离验证门（REVIEW.md §3 —— VPS Docker 沙箱：禁网 + 只读根 + 蜜罐凭据在场，boot 通过且 `dump-config` 出现插件行）。该步骤在商店验证宿主上执行，不在公开构建里；未过门前不列任何条目。商店规则不变：**未 boot 验证不上架**。

**机器通道，透明可见**。商店两条供给线汇入同一个五步沙箱审核 + sha256 钉死（[docs/REVIEW.md](docs/REVIEW.md)）：①作者通道——任何人向公开投稿箱 PUT tarball，审核记录公开；②机器通道——生态审计里干净 PASS 的仓库，从钉死公开 commit 摄入、可复现构建、同一把尺子审查、沙箱 boot 验证。机器通道正是商店在没有投稿的情况下能到 180 插件的原因：审计把好仓库找出来，验证管道把仓库变成上架条目。

**未上架的长尾作者池**：1,189 个 PASS 仓库，商店现有 180 个插件 —— 粗略还有约 **1,000 个 PASS 仓库未上架**（精确重叠随帧变化）。如果你的仓库在其中，最难的一步（审计已证明：版本可钉、可构建、无红线）已经完成。两条路：①自助（作者通道）：[audit.html](https://whaleharness.com/audit.html) 或 [audit-report.md](https://whaleharness.com/audit-report.md) 自查判定后 PUT tarball 到投稿箱（`curl -T your-plugin-0.1.0.tgz https://whaleharness.com/submit/whalepod2026/`），审核全程公开、退回说明精确到修法；完整闭环案例 [kwawa-return.html](https://whaleharness.com/kwawa-return.html)。②机器通道：保持仓库干净 PASS（下面两类都是五分钟可修），管道可能自己把你接进来。

**被拒两大主因（同帧新数）**：

- 格式（814 仓库，五分钟可修）：618 处 `dsh.bundle.patch` 必须是 `./cordis.patch.yml` · 595 处 `cordis.patch.yml` 缺失 · 160 处补丁加载外部包 · 124 处版本号错误
- 红线（307 仓库，安全）：247（80%）subprocess 无 `dsh.runtime:host` 声明 · 50（16%）网络外传 · 42（14%）敏感路径访问 · 3（1%）eval · 35 个仓库踩多条红线

修法： [audit-fixes.html](https://whaleharness.com/audit-fixes.html) · [redline-audit.html](https://whaleharness.com/redline-audit.html) · [zero-trust.html](https://whaleharness.com/zero-trust.html) · 逐行证据在 [audit.json](https://whaleharness.com/audit.json) · 验证作为共享信任层的公开信 [open-letter.html](https://whaleharness.com/open-letter.html)
