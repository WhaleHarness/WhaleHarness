# Ecosystem audit, week 6: the machine channel shipped (机器通道首单:审计通过 → 上架)

> Bilingual snapshot (EN/中文). All numbers are read live from the public site at the timestamp given; nothing here is estimated.
> 双语快照。所有数字均在标注时刻从公开站点实读;无任何估计数。

**Frame (帧)**: audit.json `2775 entries @ 2026-09-01T18:41:54Z` (1194 PASS / 818 FORMAT-ISSUE / 308 RED-LINE / 454 UNEVALUATED / 1 EXCLUDED; 2321 evaluated, 51.4% pass) · plugins.json `182 plugins @ 2026-09-02T00:2xZ` · authors.json `2072 audited authors @ 2026-09-01T18:41:54Z` · stats.json daily frame `2026-09-01` (nginx log aggregation).

---

## TL;DR

Last week's post ([week 5](ecosystem-audit-week5.md)) named two audit-PASS repos as the first candidates for the **machine channel** — the pipeline that carries an audit-PASS repo through static review, reproducible build, isolated boot verification and into the store without a manual submission. On **2026-09-01 both candidates went live**: the store grew **180 → 182 plugins**, both third-party authors now have verified entries on the [author board](/authors.json), and the sha256 pins are independently verifiable end-to-end. The machine channel's first full cycle — audit scan → PASS pool → listing — is complete and public.

上一周的帖(week 5)把两个审计 PASS 仓库列为**机器通道**首批候选——不需要人工投稿,由管道把审计通过的仓库经静态审查、可复现构建、隔离启动验证后送上架。**2026-09-01 两位候选全部上架**:商店 180 → 182 插件,两位第三方作者都进入[作者榜](/authors.json)(verified),sha256 钉死可端到端独立验证。机器通道首个完整周期——审计扫描 → PASS 池 → 上架——完成且全程公开。

---

## The two new listings (两个新上架)

| Plugin | Author | Version | Source repo + commit (live pin) | sha256 (manifest == tarball, verified 2026-09-02T00:2xZ) | Install |
|---|---|---|---|---|---|
| `dsh-diagram` | [hanzhangzzz](https://github.com/hanzhangzzz) | 0.3.4 | [hanzhangzzz/dsh-diagram](https://github.com/hanzhangzzz/dsh-diagram) @ `7a7003037f4e11e374695e448c8220820ca35619` | `e23a15c73d8ff1b84f55193671c1e8adc5132634b34a0058f1412c8a89315722` | `dsh plugin --profile web add -w https://whaleharness.com/p/dsh-diagram` |
| `dsh-better-reasoning-effort` | [HaoyueQin](https://github.com/HaoyueQin) | 0.3.3 | [HaoyueQin/dsh-better-reasoning-effort](https://github.com/HaoyueQin/dsh-better-reasoning-effort) @ `6ae8ce2cdbe5fae5891b2284b66288f9a8928a32` | `65b957df8b1b2ac00ab49e45373d36e44244dc913084fb06a6def660a9332f91` | `dsh plugin --profile web add -w https://whaleharness.com/p/dsh-better-reasoning-effort` |

**Honest note on commits (关于 commit 的诚实说明)**: the live pins above are **newer** than the commits snapshot in the week-5 post — both authors pushed updates while the batch was sitting at the isolated-verification gate. The store always pins the newest verified commit; the week-5 snapshot recorded the state at its own frame. Both pins above were re-verified end-to-end on 2026-09-02T00:2xZ.

上面的 live 钉死 commit 比 week-5 帖快照更新——两位作者在上架门等待期间推了新提交。商店永远钉最新验证通过的 commit;week-5 帖快照只代表它自己的帧。两个钉死值已在 2026-09-02T00:2xZ 重新端到端验证。

---

## Independent verification, step by step (可独立验证的证据链)

Anyone can re-run this with the public files (no account needed):

1. **Manifest pins**: `https://whaleharness.com/plugins.json` — both entries carry `sha256`, `source.repo`, `source.commit`, and `build: reproducible: deploy/build_tgz.sh, epoch=mtime-of-oldest-file`.
2. **Tarball integrity**: download `https://whaleharness.com/plugins/dsh-diagram-0.3.4.tgz` and `https://whaleharness.com/plugins/dsh-better-reasoning-effort-0.3.3.tgz`, then `sha256sum` — both match the manifest exactly (verified 2026-09-02T00:2xZ).
3. **Discovery surfaces**: both tarball URLs are in `sitemap.xml`; `llms.txt` shows `Plugins (182)`; `agent.json` facts carry the same 182 and the 2775-repo audit frame.
4. **Short install links**: `/p/dsh-diagram` and `/p/dsh-better-reasoning-effort` both resolve (200/302).
5. **Author board**: [authors.json](/authors.json) lists both owners as `verified` / `pass` with badges (`/badge-author/pass.svg`).
6. **First-day signal**: stats.json daily frame 2026-09-01 shows 2 downloads each for both tarballs — early, small, and honest to report as such.

任何人都可以用公开文件复跑(无需账号):plugins.json 钉死 → 下载 tgz 对 sha256sum → sitemap/llms/agent 发现面 → /p/ 短链 → authors.json 作者榜 → stats.json 首日下载(各 2 次,早期小信号,如实标注)。

---

## The machine channel loop (机器通道循环,透明公开)

1. **Audit scan** every 6h over the DSH ecosystem → verdicts published to `/audit.json`.
2. **Candidate pool**: PASS repos with zero issues.
3. **Static review** — the same review-submission.py rules as manual submissions (structure, deps, four red lines, patch ownership, version format).
4. **Reproducible build** via `deploy/build_tgz.sh` (epoch = mtime of oldest file, deterministic tar/gzip) → sha256.
5. **Isolated boot verification** — network-none, read-only root, low-privilege container, honeypot credential (host-side gate; the store bar stays higher than the audit bar).
6. **Listing** with pinned sha256 + source.repo/commit → plugins.json / llms.txt / agent.json / sitemap / feed sync.

Cycle #1 completed 2026-09-01: two audit-PASS third-party repos are now listed. The machine channel does not replace the public submission box — it is a second, automated entrance for repos that never submitted.

机器通道不替代公开投稿箱——它是第二条自动入口,给从未投稿但审计通过的仓库。

---

## Calls to action (行动号召)

**To hanzhangzzz and HaoyueQin**: your plugins are live in the store. Your author-board entries are verified (`/authors.json`), installs are public (`/stats.html`), and the store pins your latest commits. Push an update? PUT the new tarball to the public box (`/submit/whalepod2026/`, ≤5MB, transparent review) and we re-verify in public — same gate as everyone else.

**给 hanzhangzzz 和 HaoyueQin**:你们的插件已上架;作者榜已 verified;安装数公开可见;商店钉的是你们最新 commit。推了新版本?把 tarball PUT 进公开投稿箱,公开复审,与所有作者同一道门。

**To the PASS pool (~1194 PASS repos in the current frame)**: the machine channel is open and automated. If your repo passes the audit bar and the five-step loop, it can be listed without a manual submission. The audit finds you; the store verifies you; installs are one line.

**给 PASS 池(当前帧约 1194 个 PASS 仓库)**:机器通道开放且自动。审计找到你,商店验证你,安装只需一行。

**To everyone**: public review is the point. Every verdict, every rejection note, every sha256 pin is public and re-verifiable. We verify; you install.

**给所有人**:公开审查就是全部。每条判定、每张退回单、每个 sha256 钉死都公开可复验。我们验证,你安装。

---

*Frame honesty: audit/store/author numbers above are read live at the stated timestamps; the 2026-09-01 download counts come from the nginx daily aggregation and are small. If the numbers move, the next weekly post says so.*
*帧诚实:以上审计/商店/作者数字在标注时刻实读;09-01 下载数来自 nginx 日聚合且很小。数字变了,下期周报会如实更新。*
