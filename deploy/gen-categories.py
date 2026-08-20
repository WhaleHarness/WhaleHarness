#!/usr/bin/env python3
"""WhaleHarness categories generator (round14 product-form, dispatch 03:10Z).

Derives a category for every store-listed plugin from the SHIPPED tarball's
package.json keywords (evidence = artifact the user actually installs).
Plugins without keywords fall back to a documented description-keyword
heuristic and are marked as such. No README metadata is invented; plugins
that can't be classified stay "" (empty). Output: categories.json, consumed
by index.html (full-store view) — no hand-written numbers.

Usage: python3 gen-categories.py /srv/whaleharness/plugins.json [tarball-dir]
  tarball-dir: optional cache dir of *.tgz; if absent, downloads from site.
"""
import datetime
import json
import re
import sys
import tarfile
from pathlib import Path
from urllib.request import urlopen

# keyword -> category (primary, first match wins)
# round29 (dispatch 04:30Z, 2026-08-20): extended from the 43 previously
# unclassified store plugins' real tarball package.json keywords. Every tuple
# below maps at least one live plugin; no invented keywords. New category
# "search" is grounded in 4 real plugins (web-search providers + finder).
KEYWORD_CAT = [
    (("web-search", "websearch", "search-provider", "exa-search"), "search"),
    (("search", "discovery"), "search"),
    (("subagent", "delegation"), "workflow"),
    (("browser-automation", "webbridge"), "workflow"),
    (("reverse-engineering", "pentest", "security-research", "ctf"), "ops"),
    (("tmux", "pane-control", "tmux-watch", "terminal"), "ops"),
    (("rollback", "snapshot", "guard"), "ops"),
    (("balance", "quota", "spend", "cost", "pricing", "tokens", "compaction"), "ops"),
    (("model-router", "cost-optimizer", "context-caching", "model", "settings"), "ops"),
    (("hud", "git-status", "mcp", "mcp-server"), "ops"),
    (("cleanup", "delete"), "ops"),
    (("theme", "skin", "wallpaper", "换肤"), "ui"),
    (("web-ui",), "ui"),
    (("conversation", "navigation", "timeline"), "ui"),
    (("web", "badge", "attention", "notification", "desktop-notification"), "ui"),
    (("polish", "rewrite"), "productivity"),
    (("report", "daily-report", "handoff", "deliverable"), "productivity"),
    (("blender", "3d-modeling"), "productivity"),
    (("deep-read", "deep-reading", "reading", "reading-companion", "book", "pdf",
      "study", "knowledge-map", "mindmap", "feynman", "summarization"), "knowledge"),
    (("live2d", "mascot", "cute", "whale-girl"), "fun"),
    (("agent-preset",), "workflow"),
    (("plan-review", "annotation", "plannotator"), "workflow"),
    (("generative-ui", "ui", "render"), "ui"),
    (("knowledge-base", "knowledge"), "knowledge"),
    (("memory", "agent-memory", "storage"), "memory"),
    (("submit", "verify", "review", "workflow"), "workflow"),
    (("status", "monitoring", "checkup", "health"), "ops"),
    (("brand", "copywriting", "copy"), "brand"),
    (("breathe", "mindful", "calm", "wellness"), "wellness"),
    (("digest", "summarizer", "summary", "summarize"), "productivity"),
    (("archive", "archive-tool"), "archive"),
    (("praise", "fortune", "fun", "celebrate"), "fun"),
    (("store", "catalog", "marketplace"), "store"),
]
# description-keyword -> category (only used when keywords are absent)
# round29 additions are regex patterns that match the real package.json
# descriptions of the 10 keywordless unclassified plugins; they are placed
# before the original heuristics and were checked not to re-classify the 9
# keywordless plugins that already carry a category.
DESC_CAT = [
    (r"annotation|批注", "workflow"),
    (r"审计|audit|成本", "ops"),
    (r"deep\.?research|research", "search"),
    (r"learning|学习", "knowledge"),
    (r"循环|loop", "workflow"),
    (r"导航", "ui"),
    (r"acceptance|验证|验收", "workflow"),
    (r"command palette|命令面板|palette", "ui"),
    (r"theme|主题|换肤", "ui"),
    (r"practices|实践", "knowledge"),
    (r"置顶|sticky|pin", "ui"),
    (r"模板|template", "workflow"),
    (r"防护|guard|漂移", "ops"),
    (r"summariz", "productivity"),
    (r"archiv", "archive"),
    (r"memory", "memory"),
    (r"ui\b", "ui"),
]

CATS = {
    "fun": {"zh": "趣味", "en": "fun"},
    "memory": {"zh": "记忆", "en": "memory"},
    "workflow": {"zh": "工作流", "en": "workflow"},
    "ops": {"zh": "运维", "en": "ops"},
    "brand": {"zh": "品牌", "en": "brand"},
    "wellness": {"zh": "健康", "en": "wellness"},
    "productivity": {"zh": "效率", "en": "productivity"},
    "ui": {"zh": "界面", "en": "ui"},
    "knowledge": {"zh": "知识", "en": "knowledge"},
    "archive": {"zh": "存档", "en": "archive"},
    "store": {"zh": "商店", "en": "store"},
    "search": {"zh": "搜索", "en": "search"},
}


def classify(pkg):
    kws = [k.lower() for k in (pkg.get("keywords") or [])]
    for keys, cat in KEYWORD_CAT:
        if any(k in kws for k in keys):
            return cat, "tarball package.json keywords"
    desc = (pkg.get("description") or "")
    for pat, cat in DESC_CAT:
        if re.search(pat, desc, re.I):
            return cat, "heuristic: description keyword"
    return "", "unclassified"


def fetch(name, ver, base, cache):
    fn = f"{name}-{ver}.tgz"
    p = cache / fn
    if not p.exists():
        url = f"{base}/plugins/{fn}"
        with urlopen(url, timeout=30) as r:
            p.write_bytes(r.read())
    return p


def main():
    manifest_path, cache = sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/tgz-cats")
    cache.mkdir(exist_ok=True)
    m = json.load(open(manifest_path))
    base = m.get("baseUrl", "https://whaleharness.com")
    out, seen = {}, set()
    for p in m["plugins"]:
        name, ver = p["name"], p["version"]
        assert name not in seen, f"duplicate plugin {name}"
        seen.add(name)
        tgz = fetch(name, ver, base, cache)
        with tarfile.open(tgz, "r:gz") as tf:
            pkg = json.loads(tf.extractfile("package/package.json").read())
        cat, ev = classify(pkg)
        out[name] = {
            "category": cat,
            "category_zh": CATS[cat]["zh"] if cat else "",
            "category_en": CATS[cat]["en"] if cat else "",
            "keywords": pkg.get("keywords") or [],
            "evidence": ev,
            "version_checked": ver,
            "sha256": p.get("sha256", ""),
        }
    doc = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "category derived from the shipped tarball package.json keywords; "
                  "fallback heuristic from description keywords is labelled; "
                  "unclassifiable plugins stay empty. No fabricated metadata.",
        "categories": CATS,
        "plugins": out,
    }
    print(json.dumps(doc, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
