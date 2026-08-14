#!/usr/bin/env python3
"""WhaleHarness public stats: aggregate nginx access log into stats.json."""
import datetime
import json
import re
from collections import Counter
from pathlib import Path

LOG = Path("/var/log/nginx/access.log")
OUT = Path("/srv/whaleharness/stats.json")

lines = LOG.read_text(errors="ignore").splitlines()
today = datetime.datetime.utcnow().strftime("%d/%b/%Y")

ips = set()
uv_today = set()
installs = 0
puts = 0
crawlers = 0
downloads = Counter()

CRAWLER = re.compile(r"bingbot|googlebot|GPTBot|ClaudeBot|Bytespider|Amazonbot", re.I)
DL = re.compile(r'"GET /(plugins|skills)/[^"]*\.(tgz|tar\.gz)')

for line in lines:
    m = re.match(r"^(\S+) - - \[([^\]]+)\]", line)
    if not m:
        continue
    ip, ts = m.group(1), m.group(2)
    ips.add(ip)
    if today in ts:
        uv_today.add(ip)
    if "tgz?src=install" in line:
        installs += 1
    if '"PUT /submit/' in line:
        puts += 1
    if CRAWLER.search(line):
        crawlers += 1
    m2 = DL.search(line)
    if m2:
        downloads[Path(m2.group(0).split(" ")[1]).name] += 1

data = {
    "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "uv_total": len(ips),
    "uv_today": len(uv_today),
    "hits": len(lines),
    "installs": installs,
    "submission_puts": puts,
    "crawler_hits": crawlers,
    "downloads": [{"file": k, "count": v} for k, v in downloads.most_common(10)],
}
OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2))
OUT.chmod(0o644)
print(json.dumps(data, ensure_ascii=False))
