# Ecosystem audit, week 4: the store follows the signal

> Snapshot frames: `2026-08-31T12:41:36Z` (`/audit.json`), `2026-08-31T12:41:37Z` (`/authors.json`); rankings frame `2026-08-29T13:07:36Z` (`/rankings.json`, weighted consensus across 21 sources, 6h crawl). The audit runs every 6 hours and the live count is authoritative — numbers below are from these frames; the live files may already be newer. Written by the WhaleHarness crew, same rules as the store: verifiable numbers only.

## The headline

The 6-hourly pipeline is now at **2,757 audited DSH plugin repos**:

| Verdict | Count |
|---|---|
| PASS | 1,187 |
| FORMAT-ISSUE | 810 |
| RED-LINE | 307 |
| UNEVALUATED | 452 |
| EXCLUDED | 1 |
| **Version-pinned & evaluated** | **2,305** |

**51.5%** of evaluated repos pass, from **2,057 authors**. The store itself is at **180 verified plugins** — every one boot-verified in an isolated sandbox and sha256-pinned.

## The store follows the signal

Cross-referencing the ecosystem consensus rankings (weighted community recommendation, 21 sources) against the store, the result is clean: **every plugin the ecosystem actually recommends is already listed**. 20 of 20 consensus-top plugins are in the store, all with PASS verdicts:

| Plugin | Repo | rec_score | sources | Store | Audit |
|---|---|---|---|---|---|
| dsh-genui | [omdsh-dev/dsh-genui](https://github.com/omdsh-dev/dsh-genui) | 9.6 | 11 | listed | PASS |
| dsh-agent-teams | [nanmicoder/dsh-agent-teams](https://github.com/nanmicoder/dsh-agent-teams) | 5.8 | 7 | listed | PASS |
| dsh-context | [bowenliang123/dsh-context](https://github.com/bowenliang123/dsh-context) | 5.8 | 7 | listed | PASS |
| dsh-annotation | [omdsh-dev/dsh-annotation](https://github.com/omdsh-dev/dsh-annotation) | 4.8 | 6 | listed | PASS |
| dsh-navbar | [vlln/dsh-navbar](https://github.com/vlln/dsh-navbar) | 4.0 | 5 | listed | PASS |
| dsh-reverse-skill | [dhicoc/dsh-reverse-skill](https://github.com/dhicoc/dsh-reverse-skill) | 4.0 | 5 | listed | PASS |
| dsh-memento | [perrylink/dsh-memento](https://github.com/perrylink/dsh-memento) | 3.2 | 4 | listed | PASS |
| dsh-context-doctor | [zhenyu98/dsh-context-doctor](https://github.com/zhenyu98/dsh-context-doctor) | 3.2 | 4 | listed | PASS |
| dsh-spotlight | [0xsline/dsh-spotlight](https://github.com/0xsline/dsh-spotlight) | 3.2 | 4 | listed | PASS |
| dsh-client-auto-continue | [hsiangnianian/dsh-auto-continue](https://github.com/hsiangnianian/dsh-auto-continue) | 3.2 | 4 | listed | PASS |
| dsh-telemetry-redactor | [030611/dsh-telemetry-redactor](https://github.com/030611/dsh-telemetry-redactor) | 3.2 | 4 | listed | PASS |
| dsh-image-gen | [shanliuling/dsh-image-gen](https://github.com/shanliuling/dsh-image-gen) | 3.2 | 4 | listed | PASS |
| … (8 more, all listed) | | | | | |

The 20 most-downloaded plugins in the ecosystem crawl are listed too. Both lanes — the machine lane (repos ingested from public sources, then run through the same verification loop) and the author lane (submissions) — end in the same five-step sandboxed review with pinned sha256.

## The untapped pool: 1,029 PASS repos not listed yet

1,187 repos passed the audit — **1,029 of them are not in the store yet**. If yours is one of them, the hard part is already done: the audit proved the repo version-pinned, buildable and free of red lines. Listing adds the store's verified badge and sha256-pinned tarball, public per-plugin download stats, and a transparent review record.

Self-serve: check your repo's verdict at [audit.html](https://whaleharness.com/audit.html) or grep [audit-report.md](https://whaleharness.com/audit-report.md). Already have a verdict? The fix paths are public — see below.

## Why plugins still fail (same frame, fresh numbers)

### Format issues (810 repos): packaging, five-minute fixes

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

Fix paths: [audit-fixes.html](https://whaleharness.com/audit-fixes.html) · [redline-audit.html](https://whaleharness.com/redline-audit.html) · [zero-trust.html](https://whaleharness.com/zero-trust.html) · line-level evidence in [audit.json](https://whaleharness.com/audit.json)

## Get listed

```
curl -T your-plugin-0.1.0.tgz https://whaleharness.com/submit/whalepod2026/
```

Reviews are public; rejection notes tell you exactly what to fix. The full loop end to end: [kwawa-return.html](https://whaleharness.com/kwawa-return.html) — a returning author, two plugins listed the same day.

---

# 生态审计第四周：商店跟随生态信号

> 快照帧：`2026-08-31T12:41:36Z`（`/audit.json`）、`2026-08-31T12:41:37Z`（`/authors.json`）；共识榜帧 `2026-08-29T13:07:36Z`（`/rankings.json`，21 个来源加权共识，6h 一轮）。审计每 6 小时一轮，线上计数为准；本页数字为快照帧，live 文件可能已更新。只写可验证数字。

**大盘**：6 小时一轮的审计管道已审 **2,757 个 DSH 插件仓库**：1,187 PASS · 810 格式问题 · 307 红线 · 452 未评估 · 1 排除（2,305 已钉版本评估，通过率 51.5%），作者榜 2,057 人；商店现有 **180 个验证插件**（沙箱 boot 验证 + sha256 钉死）。

**商店跟随生态信号**：把生态共识榜（21 个来源加权推荐）与商店交叉比对——共识榜 20/20 全部已在商店且全为 PASS（上表），生态抓取中下载量最高的 20 个插件也全部已上架。两条进店通道（机器通道：从公开仓库摄入再走同一验证环；作者通道：投稿）都汇入同一个五步沙箱审核 + sha256 钉死。

**未上架的长尾作者池**：1,187 个 PASS 仓库里还有 **1,029 个未进商店**。如果你的仓库在其中，最难的一步（审计已证明：版本可钉、可构建、无红线）已经完成。上架带来：商店验证徽章 + sha256 钉死 tarball、公开的逐插件下载统计、透明的公开审核记录。自查：[audit.html](https://whaleharness.com/audit.html) 或 [audit-report.md](https://whaleharness.com/audit-report.md)。

**被拒两大主因（同帧新数）**：

- 格式（810 仓库，五分钟可修）：618 处 `dsh.bundle.patch` 必须是 `./cordis.patch.yml` · 595 处 `cordis.patch.yml` 缺失 · 160 处补丁加载外部包 · 124 处版本号错误
- 红线（307 仓库，安全）：247（80%）subprocess 无 `dsh.runtime:host` 声明 · 50（16%）网络外传 · 42（14%）敏感路径访问 · 3（1%）eval · 35 个仓库踩多条红线

修法： [audit-fixes.html](https://whaleharness.com/audit-fixes.html) · [redline-audit.html](https://whaleharness.com/redline-audit.html) · [zero-trust.html](https://whaleharness.com/zero-trust.html) · 逐行证据在 [audit.json](https://whaleharness.com/audit.json)

**上架**：

```
curl -T your-plugin-0.1.0.tgz https://whaleharness.com/submit/whalepod2026/
```

审核全程公开，退回说明会精确到修法。完整闭环案例：[kwawa-return.html](https://whaleharness.com/kwawa-return.html)——返场作者一天内双投双上架。
