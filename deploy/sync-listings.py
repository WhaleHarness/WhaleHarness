#!/usr/bin/env python3
"""sync-listings.py — 收录三件套同步器 (mechanism fix for recurring drift).

Why this exists (blameless root cause):
  plugins.json is the single source of truth for listings, updated by the
  listing pipeline whenever a new plugin is boarded. agent.json / llms.txt /
  sitemap.xml are derived surfaces; hand-syncing them after each listing
  repeatedly drifted (observed 2026-08-15~08-17, 5+ recurrences). This script
  regenerates all three from plugins.json so the drift cannot recur.

Usage:
  python3 sync-listings.py [--base DIR] [--out DIR]
    --base DIR  read live/current files from DIR (default: ./work)
    --out DIR   write regenerated files to DIR (default: .)

Behaviour:
  1. agent.json — plugins array rebuilt from plugins.json via the same field
     mapping the existing entries use (install_short, absolute tarball URL).
     Top-level identity/promo/key_pages sections are preserved verbatim.
     generated_at is bumped to now.
  2. llms.txt — the "## Plugins (N)" section is rewritten: header count equals
     the real plugin count, every plugins.json name gets a line. Curated line
     text from the base file is preserved by plugin name; plugins without a
     curated line fall back to description_en. Add a curated override below.
  3. sitemap.xml — rebuilt from the base file's page URLs (non-plugin, non-
     skill entries are copied verbatim in order) + every tarball in
     plugins.json + the skills list. All URLs must be 200-verified before
     deploy (see DEPLOY note).
"""
import argparse, datetime, json, pathlib, re, sys

BASE_URL = "https://whaleharness.com"
SKILLS = [
    ("whale-brand-0.1.0.tar.gz", "/skills/whale-brand-0.1.0.tar.gz"),
    ("whale-marketing-0.1.0.tar.gz", "/skills/whale-marketing-0.1.0.tar.gz"),
    ("whale-plugin-dev-0.1.0.tar.gz", "/skills/whale-plugin-dev-0.1.0.tar.gz"),
]

# Curated llms.txt line overrides keyed by plugin name (appended after the
# tool description). Leave empty for plugins whose description_en is enough.
LLMS_OVERRIDES = {
    "dsh-x-archive": "Community submission (returning author), verified by full review loop 2026-08-17",
}


def transform_plugin(p: dict) -> dict:
    """plugins.json entry -> agent.json entry (same mapping as existing entries)."""
    return {
        "name": p["name"],
        "tool": p["tool"],
        "version": p["version"],
        "description_en": p["description_en"],
        "install": p["install"],
        "install_short": f"dsh plugin --profile web add -w {BASE_URL}/p/{p['name']}",
        "tarball": f"{BASE_URL}{p['tarball']}" if p["tarball"].startswith("/") else p["tarball"],
        "sha256": p["sha256"],
        "source": p["source"],
    }


def transform_skill(s: dict) -> dict:
    """plugins.json skill entry -> agent.json skill entry (same field set as the
    existing first-party skill entries: name/version/description_en/install)."""
    out = {
        "name": s["name"],
        "version": s["version"],
        "description_en": s.get("description_en", s.get("description", "")),
        "install": s["install"],
    }
    if "sha256" in s:
        out["sha256"] = s["sha256"]
    if "tarball" in s:
        out["tarball"] = f"{BASE_URL}{s['tarball']}" if s["tarball"].startswith("/") else s["tarball"]
    return out


def sync_agent(agent: dict, plugins: list[dict], skills: list[dict]) -> dict:
    """Merge with refresh: keep entries verbatim when version/sha256 already match
    plugins.json (source of truth); append missing names; refresh entries whose
    version or sha256 differs (version bumps never propagated to agent.json before
    — observed whale-fortune 0.1.0->0.2.0 on 2026-08-27).

    Skills are merged the same way from plugins.json["skills"]. Before v2 the
    skills array was preserved verbatim from the base file, so a skill added to
    plugins.json never reached agent.json — observed whale-plugin-dev (live in
    sitemap + llms.txt Skills (3) + /skills/ tarball 200) missing from
    agent.json skills (2) on 2026-08-28."""
    out = dict(agent)  # shallow copy, plugins replaced below
    existing = {p["name"]: p for p in out["plugins"]}
    merged = []
    refreshed = 0
    for p in plugins:  # plugins.json order is authoritative
        cur = existing.get(p["name"])
        if cur is None:
            merged.append(transform_plugin(p))
        elif cur.get("version") != p["version"] or cur.get("sha256") != p["sha256"]:
            refreshed += 1
            merged.append(transform_plugin(p))
        else:
            merged.append(cur)  # verbatim
    out["plugins"] = merged
    if refreshed:
        print(f"  [agent] refreshed {refreshed} stale entries from plugins.json (version/sha256 changed)")
    if skills:
        existing_sk = {s["name"]: s for s in out.get("skills", [])}
        merged_sk = []
        added_sk = []
        for s in skills:  # plugins.json skills order is authoritative
            cur = existing_sk.get(s["name"])
            if cur is None:
                merged_sk.append(transform_skill(s))
                added_sk.append(s["name"])
            elif cur.get("version") != s["version"] or cur.get("sha256") != s.get("sha256"):
                merged_sk.append(transform_skill(s))
            else:
                merged_sk.append(cur)  # verbatim
        if added_sk:
            print(f"  [agent] skills: added {len(added_sk)} missing from plugins.json ({', '.join(added_sk)})")
        out["skills"] = merged_sk
    out["generated_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return out


def rank_section(llms: str) -> str:
    try:
        rk = json.loads(pathlib.Path("/srv/whaleharness/rankings.json").read_text())
        top = rk.get("consensus", [])[:5]
        if not top:
            return llms
        lines = ["## 生态共识榜 (community consensus x verified, refreshed every 6h)", ""]
        for i, e in enumerate(top, 1):
            lines.append(f"- {i}. {e['name']} — consensus {e['rec_score']}, {e['rec_sources']} sources; verified (audit + whitebox). Full data: /rankings.json")
        lines.append("")
        sep = chr(10)
        return llms + sep * 2 + sep.join(lines)
    except Exception:
        return llms

def sync_llms(llms: str, plugins: list[dict]) -> str:
    sec_re = re.compile(r"(## Plugins \(\d+\)\n)(.*?)(\n## )", re.S)
    m = sec_re.search(llms)
    if not m:
        raise SystemExit("llms.txt: no '## Plugins (N)' section found")
    # collect curated lines from the base section
    curated = {}
    for line in m.group(2).strip().splitlines():
        lm = re.match(r"^- ([a-z0-9-]+) — (.*)$", line.strip())
        if lm:
            curated[lm.group(1)] = line.strip()
    lines = []
    for p in plugins:
        name = p["name"]
        if name in curated:
            lines.append(curated[name])
            continue
        desc = p.get("description_en", "").rstrip(".")
        line = f"- {name} — {desc}."
        ov = LLMS_OVERRIDES.get(name)
        if ov:
            line += f" {ov}."
        lines.append(line)
        print(f"  [llms] appended curated default for {name}")
    # keep any trailing block of the section (e.g. "Install form (verified):")
    rest = m.group(2).split("## Skills")[0]
    trail_lines = [ln for ln in rest.strip("\n").splitlines()
                   if ln.strip() and not re.match(r"^- [a-z0-9-]+ —", ln.strip())]
    trail = ("\n\n" + "\n".join(trail_lines)) if trail_lines else ""
    new_sec = f"## Plugins ({len(plugins)})\n" + "\n".join(lines) + trail + "\n"
    return llms[: m.start(1)] + new_sec + llms[m.end(2):]


def sync_sitemap(sitemap: str, plugins: list[dict]) -> str:
    page_urls = []
    for u in re.findall(r"<loc>([^<]+)</loc>", sitemap):
        if "/plugins/" in u or "/skills/" in u:
            continue
        if u not in page_urls:
            page_urls.append(u)
    tarball_urls = [f"{BASE_URL}{p['tarball']}" for p in plugins]
    skill_urls = [f"{BASE_URL}{s[1]}" for s in SKILLS]
    urls = page_urls + tarball_urls + skill_urls
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="work", help="dir with current agent.json/llms.txt/sitemap.xml/plugins.json")
    ap.add_argument("--out", default=".", help="dir to write regenerated files")
    args = ap.parse_args()
    base, out = pathlib.Path(args.base), pathlib.Path(args.out)
    pj = json.loads((base / "plugins.json").read_text())
    plugins = pj["plugins"]
    skills = pj.get("skills", [])
    agent = json.loads((base / "agent.json").read_text())
    llms = (base / "llms.txt").read_text()
    sitemap = (base / "sitemap.xml").read_text()
    print(f"plugins.json: {len(plugins)} plugins, {len(skills)} skills")
    out.mkdir(parents=True, exist_ok=True)
    a = sync_agent(agent, plugins, skills)
    (out / "agent.json").write_text(json.dumps(a, ensure_ascii=False, indent=1) + "\n")
    (out / "llms.txt").write_text(rank_section(sync_llms(llms, plugins)))
    (out / "sitemap.xml").write_text(sync_sitemap(sitemap, plugins))
    # sanity summary
    n_sitemap = len(re.findall(r"<loc>", (out / "sitemap.xml").read_text()))
    n_llms = len(re.findall(r"^- [a-z0-9-]+ —", (out / "llms.txt").read_text(), re.M))
    print(f"agent.json plugins: {len(a['plugins'])}  skills: {len(a.get('skills', []))}  generated_at: {a['generated_at']}")
    print(f"llms.txt header: ## Plugins ({n_llms})")
    print(f"sitemap.xml URLs: {n_sitemap} (pages {len(page_urls := re.findall(r'<loc>([^<]+)</loc>', (out / 'sitemap.xml').read_text()))})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
