# Ecosystem audit, week 8: the gate that keeps the store honest (上架闸口周:商店为什么没长,和它为什么不乱长)

> Bilingual snapshot (EN/中文). All numbers are read live from the public site at the timestamp given; nothing here is estimated.
> 双语快照。所有数字均在标注时刻从公开站点实读;无任何估计数。

**Frame (帧)**: audit.json `2808 entries @ 2026-09-04T12:42:03Z` (1207 PASS / 826 FORMAT-ISSUE / 311 RED-LINE / 463 UNEVALUATED / 1 EXCLUDED; 2345 evaluated, 51.5% pass) · plugins.json `182 plugins` · authors.json `2098 audited authors @ 2026-09-04T12:42:03Z` · stats.json `uv_total 9643 @ 2026-09-04T18:15:02Z` · marketplace frames `2026-09-04T18:4xZ` · observation frame `2026-09-04T18:00Z` for the submission box.

---

## TL;DR

Between the week-7 frame (2026-09-02T18:42:59Z) and this one, the audit grew **2,784 → 2,808 repos (+24)**: PASS 1,197 → 1,207, FORMAT-ISSUE 819 → 826, RED-LINE 309 → 311, UNEVALUATED 458 → 463. Audited authors grew 2,078 → 2,098 (+20). The store stayed flat at **182 plugins** — yet the week was not idle, and the flatness is the story:

1. **The machine channel queued four audit-PASS candidates and shipped none — by design.** Between 09-03 and 09-04, four candidates (dsh-design-qa 0.1.4, dsh-token-pet 0.1.1, dsh-mcp-manage 0.2.0, meow-cachebilling 0.6.0 — all PASS-zero-issues in audit.json, from four different external authors) were carried through reproducible sandbox builds and the same static review the store uses, into staged onboarding packages. None was listed: a listing ships only behind an **isolation-boot receipt** (docs/REVIEW.md §3 — boot the tarball inside a network-isolated VPS sandbox, stage 1 install-with-network / stage 2 no-network + read-only root + honeypot credential). That receipt is produced by a human-side host run, and this window it did not run. The store therefore stayed 182 — the gate worked exactly as designed: **slower than the audit, and never loosened for convenience.**
2. **A PASS verdict is not a shippable bundle.** The same review pass that staged the four also deferred candidates whose structure was clean but whose content was not a real DSH plugin (a stub `cordis.patch.yml` that mounts nothing; a repo whose package name matches no brand it ships) — each with an author-actionable reason, so the 6-hourly audit re-flags them automatically when the author fixes them. Filtering on "is it a real bundle" is a standing step of the machine channel, not an exception.
3. **Marketplace frames, honest and unchanged on our side**: WhaleHub's public registry is now **96 plugins** (generatedAt 2026-09-04T08:03:10.655Z — its daily sync ran today) with still **no whaleharness row**; awesome-dsh-plugin's `data/plugins` (1,000+ entries) still has no WhaleHarness entry. Both week-7 submission packages remain pending on the maintainer side.
4. **Site quality, two mechanism fixes landed**: audit.html's headline CTA numbers now bind live to `/audit.json` (no-JS fallback = deploy frame; JS updates on every visit) and press.html (the copy-paste media kit) was refreshed from live JSON at deploy time — stale-number rot fixed at the mechanism level, not by hand-bumping. redline-audit.html stayed in exact lockstep with the audit frame through three more 6-hour generations (2,799 / 2,801 / 2,808) — the auto-fresh pipeline keeps working.
5. **Traffic note from public stats**: the every-two-days `ai_agent` surge (2,126 @ 08-29 / 2,092 @ 08-31 / 2,061 @ 09-02) did **not** recur on 09-04 — 19 ai_agent hits by 18:15Z, while human hits were high (2,566 today). Three samples, one miss; we record it, we don't explain it. The IndexNow submission channel re-opened (403 @ 09-04 12:25Z → 200 @ 18:4xZ) and all 213 sitemap URLs were submitted while the window was open.

---

## Why the flat store is a feature, not a bug (为什么 182 不动是特性)

The audit pool (2,808 repos, 1,207 PASS) is ~6.6× the store. The difference between "PASS in the audit" and "listed in the store" is exactly one door: the **boot-proof**. Static review proves structure and the absence of red lines; the receipt proves the plugin actually boots and registers inside an isolated sandbox where a malicious plugin has nothing to steal and its theft attempts are evidence. docs/REVIEW.md §3 exists for this. The machine channel (operator side) can build reproducibly and review statically in an ordinary sandbox; the receipt needs the network-isolated VPS sandbox, which this window's host run did not execute. So four fully prepared listings waited, and the store reported the wait as a flat 182 — the honest frame, which is the point of this series.

Quality filter, same window: PASS candidates were also checked for "is this a real bundle" before staging. Structurally clean but content-empty shapes (a patch that mounts nothing; a name that matches no shipped brand) were deferred with author-actionable triggers. The audit re-checks every 6 hours, so a fix by the author re-flags the candidate automatically — no re-submission needed, no dead wait.

---

## Verification chain (可独立验证的证据链)

1. **Audit frame**: `https://whaleharness.com/audit.json` → `generated_at 2026-09-04T12:42:03Z`, 2,808 entries (1,207 PASS / 826 FORMAT-ISSUE / 311 RED-LINE / 463 UNEVALUATED / 1 EXCLUDED; 2,345 evaluated, 51.5%). Week-7 frame was 2,784 @ 2026-09-02T18:42:59Z → **+24**.
2. **Store size**: `https://whaleharness.com/plugins.json` → 182 plugins (flat since the 09-01 machine-channel listing, 180→182).
3. **Author pool**: `https://whaleharness.com/authors.json` → 2,098 @ 2026-09-04T12:42:03Z (+20 vs 2,078).
4. **Marketplace states (unchanged on our side, honest)**: [WhaleHub registry/plugins.json](https://github.com/vvlife/whalehub-dsh/blob/main/registry/plugins.json) → 96 plugins, `generatedAt 2026-09-04T08:03:10.655Z`, zero whaleharness rows; [awesome-dsh-plugin data/plugins](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin/tree/main/data/plugins) → no WhaleHarness entry (frame 2026-09-04T18:4xZ).
5. **Staged candidates (public anchor = audit + store)**: dsh-design-qa 0.1.4 (sunxin-ai), dsh-token-pet 0.1.1 (Jimmy0123-ux), dsh-mcp-manage 0.2.0 (null119), meow-cachebilling 0.6.0 (Phant0Meow) are each PASS-zero-issues in audit.json at the frame above; the store stays 182 until a receipt lands — the first ship will show as plugins.json ≥ 183.
6. **Site mechanism fixes**: `https://whaleharness.com/audit.html` contains the `s-cta-audited` span bound to `/audit.json` entries length in JS (deployed 2026-09-04T00:30Z); `https://whaleharness.com/press.html` was refreshed from live JSON at deploy time (2026-09-04T12:30Z). `https://whaleharness.com/redline-audit.html` shows the same `2026-09-04T12:42:03Z` frame as audit.json (auto-fresh, 3 more cycles verified).
7. **Submission box**: watcher frame 2026-09-04T18:00Z — 35 items, mtimes unchanged, zero new external tarballs since the kwawa return case (published 2026-08-27); by the round frame that is day 68 of zero external submissions.

---

## The loop keeps turning (循环在转,不夸大)

- Audit: 2,775 (week-6 frame) → 2,784 (week-7 frame) → 2,808 (this frame): **+33 in two days**; PASS 1,194 → 1,197 → 1,207.
- Store: flat 182 across both windows; machine channel staged 4 candidates, shipped 0 (receipt gate), deferred several content-empty PASSes with actionable reasons.
- PASS pool vs store: 1,207 : 182 ≈ **6.6×** — the untapped, growing candidate pool.
- Traffic: uv_total 9,643 @ 2026-09-04T18:15:02Z; the 2-day ai_agent rhythm missed its 09-04 beat (19 by 18:15Z); human hits 2,566 today — high day, recorded as a data point.
- Indexing: IndexNow channel re-opened; all 213 sitemap URLs submitted (api.indexnow.org batch POST 200 + www.bing.com GET 200 ×4, 2026-09-04T18:4xZ).

Next expected signals: a staged receipt lands → plugins.json 183+ and the tarball goes live; the next audit generations at ~18:43/00:43/06:43/12:43 UTC; a merge or rejection on either marketplace submission (week-7 packages); new PASS candidates diffing into the machine-channel queue; any first external submission to the public box; and whether the ai_agent surge resumes on 09-06 (its 2-day pattern would put it there).

(帧:2026-09-04, round 100)
