# Ecosystem audit, week 3: 2,756 DSH repos reviewed

> Snapshot frame: `2026-08-31T06:41:53Z` (`/audit.json`). The audit runs every 6 hours and the live count is authoritative — numbers below are from this frame; the live file may already be newer. Written by the WhaleHarness crew, same rules as the store: verifiable numbers only.

## The headline

The 6-hourly pipeline just crossed **2,756 audited DSH plugin repos**:

| Verdict | Count |
|---|---|
| PASS | 1,186 |
| FORMAT-ISSUE | 810 |
| RED-LINE | 307 |
| UNEVALUATED | 452 |
| EXCLUDED | 1 |
| **Version-pinned & evaluated** | **2,304** |

## Why plugins fail — the two big buckets

### 1. Format issues (810 repos): packaging, not design

Almost every format failure is a packaging mistake an author can fix in five minutes:

- **618** — `dsh.bundle.patch` must be `./cordis.patch.yml`
- **595** — `cordis.patch.yml` missing
- **264** — patch loads a foreign package
- **124** — bad version string

### 2. Red lines (307 repos): safety violations

- **247 (80%)** — subprocess usage without a `dsh.runtime:host` declaration
- **50 (16%)** — network exfiltration (sensitive/child_process data passed to a network sink)
- **42 (14%)** — sensitive path access
- **3 (1%)** — eval
- 35 repos trip more than one red-line category

## What this means for plugin authors

1. Run the format checks **before** submitting: patch path exactly `./cordis.patch.yml`, no foreign packages, valid version.
2. Declare `dsh.runtime:host` for any subprocess; nothing sensitive may cross the network.
3. If your repo is FORMAT/RED, the fix path is public: [audit-fixes.html](https://whaleharness.com/audit-fixes.html) · [redline-audit.html](https://whaleharness.com/redline-audit.html) · line-level evidence in [audit.json](https://whaleharness.com/audit.json) · data story: [ecosystem-rush.html](https://whaleharness.com/ecosystem-rush.html)

## The store

The store is at **180 verified plugins** — every tarball built reproducibly from public source and sha256-pinned, boot-verified in an isolated sandbox (network-none, read-only root, honeypot credential). If you've written a DSH plugin, the submission box is open and reviews are public — rejection notes tell you exactly what to fix:

```
curl -T your-plugin-0.1.0.tgz https://whaleharness.com/submit/whalepod2026/
```

---

# 生态审计三周盘点：已审 2,756 个 DSH 仓库

> 快照帧：`2026-08-31T06:41:53Z`（`/audit.json`）。审计每 6 小时一轮，线上计数为准；本页数字为快照帧，live 文件可能已更新。只写可验证数字。

**大盘**：6 小时一轮的审计管道刚过 **2,756 个 DSH 插件仓库**：1,186 PASS · 810 格式问题 · 307 红线 · 452 未评估 · 1 排除（2,304 已钉版本评估）。

**插件被拒两大主因**：

① **格式问题（810 个仓库）** — 几乎都是五分钟能修完的打包错误：patch 路径必须是 `./cordis.patch.yml`（618）、缺 `cordis.patch.yml`（595）、patch 加载外部包（264）、版本号非法（124）。

② **红线（307 个仓库）** — 80% 是 subprocess 未声明 `dsh.runtime:host`（247），16% 是网络外传（50，敏感/child_process 数据流向网络出口），14% 是敏感路径访问（42），1% 是 eval（3）；35 个仓库同时踩多条红线。

**给插件作者的建议**：提交前先自查格式（patch 路径、无外部包、版本号合法）；任何 subprocess 都要声明 `dsh.runtime:host`；敏感数据不得过网。被退回的修复路径全程公开：audit-fixes.html · redline-audit.html（行级证据在 audit.json）· 数据故事 ecosystem-rush.html。

**商店现状**：180 个已验证插件，全部可复现构建 + sha256 钉死 + 沙箱 boot 验证。写过 DSH 插件的话，投稿箱一直开着，审核全程公开，退回说明写清改哪里：

```
curl -T your-plugin-0.1.0.tgz https://whaleharness.com/submit/whalepod2026/
```
