# WhaleHarness

A plugin store for [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (DSH): a pod of plugins in the deep sea.

**Site: https://whaleharness.com** — bilingual (EN/中文), every plugin verified in a real DSH session before shipping.

[![site](https://img.shields.io/badge/site-whaleharness.com-4fc3f7)](https://whaleharness.com) [![plugins](https://img.shields.io/badge/plugins-6-4fc3f7)](https://whaleharness.com/plugins.json)

## Pod members (5)

| Plugin | Tool | What it does |
|---|---|---|
| whale-praise | `whale_praise` | Cetacean-grade praise for any named deed. |
| whale-fortune | `whale_fortune` | Deep-sea aphorisms on demand. |
| whale-submit | `whale_submit` | Package your own plugin and PUT it to the public submission box — from inside a DSH session. |
| whale-status | `whale_status` | Site checkup: HTTPS, DNS, TLS expiry, sha256 integrity of every published tarball. |
| whale-brand-check | `whale_brand_check` | Scores copy against the whale-brand voice rules. |

## Install

```sh
dsh plugin --profile web add -w https://whaleharness.com/plugins/whale-praise-0.1.0.tgz?src=install
```

All install commands are one-liners on the site, with `?src=install` attribution and sha256 checksums in [plugins.json](dist/plugins.json).

## Skills

- `whale-brand` — brand voice (deep, calm, witty)
- `whale-marketing` — promotion playbook

Install: `mkdir -p "$DSH_HOME/skills" && curl -fsSL https://whaleharness.com/skills/whale-brand-0.1.0.tar.gz | tar xz -C "$DSH_HOME/skills"`

## Publish your plugin here

1. Check [docs/REVIEW.md](docs/REVIEW.md) for the format and the safety red lines.
2. Either PUT your tarball to the public submission box, or install whale-submit and do it from a session.
3. Review is transparent: submissions are publicly readable; verdicts are posted publicly.

## Repository layout

- `plugins/` — cordis bundle sources (three files each: package.json, cordis.patch.yml, lib/index.js)
- `skills/` — SKILL.md sources
- `dist/plugins.json` — the live store manifest (sha256-checked)
- `deploy/` — nginx site config, stats aggregator, press-page generator
- `docs/REVIEW.md` — review checklist used for every submission
- `ROUNDS.md` — the public build log: every round of work, including the mistakes

## The build log

The site was built live, round by round, with the process recorded in [ROUNDS.md](ROUNDS.md) and replayed as an async text livestream at https://whaleharness.com/live.html — every pitfall documented actually broke a boot.

## License

MIT for all plugin sources.
