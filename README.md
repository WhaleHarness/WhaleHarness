# WhaleHarness

A **verified plugin store & public ecosystem audit** for [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (DSH). Bilingual (EN/中文), built in public — every plugin is boot-verified in a real DSH session before shipping, and the wider ecosystem is audited every 6 hours.

**Site: https://whaleharness.com** · Live stats: https://whaleharness.com/stats.html

[![site](https://img.shields.io/badge/site-whaleharness.com-4fc3f7)](https://whaleharness.com)
[![verified plugins](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fwhaleharness.com%2Fplugins.json&query=plugins.length&label=verified%20plugins&color=4fc3f7)](https://whaleharness.com/plugins.json)
[![audited repos](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fwhaleharness.com%2Faudit.json&query=entries.length&label=audited%20repos&color=4fc3f7)](https://whaleharness.com/audit.json)

## The store

Browse: [store.html](https://whaleharness.com/store.html) · [plugins.json](https://whaleharness.com/plugins.json) (machine-readable, sha256 per tarball) · [stats.html](https://whaleharness.com/stats.html)

Every plugin is:

- **Verified** — built reproducibly from public source (`source.repo` + commit), boot-checked in an isolated low-privilege sandbox with a honeypot credential
- **Pinned** — sha256 checksums in plugins.json, no silent mutation
- **Installable in one line** — short link by plugin name:

```sh
dsh plugin --profile web add -w https://whaleharness.com/p/whale-praise
```

## Ecosystem audit

Every 6 hours the pipeline audits the wider DSH plugin ecosystem (third-party repos, not just this store) and publishes machine-readable verdicts with evidence:

- [audit.json](https://whaleharness.com/audit.json) — per-repo verdicts
- [audit-fixes.html](https://whaleharness.com/audit-fixes.html) — how to fix each tier
- [redline-audit.html](https://whaleharness.com/redline-audit.html) — the safety red lines that get plugins rejected
- [audit-trends.html](https://whaleharness.com/audit-trends.html) — the data story over time
- [ecosystem-audit-week3.md](docs/ecosystem-audit-week3.md) — what gets DSH plugins rejected: the numbers (bilingual, snapshot with live-data note)
- [ecosystem-audit-week4.md](docs/ecosystem-audit-week4.md) — week 4: the store follows the signal (consensus-top plugins, the untapped PASS pool; bilingual snapshot)
- [ecosystem-audit-week5.md](docs/ecosystem-audit-week5.md) — week 5: from PASS to store listing (the machine channel; two new candidates staged, bilingual snapshot)
- [ecosystem-audit-week6.md](docs/ecosystem-audit-week6.md) — week 6: the machine channel shipped (both week-5 candidates are live in the store, 180→182 plugins; verified sha256 + author board, bilingual snapshot)
- [ecosystem-audit-week7.md](docs/ecosystem-audit-week7.md) — week 7: a store is not a front door (distribution week: the two in-client marketplace upstreams mapped, submission packages public and pending; audit 2,784, bilingual snapshot)

Put your repo's audit badge in its README:

```md
[![WhaleHarness audit](https://whaleharness.com/badge/<owner>/<repo>/badge.svg)](https://whaleharness.com/audit.html)
```

## The first-party pod

This repo is the first-party pod source; the live store also hosts many more third-party plugins (count is live in the badge above):

| Plugin | Tool | What it does |
|---|---|---|
| whale-praise | `whale_praise` | Cetacean-grade praise for any named deed. |
| whale-fortune | `whale_fortune` | Deep-sea aphorisms on demand. |
| whale-submit | `whale_submit` | Package your own plugin and PUT it to the public submission box — from inside a DSH session. |
| whale-status | `whale_status` | Site checkup: HTTPS, DNS, TLS expiry, sha256 integrity of every published tarball. |
| whale-brand-check | `whale_brand_check` | Scores copy against the whale-brand voice rules. |

## Skills

- `whale-brand` — brand voice (deep, calm, witty)
- `whale-marketing` — promotion playbook

Install: `mkdir -p "$DSH_HOME/skills" && curl -fsSL https://whaleharness.com/skills/whale-brand-0.1.0.tar.gz | tar xz -C "$DSH_HOME/skills"`

## Publish your plugin here

The submission box is public and review is transparent — verdicts are posted publicly, and a rejection note tells you exactly what to fix.

1. Read [docs/REVIEW.md](docs/REVIEW.md) and [redline-audit.html](https://whaleharness.com/redline-audit.html) for the format, the safety red lines, and the top rejection reasons.
2. Build a valid npm-style tarball, then PUT it to the box:

```sh
curl -T my-plugin-0.1.0.tgz https://whaleharness.com/submit/whalepod2026/my-plugin-0.1.0.tgz
```

3. Watch it go through public review — real case: [kwawa-return.html](https://whaleharness.com/kwawa-return.html) (rejected → fixed → shipped within a day).

## Help improve it

Built in public, needs crew feedback:

- Ideas and questions: [Discussions](https://github.com/WhaleHarness/WhaleHarness/discussions)
- Bugs and problems: [Issues](https://github.com/WhaleHarness/WhaleHarness/issues)
- Fixes and improvements: open a PR — review is the same transparent process as plugin submissions
- Review appeals: every rejection note lists exactly what to fix; re-submit when done

## Repository layout

- `plugins/` — first-party cordis bundle sources (package.json, cordis.patch.yml, lib/index.js)
- `skills/` — SKILL.md sources
- `dist/plugins.json` — static repo snapshot (the live manifest is https://whaleharness.com/plugins.json)
- `tools/` — audit & review pipeline (`review-submission.py`, listings sync, etc.)
- `deploy/` — nginx site config, stats aggregator, press-page generator
- `docs/REVIEW.md` — review checklist used for every submission
- `ROUNDS.md` — the public build log: every round of work, including the mistakes

## The build log

The site was built live, round by round, with the process recorded in [ROUNDS.md](ROUNDS.md) and replayed as an async text livestream at https://whaleharness.com/live.html — every pitfall documented actually broke a boot.

## License

MIT for all plugin sources.
