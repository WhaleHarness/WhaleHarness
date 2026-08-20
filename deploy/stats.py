#!/usr/bin/env python3
"""WhaleHarness public stats: aggregate nginx access log into stats.json.

Two groups (per dispatch 2026-08-16T12:25Z — "single-day numbers are meaningless, show cumulative"):
  - today : real-time aggregation of the current UTC day from /var/log/nginx/access.log
  - total : cumulative = daily snapshot files (/srv/whaleharness/stats-history/YYYY-MM-DD.json)
            summed + today's real-time numbers. Real computation, no fabrication.
  - history: the per-day snapshots, newest first.

Downloads vs crawlers (per dispatch 2026-08-16T12:40Z — "crawler fetches are not installs"):
  - download counts EXCLUDE lines whose UA matches CRAWLER (GPTBot / Claude-SearchBot etc.
    fetch tarballs from the sitemap; that is crawling, not a human downloading).
  - non-crawler UAs (curl / node / browser) are kept — they may be real people.
  - crawler_hits uses the same CRAWLER regex, so the two stay consistent.

Self-pollution (per dispatch 2026-08-16T12:55Z — "node UA no-param downloads are the site's own
whale_status health check; it GETs every tarball once per run"):
  - download counts ALSO EXCLUDE lines whose URL carries ?src=verify — that is the site's own
    verification traffic (whale_status adds ?src=verify; Moby ships it in 0.2.2).
  - installs keep counting only src=install, unchanged.
  - historical snapshots (8-15 / 8-14) were produced by whale_status versions that did NOT send
    ?src=verify, so their node-UA batches are indistinguishable from real humans and stay as-is
    (honest: we do not retroactively invent a filter for them).

Per-plugin installs (per dispatch 2026-08-17T01:55Z — "track installs per plugin, milestone
'10 installs' needs verifiable data"):
  - installs_by_plugin counts ?src=install requests grouped by plugin name, extracted from the
    URL path: /plugins/whale-status-0.2.2.tgz?src=install -> whale-status (version suffix
    stripped, so all versions of one plugin share one bucket).
  - the per-plugin sum matches the flat installs counter on the same lines (same detection;
    only extractable names are bucketed). Snapshot files written from this version onwards
    carry the field; older snapshots (8-14/8-15/8-16) predate it and contribute nothing to the
    cumulative per-plugin table (honest: no backfill from rotated logs).

Daily snapshot: `whaleharness-stats.py --snapshot yesterday` aggregates the just-ended
calendar day from the access log and writes stats-history/YYYY-MM-DD.json.
Cron line to add (/etc/cron.d/whaleharness-stats):
    5 0 * * * root /usr/bin/python3 /usr/local/bin/whaleharness-stats.py --snapshot yesterday > /dev/null
(00:05 runs before logrotate ~00:55, so the log still holds the full previous day.)

One-time history rebuild (e.g. 2026-08-15 from the rotated log, re-run after this fix so the
8-15 downloads drop the crawler fetches):
    /usr/bin/python3 /usr/local/bin/whaleharness-stats.py --snapshot 2026-08-15 --log /var/log/nginx/access.log.1

Legacy keys (uv_total / uv_today / hits / installs / submission_puts / crawler_hits / downloads)
are kept for old consumers; uv_total now means the CUMULATIVE total (the fix the user asked for).
"""
import argparse
import datetime
import json
import re
from collections import Counter
from pathlib import Path

LOG = Path("/var/log/nginx/access.log")
HIST = Path("/srv/whaleharness/stats-history")
OUT = Path("/srv/whaleharness/stats.json")
SINCE = "2026-08-14"

# Known search/AI crawler UAs. Download counting skips lines matching this regex:
# a crawler fetching a tarball is crawling, not an install/download (dispatch 12:40Z).
# Conservative list of well-known bots; deliberately NOT matching generic "bot" or
# curl/node/python (those may be real humans and must keep counting).
CRAWLER = re.compile(
    r"bingbot|googlebot|GoogleOther|Google-InspectionTool|GPTBot|OAI-SearchBot|ChatGPT-User|"
    r"ClaudeBot|Claude-SearchBot|anthropic|PerplexityBot|Bytespider|Applebot|YandexBot|"
    r"Baiduspider|DuckDuckBot|DotBot|SemrushBot|AhrefsBot|MJ12bot|CCBot|PetalBot|Amazonbot|"
    r"facebookexternalhit|Twitterbot|LinkedInBot|archive\.org_bot|DataForSeoBot|Exabot|SeznamBot",
    re.I,
)
DL = re.compile(r'"GET /(plugins|skills)/[^"]*\.(tgz|tar\.gz)')
# ?src=install request -> capture the tarball file name so the plugin can be bucketed
INSTALL = re.compile(r'"GET /(?:plugins|skills)/([^"? ]+\.tgz)\?src=install')


def aggregate(lines, day_stamp):
    """Counters for log lines whose timestamp contains day_stamp ('16/Aug/2026')."""
    ips = set()
    installs = puts = crawlers = hits = 0
    installs_unbucketed = 0
    downloads = Counter()
    installs_by_plugin = Counter()
    for line in lines:
        m = re.match(r"^(\S+) - - \[([^\]]+)\]", line)
        if not m:
            continue
        ip, ts = m.group(1), m.group(2)
        if day_stamp not in ts:
            continue
        hits += 1
        ips.add(ip)
        is_crawler = bool(CRAWLER.search(line))
        is_verify = "?src=verify" in line
        if "tgz?src=install" in line:
            installs += 1
            mi = INSTALL.search(line)
            if mi:
                stem = mi.group(1)[:-4]  # strip ".tgz"
                mv = re.match(r"^(.*?)-(\d+(?:\.\d+)+)$", stem)
                installs_by_plugin[mv.group(1) if mv else stem] += 1
            else:
                # round29 (dispatch 02:00Z): an install line that the per-plugin
                # regex cannot bucket (non-GET method, or path outside
                # /plugins|/skills) still counts flat; record it so the
                # flat-vs-per-plugin gap is visible instead of silently lost.
                installs_unbucketed += 1
        if '"PUT /submit/' in line:
            puts += 1
        if is_crawler:
            crawlers += 1
        m2 = DL.search(line)
        # downloads = human/non-crawler fetch, and NOT the site's own verification traffic
        if m2 and not is_crawler and not is_verify:
            downloads[Path(m2.group(0).split(" ")[1]).name] += 1
    return {
        "uv": len(ips),
        "hits": hits,
        "installs": installs,
        "submission_puts": puts,
        "crawler_hits": crawlers,
        "downloads": [{"file": k, "count": v} for k, v in downloads.most_common(20)],
        "installs_by_plugin": [{"plugin": k, "count": v}
                               for k, v in installs_by_plugin.most_common(20)],
        "installs_unbucketed": installs_unbucketed,
    }


def read_snapshots():
    snaps = []
    if HIST.is_dir():
        for p in sorted(HIST.glob("*.json")):
            try:
                d = json.loads(p.read_text())
                d["date"] = p.stem
                snaps.append(d)
            except Exception:
                continue
    return snaps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", metavar="DAY", default=None,
                    help="aggregate one calendar day (YYYY-MM-DD, or 'yesterday') from --log and "
                         "write stats-history/DAY.json")
    ap.add_argument("--log", metavar="PATH", default=None,
                    help="log file to read for --snapshot (default: /var/log/nginx/access.log)")
    args = ap.parse_args()

    if args.snapshot:
        day = args.snapshot
        if day == "yesterday":
            day = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        src = Path(args.log) if args.log else LOG
        lines = src.read_text(errors="ignore").splitlines()
        stamp = datetime.datetime.strptime(day, "%Y-%m-%d").strftime("%d/%b/%Y")
        data = aggregate(lines, stamp)
        data["date"] = day
        data["source"] = "nginx access.log daily aggregation (per-day unique IPs)"
        HIST.mkdir(parents=True, exist_ok=True)
        out = HIST / f"{day}.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        out.chmod(0o644)
        print(json.dumps({"snapshot": day, "src": str(src), **data}, ensure_ascii=False))
        return

    lines = LOG.read_text(errors="ignore").splitlines()
    today = datetime.datetime.utcnow().strftime("%d/%b/%Y")
    today_data = aggregate(lines, today)

    snaps = read_snapshots()
    total = {"uv": 0, "hits": 0, "installs": 0, "submission_puts": 0, "crawler_hits": 0,
             "installs_unbucketed": 0,
             "downloads": Counter(), "installs_by_plugin": Counter()}
    for s in snaps:
        for k in ("uv", "hits", "installs", "submission_puts", "crawler_hits"):
            total[k] += int(s.get(k, 0))
        total["installs_unbucketed"] += int(s.get("installs_unbucketed", 0))
        for d in s.get("downloads", []):
            total["downloads"][d["file"]] += int(d.get("count", 0))
        for p in s.get("installs_by_plugin", []):
            total["installs_by_plugin"][p["plugin"]] += int(p.get("count", 0))
    for k in ("uv", "hits", "installs", "submission_puts", "crawler_hits"):
        total[k] += today_data[k]
    total["installs_unbucketed"] += today_data["installs_unbucketed"]
    for d in today_data["downloads"]:
        total["downloads"][d["file"]] += d["count"]
    for p in today_data["installs_by_plugin"]:
        total["installs_by_plugin"][p["plugin"]] += p["count"]
    total["downloads"] = [{"file": k, "count": v}
                          for k, v in total["downloads"].most_common(20)]
    total["installs_by_plugin"] = [{"plugin": k, "count": v}
                                   for k, v in total["installs_by_plugin"].most_common(20)]

    data = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "since": SINCE,
        "today": today_data,
        "total": total,
        "history": snaps,
        # legacy keys with corrected semantics (uv_total = cumulative since SINCE)
        "uv_total": total["uv"],
        "uv_today": today_data["uv"],
        "hits": today_data["hits"],
        "installs": today_data["installs"],
        "submission_puts": today_data["submission_puts"],
        "crawler_hits": today_data["crawler_hits"],
        "downloads": today_data["downloads"],
        "installs_by_plugin": today_data["installs_by_plugin"],
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    OUT.chmod(0o644)
    print(json.dumps({"today": today_data, "total": total, "snapshots": len(snaps)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
