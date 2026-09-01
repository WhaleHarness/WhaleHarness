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
from urllib.request import Request, urlopen

# keyword -> category (primary, first match wins)
# round29 (dispatch 04:30Z, 2026-08-20): extended from the 43 previously
# unclassified store plugins' real tarball package.json keywords. Every tuple
# below maps at least one live plugin; no invented keywords. New category
# "search" is grounded in 4 real plugins (web-search providers + finder).
KEYWORD_CAT = [
    (("sql", "database", "db", "postgres", "mysql", "sqlite", "query", "db-tools"), "database"),
    (("voice", "语音", "asr", "tts", "speech"), "audio"),
    # round38-4 (workflow): grounded in dsh-evolve-modes 0.3.2 keywords.
    (("agent-review", "plan-mode", "acceptance-review", "self-evolution", "taskboard"), "workflow"),
    # round38-5 (ops): grounded in dsh-better-reasoning-effort 0.3.3 keywords.
    (("reasoning-effort", "llm-settings", "input-modality"), "ops"),


    (("finance", "financial", "trading", "market-data", "stock", "crypto", "finreport", "财经"), "finance"),
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
    # round35 (dispatch 05:10Z, 2026-08-21): fifth batch of 23 new SKUs left
    # 22 unclassified. Every tuple below maps at least one live shipped tarball
    # package.json keyword (evidence extracted from the actual /plugins/*.tgz
    # artifacts, downloaded 2026-08-21T06:3xZ). No invented keywords.
    (("desktop-pet", "桌宠", "kun", "ikun"), "fun"),    # dsh-ikun-pet (also rescues dsh-pet: has codex+desktop-pet)
    (("codex", "provider"), "ops"),                     # dsh-codex-provider: OpenAI Codex provider
    (("deeplink",), "ui"),                              # dsh-session-deeplink: URL ?session= navigation
    (("turn-delete", "side-chat"), "ui"),               # dsh-turn-delete / dsh-side-chat: conversation editing
    (("chinese",), "productivity"),                     # dsh-think-zh: Simplified-Chinese output enforcement
    (("subagents", "orchestration", "failover", "high-availability"), "workflow"),  # dsh-ha-orchestrator
    (("sandbox",), "ops"),                              # dsh-sandbox-escalation-fix
    (("audit", "evidence"), "ops"),                     # qiushi-dsh-evidence-audit
    (("verification", "observability"), "ops"),         # dsh-verification-receipt (execution summaries)
    (("telemetry", "redaction"), "ops"),                # dsh-telemetry-redactor
    (("prompt-template", "model-profile"), "workflow"), # dsh-prompt-profile
    (("skills",), "workflow"),                          # dsh-skills-manager (local/agent skills management)
    # round36 (batch-6 UNCAT backfill): 8 SKUs left unclassified by round35.
    # Every tuple maps at least one live tarball keyword; no invented keywords.
    (("sidechain", "btw"), "ui"),                       # dsh-btw: transient /btw side questions
    (("workbench", "jupyter", "reproducible-research", "bioinformatics"), "productivity"),  # dsh-science-workbench
    (("prompt-optimize",), "productivity"),             # dsh-prompt-optimize
    # round37 (batch-7): 8 SKUs left unclassified by round36 (batch-7 listing).
    # Every tuple maps at least one live tarball keyword; no invented keywords.
    (("chat-outline",), "ui"),                          # dsh-chat-outline
    (("textarea", "resize", "expand"), "ui"),           # dsh-composer-expand
    (("selection", "quote"), "ui"),                     # dsh-selection-ask
    (("lorebook", "world-info", "sillytavern"), "productivity"),  # dsh-lorebookmd
    (("vlm", "multimodal", "image-understanding", "ocr"), "knowledge"),  # dsh-vision-bridge
    # round38 (whale-shot, store dogfooding #1): own headless-screenshot tool.
    (("screenshot", "playwright", "browser"), "productivity"),  # whale-shot
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
    # round35 additions: regexes matching the real package.json descriptions
    # of the keywordless fifth-batch plugins (evidence = shipped tarball
    # description text); placed before the broad tail heuristics.
    (r"workspace file path|instead of model attachments", "workflow"),  # dsh-drop-to-path
    (r"reasoning effort|model routing", "ops"),                         # dsh-reasoning-settings
    (r"agent preset|agent-presets|preset 分发", "workflow"),            # dsh-router-flash
    (r"技能管理器|skill manager|managing local skills|shared Agent skills", "workflow"),  # dsh-skill-manager / dsh-skills-manager
    (r"token consumption|token usage|cost estimate|context pressure|套餐余量|消耗 token", "ops"),  # dsh-token-panel / dsh-ocgo-lite
    (r"简体中文", "productivity"),                                      # dsh-think-zh
    (r"global rules|AGENTS\.md", "workflow"),                           # dsh-global-rules
    (r"streaming reveals|animations|scroll-follow", "ui"),              # dsh-plugin-smooth-stream
    (r"系统提示词|deployment persona|persona", "workflow"),             # dsh-prompt-persona
    (r"sandbox escalation", "ops"),                                     # dsh-sandbox-escalation-fix
    # round36 additions: regexes matching the real tarball descriptions of the
    # keywordless batch-6 plugins (evidence = shipped tarball description
    # text); placed before the broad tail heuristics.
    (r"composer mic|transcription|hold-to-talk", "ui"),   # dsh-client-ui-voice-input
    (r"quick-jump rail|prompt rail", "ui"),               # dsh-prompt-rail
    (r"skin plugin|built-in skins", "ui"),                # dsh-client-ui-skins
    (r"便签", "ui"),                                      # dsh-sticky-notes
    (r"思考强度|推理等级", "ops"),                        # dsh-effort-slider
    # round37 additions: regexes matching the real tarball descriptions of the
    # keywordless batch-7 plugins (evidence = shipped tarball description text);
    # placed before the broad tail heuristics.
    (r"distill|reflection", "productivity"),            # distill
    (r"telegram|bot bridge", "workflow"),               # telegram
    (r"滑动|变祖器", "ui"),                              # dsh-huadong-bianzuqi
    # round38-1 (finance gap): grounded in dsh-finreport 0.1.0 tarball
    # description (Yahoo Finance / CoinGecko / 财经日报).
    (r"财经|finance|financial", "finance"),
    # round38-2 (outline): grounded in whale-outline 0.1.0 tarball description (An offline outline generator).
    # round38-3 (audio): grounded in dsh-voice 0.8.0 tarball description (Full-duplex voice mode / streamed ASR -> LLM -> TTS with barge-in).
    (r"voice|语音|asr|tts|speech", "audio"),
    # round38-4b (taskboard): grounded in dsh-taskboard 0.1.3 description.
    (r"taskboard|任务板", "workflow"),

    (r"outline|大纲", "productivity"),
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
    "audio": {"zh": "音频", "en": "audio"},
    "database": {"zh": "数据库", "en": "database"},
    "finance": {"zh": "金融", "en": "finance"},
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
        # round35: site 403s UA-less clients (observed 2026-08-21); send a
        # browser UA so the generator keeps working unattended.
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (WhaleHarness categories generator)"})
        with urlopen(req, timeout=30) as r:
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
