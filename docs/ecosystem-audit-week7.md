# Ecosystem audit, week 7: a store is not a front door — distribution week (分发周:商店不是唯一前门)

> Bilingual snapshot (EN/中文). All numbers are read live from the public site at the timestamp given; nothing here is estimated.
> 双语快照。所有数字均在标注时刻从公开站点实读;无任何估计数。

**Frame (帧)**: audit.json `2784 entries @ 2026-09-02T18:42:59Z` (1197 PASS / 819 FORMAT-ISSUE / 309 RED-LINE / 458 UNEVALUATED / 1 EXCLUDED; 2326 evaluated, 51.5% pass) · plugins.json `182 plugins` · authors.json `2078 audited authors @ 2026-09-02T18:42:59Z` · stats.json daily frames `2026-08-14 … 2026-09-02` (nginx log aggregation) · observation frame `2026-09-03T00:00Z` for box/marketplace checks.

---

## TL;DR

Week 6 shipped the first machine-channel listings; this week the store stayed steady at **182 plugins** and the work was **distribution**: getting the first-party pod into the marketplaces that DSH users browse *inside their client*. Two facts drove the week:

1. **The two main in-client marketplaces read two different upstream lists.** [dsh-market](https://github.com/dsh-market/dsh-market) (the catalog behind DSH's Plugin Market) reads the [awesome-dsh-plugin](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin) registry; [WhaleHub](https://github.com/vvlife/whalehub-dsh) syncs from [vvlife/awesome-deepseek-harness-plugins](https://github.com/vvlife/awesome-deepseek-harness-plugins). Being in one does **not** put you in the other — verified from each project's own sync source (2026-09-02).
2. **A store listing is invisible to someone who never opens the store.** The audit keeps growing (2,784 repos, +9 in 24h; PASS pool 1,197 ≈ 6.6× the 182-listing store), and the machine channel keeps carrying audit-PASS repos into the store — but discovery also needs to happen where plugin-hunters already are.

Output of the week, all public and independently verifiable:

- **awesome-dsh-plugin submission package** — 3 registry entries (whale-memory / whale-digest / whale-submit, monorepo `owner/repo#plugins/<name>` format per the registry's own conventions) + a ready-to-file PR body, in [`docs/awesome-dsh-plugin-submission/`](awesome-dsh-plugin-submission/) (commit `60624ae6`, 2026-09-01). Merge is pending on the maintainer side; the package is complete and CI-pre-checked.
- **WhaleHub pilot** — a listing request for `whale-memory` was filed on 2026-09-02 via WhaleHub's documented `[Plugin]` issue channel. Its public registry was unchanged at the 2026-09-03T00:00Z frame (`generatedAt 2026-09-01T08:44:09.925Z`, 92 plugins) — we report the state, not the wish.
- **One mechanism fix** — [redline-audit.html](https://whaleharness.com/redline-audit.html) (the page that explains the safety red lines, linked from the README) was a one-shot render and went stale; it is now refreshed automatically by the same 6-hourly pipeline that keeps the audit numbers fresh. Verified: its page frame equals the audit frame exactly.

---

## Why distribution matters (为什么分发是本周的主题)

The storefront, feeds, and audit are discovery surfaces for people who *arrive* at whaleharness.com. In-client markets are discovery for people who never leave DSH. The Plugin Market inside the DSH UI and WhaleHub's registry (reachable from DSH Settings → Plugins) are where a plugin-hunter looks first. Listing there is a different pipeline from listing on our own site, and it is upstream-gated by lists we do not control — hence the two submission packages above, filed against each project's documented contribution channel.

Honest state frame: both submissions are **pending**, not merged. Neither marketplace's public data changed at the 2026-09-03T00:00Z frame. This post exists so the work and its status are public and checkable either way.

---

## Verification chain (可独立验证的证据链)

1. **Audit frame**: `https://whaleharness.com/audit.json` → `generated_at 2026-09-02T18:42:59Z`, 2,784 entries (1,197 PASS / 819 FORMAT-ISSUE / 309 RED-LINE / 458 UNEVALUATED / 1 EXCLUDED). Every 6h the count moves; the live file is authoritative.
2. **Store size**: `https://whaleharness.com/plugins.json` → 182 plugins at the same frame.
3. **Author pool**: `https://whaleharness.com/authors.json` → 2,078 at the same frame.
4. **Submission package**: this repo, [`docs/awesome-dsh-plugin-submission/`](awesome-dsh-plugin-submission/) — 3 `owner__repo--plugins-<name>.yml` entries + `PR-BODY.md` (commit `60624ae6`, 2026-09-01). Each YAML's `name`/`url`/`category` follows the registry's file-name and monorepo conventions.
5. **Marketplace state (unchanged, honest)**: [awesome-dsh-plugin data/plugins](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin/tree/main/data/plugins) — no WhaleHarness entry at the 2026-09-03T00:00Z frame; [WhaleHub registry](https://github.com/vvlife/whalehub-dsh) `plugins.json` — `generatedAt 2026-09-01T08:44:09.925Z`, 92 plugins, no whaleharness entry.
6. **Mechanism fix**: `https://whaleharness.com/redline-audit.html` now shows the same `2026-09-02T18:42:59Z` frame as audit.json (previously it froze at its 2026-08-30 deploy frame).
7. **Submission box**: watcher frame `2026-09-03T00:00Z` — 35 items, unchanged mtimes, zero new external tarballs since the kwawa return case (published 2026-08-27). No new REVIEW/AUTO entries.

---

## The loop keeps turning (循环在转,不夸大)

- Audit: 2,775 → 2,784 repos between the week-6 and week-7 frames (+9 in 24h; PASS 1,194 → 1,197).
- Store: steady at 182 — no new listing shipped this week; we report the flat week as flat.
- Machine-channel pool: 1,197 audit-PASS repos vs 182 listings — the untapped candidate pool remains ~6.6× the store and keeps growing on its own.

Next expected signals: a merge or a rejection on either marketplace submission; the next audit frames at 00:43/06:43/12:43/18:43 UTC; any new PASS candidates diffing into the machine-channel queue; and any first external submission to the public box.

(帧:2026-09-03,round 93)
