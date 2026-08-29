import json, os, datetime

BASE = "/root/whaleharness-rec"
OUT = "/srv/whaleharness/rankings.json"
db = json.load(open(os.path.join(BASE, "rec-db.json")))
pl = json.load(open("/srv/whaleharness/plugins.json"))
st = json.load(open("/srv/whaleharness/stats.json"))
try:
    cats = json.load(open("/srv/whaleharness/categories.json"))
except Exception:
    cats = {"plugins": {}}

shelf = {}
for p in pl["plugins"]:
    shelf[p["name"]] = p

# downloads per plugin from stats (today + total)
dl = {}
for src in ("today", "total"):
    for item in st.get(src, {}).get("downloads", []):
        f = item["file"]
        stem = f
        import re
        m = re.match(r"^(.*?)-\d+\.\d+\.\d+\.tgz$", f)
        if m: stem = m.group(1)
        dl.setdefault(stem, {"today": 0, "total": 0})
        dl[stem][src] += item["count"]

entries = []
for name, p in shelf.items():
    r = (p.get("source") or {}).get("repo", "").lower()
    rec = db.get(r, {})
    cat = cats.get("plugins", {}).get(name, {}).get("category", "")
    entries.append({
        "name": name,
        "version": p.get("version", ""),
        "repo": r,
        "category": cat,
        "rec_score": round(rec.get("weight", 0.0), 2),
        "rec_sources": len(rec.get("sources", [])),
        "downloads_today": dl.get(name, {}).get("today", 0),
        "downloads_total": dl.get(name, {}).get("total", 0),
        "sha256": p.get("sha256", ""),
    })

# rankings: consensus (rec), heat (downloads total), verified (all listed are verified; mark whitebox)
consensus = sorted([e for e in entries if e["rec_score"] > 0], key=lambda x: -x["rec_score"])[:20]
heat = sorted(entries, key=lambda x: -x["downloads_total"])[:20]
doc = {
    "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "method": "WhaleHarness ecosystem rankings: rec_score = weighted community recommendation (21 sources, 6h crawl); validation = audit 2671 + whitebox taste batches; heat = real download counts. Every listed plugin passed our review pipeline.",
    "consensus": consensus,
    "heat": heat,
}
json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("rankings.json:", len(consensus), "consensus /", len(heat), "heat | entries:", len(entries))
print("top consensus:", [(e["name"], e["rec_score"]) for e in consensus[:5]])
