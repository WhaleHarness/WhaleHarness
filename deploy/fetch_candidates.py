#!/usr/bin/env python3
"""Fetch DSH candidate repos from GitHub topic search.

v3 (round19, dispatch 07:05Z/07:15Z): ghgate SINGLE-TRACK. The v2 internal
budget/cooldown/abuse handling is REMOVED (dual-track = stale window, 07:15Z ②).
All search requests go through tools/ghgate.py, which now owns:
  - quota ledger (deploy/.gh-ledger.jsonl) — one place for every caller
  - cooldown gate (deploy/.fetch-flag): token refused locally while flagged
  - abuse detection (403/422 spammy -> marker + Flagged)
  - rate-limit retry/backoff
fetch keeps what is fetch-specific: incremental window, per-topic page cap,
merge + atomic write of the pool, anonymous pacing, exit-code semantics.

v4 (round29, dispatch 04:30Z ② — 候选源多元化): SECOND candidate source.
Topic search (the only source until now) is blocked by the account's spammy
flag, so candidates now ALSO come from the public dsh-suite plugin directory:
  - https://raw.githubusercontent.com/whyihaveyou/dsh-suite/main/data/plugins.json
  - 1600+ DSH plugin repos, refreshed hourly by the maintainer, anonymous raw
    fetch (NOT the GitHub API) -> zero quota, zero token, no ghgate.
  - dsh-suite runs EVERY round regardless of token/cooldown state; topic-search
    results (fresher pushed_at) override same-repo entries.
  - v3 zero-result protection is relaxed: the round is useful whenever the
    dsh-suite pull succeeds (it always has candidates); exit 1 only when BOTH
    sources fail.

v2 semantics preserved (dispatch 06:25Z acceptance, 行为不变):
  - INCREMENTAL by pushed_at window; full re-pull only when pool empty / --full
  - PER-TOPIC PAGE CAP (TOPIC_PAGES) + GLOBAL REQUEST BUDGET via gateway
    (WH_FETCH_MAX_REQ, default 6) — a single topic can't hog the round
  - MERGE: fetched repos update/append, pool never replaced by a smaller/empty
    fetch, PARTIAL results always merged even when the round stops early
  - ATOMIC WRITE: tmp + os.replace()
  - COOLDOWN HANDLING: while deploy/.fetch-flag is fresh, token search is refused
    by the gateway and this script runs ANONYMOUS-only (keeps pool fresh)
  - ANON FALLBACK: if a token pass hits abuse, the gateway writes the marker and
    this script falls back to anonymous for the rest of the round
  - Zero-result protection: nothing fetched => exit 1, pool untouched

Usage: python3 fetch_candidates.py [--out PATH] [--keep-forks] [--full] [--days N]
                                    [--since YYYY-MM-DD]
Output: lines of "owner/repo stars archived pushed_at" (deduped), stats on stderr.
Exit codes: 0 = pool updated (or partial merged on budget/ratelimit);
            1 = fetch failed (pool kept/partial merged on flagged/error).
"""
import json
import os
import re
import sys
import time
import datetime
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from ghgate import GhGate, Flagged, RateLimited, BudgetExceeded, GhError

ROOT = os.environ.get('WH_ROOT', '/opt/whaleharness-audit')
OUT = ROOT + '/deploy/candidates.txt'
BUDGET = int(os.environ.get('WH_FETCH_MAX_REQ', '6'))
TOPIC_PAGES = int(os.environ.get('WH_FETCH_TOPIC_PAGES', '2'))
DEFAULT_DAYS = int(os.environ.get('WH_FETCH_DAYS', '2'))
ANON_FALLBACK = os.environ.get('WH_FETCH_ANON', '1') != '0'
SLEEP_SEC = 7 if not os.path.exists(ROOT + '/github-moby.txt') else 3

# round29: second candidate source — dsh-suite directory (anonymous raw,
# no GitHub API, hourly-refreshed by its maintainer).
DSH_SUITE_URL = 'https://raw.githubusercontent.com/whyihaveyou/dsh-suite/main/data/plugins.json'

gh = GhGate("fetch_candidates", budget=BUDGET, root=ROOT)

if '--out' in sys.argv:
    OUT = sys.argv[sys.argv.index('--out') + 1]
FULL = '--full' in sys.argv
KEEP_FORKS = '--keep-forks' in sys.argv
DAYS = DEFAULT_DAYS
if '--days' in sys.argv:
    DAYS = int(sys.argv[sys.argv.index('--days') + 1])
SINCE = ''
if '--since' in sys.argv:
    SINCE = sys.argv[sys.argv.index('--since') + 1]

TOPICS = ['deepseek-harness', 'dsh-plugin', 'dsh']


def log(*a):
    print(*a, file=sys.stderr)


def load_pool(path):
    pool = {}
    if os.path.exists(path):
        for line in open(path, encoding='utf-8'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            name = parts[0]
            if '/' not in name:
                continue
            pool[name] = {
                'stars': parts[1] if len(parts) > 1 else '0',
                'archived': parts[2] if len(parts) > 2 else 'False',
                'pushed_at': parts[3] if len(parts) > 3 else '',
            }
    return pool


def write_pool(pool, path):
    """Atomic write: tmp + os.replace. Never truncates the live pool on failure."""
    lines = sorted('%s %s %s %s' % (n, m['stars'], m['archived'], m['pushed_at'])
                   for n, m in pool.items())
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n' if lines else '')
    os.replace(tmp, path)
    return len(lines)


def fetch_dsh_suite():
    """Anonymous raw pull of the dsh-suite plugin directory (NOT the GitHub API —
    zero quota, no token, no ghgate). Returns owner/repo -> meta dict.
    The directory is refreshed hourly by its maintainer (see _meta.generated_at).
    Entries carry repo (owner/name), stars and last_push (YYYY-MM-DD)."""
    out = {}
    with urllib.request.urlopen(DSH_SUITE_URL, timeout=30) as r:
        data = json.loads(r.read())
    for e in data.get('plugins', []):
        repo = e.get('repo') or ''
        if '/' not in repo:
            # defensive fallback: parse owner/name out of the GitHub URL
            m = re.search(r'github\.com/([^/]+/[^/]+)/?$', e.get('url') or '')
            repo = m.group(1) if m else ''
        if '/' not in repo:
            continue
        try:
            stars = int(e.get('stars') or 0)
        except (TypeError, ValueError):
            stars = 0
        out[repo] = {
            'fork': False,
            'archived': False,
            'stars': stars,
            'pushed_at': (e.get('last_push') or '')[:10],
        }
    return out


def search(topic, since_q, anon):
    """One topic, incremental window, at most TOPIC_PAGES requests, via ghgate.
    Returns (items, requests_used, stop, reason)."""
    items, page, used = [], 1, 0
    while True:
        # space-separated search terms; quote() must NOT be given the '+' join form
        # (it would encode '+' to %2B and GitHub would treat the whole string as one
        # literal token -> 0 results, observed in round18 test)
        q = 'topic:%s pushed:>=%s' % (topic, since_q) if since_q else 'topic:' + topic
        url = ('https://api.github.com/search/repositories?q=' + urllib.parse.quote(q) +
               '&per_page=100&page=%d' % page)
        try:
            d = gh.request('GET', url, anon=anon)
        except Flagged as e:
            log('request blocked topic=%s page %d: %s' % (topic, page, e))
            return items, used, True, 'flagged'
        except RateLimited as e:
            log('request rate-limited topic=%s page %d: %s' % (topic, page, e))
            return items, used, True, 'ratelimit'
        except BudgetExceeded as e:
            log('BUDGET HIT (%d) — stopping further requests: %s' % (BUDGET, e))
            return items, used, True, 'budget'
        except GhError as e:
            log('request error topic=%s page %d: %s' % (topic, page, e))
            return items, used, True, 'error'
        got = d.get('items', [])
        if not got:
            log('no items topic=%s page %d (total %s)' % (topic, page, d.get('total_count')))
            break
        for it in got:
            items.append(it)
        total = d.get('total_count', 0)
        log('topic=%s page %d: +%d (running %d / total %s)' % (topic, page, len(got), len(items), total))
        if page * 100 >= total or len(got) < 100:
            break
        page += 1
        used += 1
        if used >= TOPIC_PAGES:
            log('topic page cap hit (%s, %d pages)' % (topic, TOPIC_PAGES))
            break
        time.sleep(SLEEP_SEC)
    return items, used, False, ''


def run_pass(since_q, anon):
    """Search all topics under the gateway budget. Returns (fetched, stop, reason)."""
    fetched, stop, reason = {}, False, ''
    for topic in TOPICS:
        items, _u, s, r = search(topic, since_q, anon)
        for it in items:
            fetched[it['full_name']] = {
                'fork': it.get('fork', False),
                'archived': it.get('archived', False),
                'stars': it.get('stargazers_count', 0),
                'pushed_at': it.get('pushed_at', ''),
            }
        if s:
            stop, reason = True, r
            break
    return fetched, stop, reason


def merge_and_write(pool, fetched, out_path):
    before = len(pool)
    kept = 0
    for name, meta in fetched.items():
        if meta['fork'] and not KEEP_FORKS:
            continue
        kept += 1
        pool[name] = {'stars': str(meta['stars']), 'archived': str(meta['archived']),
                      'pushed_at': meta['pushed_at'][:10] or pool.get(name, {}).get('pushed_at', '')}
    total = write_pool(pool, out_path)
    return before, kept, total


def main():
    global FULL  # pool-empty fallback reassigns it below
    cooldown = gh.is_flagged()
    pool = load_pool(OUT)
    if not pool:
        log('pool empty -> full re-pull fallback (allowed once)')
        FULL = True
        if cooldown:
            log('WARNING: pool empty AND token in cooldown — anonymous budget-limited fill only')

    since_q = ''
    if SINCE:
        since_q = SINCE
    elif not FULL:
        since_q = (datetime.date.today() - datetime.timedelta(days=DAYS)).isoformat()
        log('incremental window: pushed:>=%s (--full to re-pull everything)' % since_q)

    # round29: seed the round with the dsh-suite directory (anonymous raw,
    # zero quota) BEFORE any token/cooldown branching — it always runs.
    fetched, stop, reason = {}, False, ''
    try:
        ds = fetch_dsh_suite()
        for name, meta in ds.items():
            fetched[name] = meta
        log('dsh-suite source: %d candidate repos (anonymous raw, 1 request)' % len(ds))
    except Exception as e:
        log('dsh-suite source FAILED: %s (continuing with topic search only)' % e)

    has_token = os.path.exists(gh.token_path)

    if has_token and not cooldown:
        log('token mode: %s' % gh.token_path)
        f2, stop, reason = run_pass(since_q, anon=False)
        fetched.update(f2)  # topic results override dsh-suite same-repo entries
        if stop and reason == 'flagged' and ANON_FALLBACK:
            log('token blocked (abuse) — marker written by gateway; falling back to ANONYMOUS search')
            a_fetched, a_stop, a_reason = run_pass(since_q, anon=True)
            for name, meta in a_fetched.items():
                fetched[name] = meta
            before, kept, total = merge_and_write(pool, fetched, OUT)
            if a_stop:
                log('ANON FALLBACK ALSO BLOCKED (%s) — partial merged: pool %d -> %d (+%d)' %
                    (a_reason, before, total, kept))
                return 1
            log('anon fallback OK: +%d repos; token stays in cooldown; pool %d -> %d' %
                (kept, before, total))
            return 0
    elif has_token:
        log('token in cooldown — anonymous-only round')
        f2, stop, reason = run_pass(since_q, anon=True)
        fetched.update(f2)
    else:
        log('WARNING: no token — anonymous search only (10/min, low quota)')
        f2, stop, reason = run_pass(since_q, anon=True)
        fetched.update(f2)

    if stop:
        # Merge whatever we got BEFORE handling the stop — partial results are never lost.
        before, kept, total = merge_and_write(pool, fetched, OUT)
        log('stopped (%s) — partial merged: pool %d -> %d (+%d)' % (reason, before, total, kept))
        if reason in ('flagged', 'error'):
            return 1
        return 0  # budget / ratelimit: partial merged, pool updated

    if not fetched and not FULL:
        log('FETCH FAILED: zero repos fetched in window; keeping existing candidates file')
        return 1

    before, kept, total = merge_and_write(pool, fetched, OUT)
    log('fetch done: new/updated=%d, pool %d -> %d -> %s' % (kept, before, total, OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
