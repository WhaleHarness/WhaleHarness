## What this PR does

Adds three first-party plugins from the WhaleHarness monorepo (`WhaleHarness/WhaleHarness`, `plugins/` subpackages) to the registry, one entry per plugin:

| entry | category | what it does |
|---|---|---|
| `WhaleHarness/WhaleHarness#plugins/whale-memory` | memory | explicit cross-session memory via the official DSH storage-domain service (set/get/list/delete tools) |
| `WhaleHarness/WhaleHarness#plugins/whale-digest` | tools | offline extractive summarizer (summary + 5 keywords + source length, ZH/EN) |
| `WhaleHarness/WhaleHarness#plugins/whale-submit` | dev | packages a plugin directory and PUTs it to a public submission box (≤5MB) |

## Checks already done

- Each subpackage declares `dsh.bundle` in its `package.json` (verified: `./cordis.patch.yml` in all three).
- Repo: `WhaleHarness/WhaleHarness` is older than 1 day, has far more than 10 commits, carries the `dsh-plugin` topic, and is actively maintained (last commit 2026-09-01T06:28:02Z).
- Descriptions are verified against the actual `lib/index.js` source in each subpackage (tool names, limits 1000 keys / 64KB per value for whale-memory, 5 keywords for whale-digest, 5MB limit for whale-submit) — no superlatives.
- These are not meta-packages and carry no third-party dependency snapshots.
- One entry file per plugin; 3 entries total (within the per-PR limit).

These plugins are also published at the WhaleHarness store (whaleharness.com) with boot-verified listings and pinned sha256 checksums.
