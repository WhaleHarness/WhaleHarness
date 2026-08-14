# whale-memory

Explicit cross-session memory for DeepSeek Harness. The model decides what is worth
remembering, tells the whale, and any later session on the same machine can recall it.

## Install

```sh
dsh plugin --profile web add -w https://whaleharness.com/plugins/whale-memory-0.1.0.tgz?src=install
```

## Tools

- `whale_memory_set(key, value)` — remember one named fact (overwrites)
- `whale_memory_get(key)` — recall it
- `whale_memory_list()` — every key with last-updated time, newest first
- `whale_memory_delete(key)` — forget it

## Storage & safety

- One JSON file: `~/.dsh/storages/whale-memory/memory.json` (atomic replace writes)
- No subprocess, no network, no credential access — the WhaleHarness red lines
- Limits: 1000 keys, 64KB per value, key charset `[A-Za-z0-9._:-]{1,128}`

## How it differs from the built-in session reference

DSH's built-in cross-session reference is passive and read-only (it surfaces candidate
snapshots). whale-memory is explicit and writable: the model curates what is remembered,
so continuity becomes a decision, not an accident.
