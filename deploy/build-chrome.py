#!/usr/bin/env python3
"""build-chrome.py — 全站共享 header/footer/nav/lang 单源机制 (round17, 派单 05:45Z).

为什么存在 (blameless root cause):
  首页二轮修验收要求「store.html/submit.html 等子页 nav 与首页一致」且
  「改 header 一处, 重跑后全站生效」。此前 16 个页面各自手写 header/nav/footer,
  语言切换按钮只有样式没有事件绑定 (点了没反应), 子页 nav 是 13 项旧导航。
  本脚本把整站 chrome (header/nav/lang/footer) 收敛为下方常量; 想改全站导航,
  只改 CHROME 常量再跑一次本脚本即可 — 一处改, 全站生效, 无后端。

用法:
  python3 build-chrome.py [站点目录]     # 默认 ./site; 对目录内所有 *.html 就地重写
幂等: 重复运行结果一致 (先剥离旧 chrome 块再重建)。

不碰的内容: 每页 <main> 正文、<head> 原有 meta/style(除注入的 chrome 块)、JSON/XML/txt。
"""
import re
import sys
import pathlib

# ---------------------------------------------------------------------------
# CHROME 单源 (改这里, 重跑, 全站生效)
# ---------------------------------------------------------------------------

# nav 5 项: (href, i18n key, zh 默认文案)
NAV = [
    ("/store.html", "nav-store", "货架"),
    ("/submit.html", "nav-submit", "投稿"),
    ("/audit.html", "nav-audit", "审计"),
    ("/build-log.html", "nav-log", "日志"),
    ("/stats.html", "nav-stats", "数据"),
]
# 每页 active 状态: 页面文件名 -> nav href
ACTIVE = {
    "index.html": "", "store.html": "/store.html", "audit.html": "/audit.html",
    "submit.html": "/submit.html", "submissions.html": "/submit.html",
    "build-log.html": "/build-log.html", "stats.html": "/stats.html",
    "audit-fixes.html": "/audit.html",
}
# footer 三小组 + 给 agent 的 + GitHub 底行 (设计鲸新 footer 结构, round32 派单 15:30Z)
FOOTER_AGENTS = [
    ("/plugins.json", "plugins.json"), ("/agent.json", "agent.json"),
    ("/llms.txt", "llms.txt"), ("/categories.json", "categories.json"),
    ("/audit.json", "audit.json"), ("/authors.json", "authors.json"),
]
# 三小组: 逛 / 读 / 参与 (href, i18n key 或 "", 默认文案)
FOOTER_BROWSE = [
    ("/store.html", "f-store", "货架"), ("/audit.html", "f-audit", "审计"),
    ("/submit.html", "f-submit", "投稿"), ("/stats.html", "f-stats", "数据"),
]
FOOTER_READ = [
    ("/blog.html", "", "Blog"), ("/deep-dive.html", "", "Deep Dive"),
    ("/zero-trust.html", "", "Zero Trust"), ("/build-log.html", "f-buildlog", "构建日志"),
]
FOOTER_JOIN = [
    ("/submissions.html", "f-submissions", "投稿箱"), ("/feedback.html", "f-feedback", "吐槽"),
    ("/open-letter.html", "f-openletter", "公开信"),
]

CHROME_CSS = """<style id="wh-chrome-css">
/* ==== shared chrome (build-chrome.py single source; id-scoped to win over page CSS) ==== */
header#wh-chrome{display:flex;align-items:center;gap:24px;padding:24px 0 0;flex-wrap:wrap;text-align:left;background:none;border:none;margin:0}
header#wh-chrome .brand{font-size:18px;font-weight:700;letter-spacing:.01em;color:#E8EFF7}
header#wh-chrome .brand .whale{margin-right:6px}
header#wh-chrome .brand a{color:#E8EFF7;text-decoration:none}
header#wh-chrome .brand a:hover{text-decoration:none;color:#E8EFF7}
nav#wh-nav{display:flex;gap:4px;flex-wrap:wrap;text-align:left;margin:0}
nav#wh-nav a{color:#9DB2C8;font-size:15px;font-weight:600;padding:10px 14px;border-radius:8px;min-height:44px;display:inline-flex;align-items:center;text-decoration:none;margin:0}
nav#wh-nav a:hover{color:#E8EFF7;background:#122841;text-decoration:none}
nav#wh-nav a.on{color:#4FD1C5}
#wh-lang{margin-left:auto;display:flex;gap:6px}
#wh-lang button{background:none;border:1px solid #1F3A5C;color:#9DB2C8;font:600 13px -apple-system,"PingFang SC","Noto Sans SC",sans-serif;padding:10px 14px;border-radius:8px;cursor:pointer;min-height:44px}
#wh-lang button.on{color:#4FD1C5;border-color:#4FD1C5}
footer#wh-chrome-footer{border-top:1px solid #1F3A5C;padding:40px 0 64px;font-size:13px;color:#6B8198;text-align:left;background:none;margin:0}
footer#wh-chrome-footer .fgrid{display:grid;grid-template-columns:auto 1fr;gap:40px}
footer#wh-chrome-footer .fg h4{font-size:12px;letter-spacing:.08em;color:#6B8198;margin:0 0 10px;text-transform:uppercase}
footer#wh-chrome-footer .fg .links{display:flex;flex-wrap:wrap;gap:6px 16px}
footer#wh-chrome-footer .fg .links a{color:#9DB2C8;text-decoration:none}
footer#wh-chrome-footer .fg .links a:hover{color:#4FD1C5;text-decoration:underline}
footer#wh-chrome-footer .fg-cols{display:grid;grid-template-columns:repeat(3,auto);gap:32px;justify-content:start}
footer#wh-chrome-footer .fg-col{display:flex;flex-direction:column;gap:10px}
footer#wh-chrome-footer .fg-col-h{font-size:11px;font-weight:600;letter-spacing:.08em;color:#6B8198;text-transform:uppercase}
footer#wh-chrome-footer .fg-col .links{display:flex;flex-direction:column;gap:6px}
footer#wh-chrome-footer .fg-col .links a{color:#9DB2C8;text-decoration:none}
footer#wh-chrome-footer .fg-col .links a:hover{color:#4FD1C5;text-decoration:underline}
footer#wh-chrome-footer .tagline{margin-top:28px}
footer#wh-chrome-footer .gh{display:inline-block;margin-top:10px;font-size:13px;font-weight:600;color:#9DB2C8}
footer#wh-chrome-footer .gh:hover{color:#4FD1C5;text-decoration:underline}
.wh-pagehead{text-align:center;padding:24px 0 8px}
@media (max-width:639px){nav#wh-nav{order:3;width:100%}#wh-lang{margin-left:0}footer#wh-chrome-footer .fgrid{grid-template-columns:1fr;gap:28px}footer#wh-chrome-footer .fg-cols{grid-template-columns:repeat(3,1fr);gap:16px}}
</style>"""

# favicon 三态(单源注入各页 head): SVG 现代浏览器 / ICO 兜底 / apple-touch
FAVICON_LINKS = (
    '<link rel="icon" type="image/svg+xml" href="/favicon.svg">\n'
    '<link rel="icon" type="image/x-icon" href="/favicon.ico">\n'
    '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n'
)

# 共享 i18n: 引擎页(index/store/audit)用 Object.assign 并入; 无引擎页用独立引擎
I18N_ZH = {
    "nav-store": "货架", "nav-submit": "投稿", "nav-audit": "审计", "nav-log": "日志", "nav-stats": "数据",
    "nav-home": "首页", "nav-live": "直播间", "nav-press": "推广物料", "nav-box": "投稿箱", "nav-fb": "吐槽",
    "fg-a": "给 agent 的", "fg-h": "给人看的",
    "fg-browse": "逛", "fg-read": "读", "fg-join": "参与",
    "f-store": "货架", "f-audit": "审计", "f-submit": "投稿", "f-stats": "数据",
    "f-buildlog": "构建日志", "f-submissions": "投稿箱", "f-feedback": "吐槽", "f-openletter": "公开信",
    "footer": "让你的鲸鱼武装到牙齿 · 我验你装。",
}
I18N_EN = {
    "nav-store": "Store", "nav-submit": "Submit", "nav-audit": "Audit", "nav-log": "Log", "nav-stats": "Stats",
    "nav-home": "Home", "nav-live": "Live", "nav-press": "Press Kit", "nav-box": "Submissions", "nav-fb": "Feedback",
    "fg-a": "For agents", "fg-h": "For humans",
    "fg-browse": "Browse", "fg-read": "Read", "fg-join": "Contribute",
    "f-store": "Store", "f-audit": "Audit", "f-submit": "Submit", "f-stats": "Stats",
    "f-buildlog": "Build Log", "f-submissions": "Submissions", "f-feedback": "Feedback", "f-openletter": "Open Letter",
    "footer": "Arm your whale to the teeth · We verify, you install.",
}

LANG_MERGE = (
    "<!-- wh-chrome:lang -->\n"
    "Object.assign(I18N.zh, " + repr(I18N_ZH) + ");\n"
    "Object.assign(I18N.en, " + repr(I18N_EN) + ");\n"
    "document.getElementById(\"lang-zh\").addEventListener(\"click\", function(){LANG=\"zh\";applyLang();});\n"
    "document.getElementById(\"lang-en\").addEventListener(\"click\", function(){LANG=\"en\";applyLang();});\n"
    "applyLang();\n"
    "<!-- /wh-chrome:lang -->"
)

STANDALONE_JS = """<script id="wh-chrome-js">
/* shared chrome engine (build-chrome.py single source) */
(function(){
  var I18N={zh:""" + repr(I18N_ZH) + """,en:""" + repr(I18N_EN) + """};
  var LANG=(function(){try{var s=localStorage.getItem("wh-lang")||localStorage.getItem("wh-audit-lang")||localStorage.getItem("wh-blog-lang");if(s==="zh"||s==="en")return s;}catch(e){}return navigator.language.startsWith("zh")?"zh":"en";})();
  function apply(){
    document.documentElement.lang=(LANG==="zh")?"zh-CN":"en";
    var zb=document.getElementById("lang-zh"),eb=document.getElementById("lang-en");
    if(zb)zb.classList.toggle("on",LANG==="zh");
    if(eb)eb.classList.toggle("on",LANG==="en");
    document.querySelectorAll("[data-i18n]").forEach(function(el){
      var k=el.getAttribute("data-i18n");if(k&&I18N[LANG][k]!==undefined)el.textContent=I18N[LANG][k];
    });
    document.querySelectorAll("[data-i18n-ph]").forEach(function(el){
      var k=el.getAttribute("data-i18n-ph");if(k&&I18N[LANG][k]!==undefined)el.placeholder=I18N[LANG][k];
    });
    document.querySelectorAll("[data-lang]").forEach(function(el){
      el.style.display=(el.getAttribute("data-lang")===LANG)?"":"none";
    });
    try{localStorage.setItem("wh-lang",LANG);}catch(e){}
  }
  function bind(){
    var zb=document.getElementById("lang-zh"),eb=document.getElementById("lang-en");
    if(zb)zb.addEventListener("click",function(){LANG="zh";apply();});
    if(eb)eb.addEventListener("click",function(){LANG="en";apply();});
  }
  bind();apply();
})();
</script>"""


def chrome_header(active: str) -> str:
    items = "".join(
        f'      <a href="{href}"{ " class=\"on\"" if href == active else ""} data-i18n="{key}">{zh}</a>\n'
        for href, key, zh in NAV
    )
    return (
        '<header id="wh-chrome">\n'
        '    <div class="brand"><span class="whale">🐋</span><a href="/">WhaleHarness</a></div>\n'
        f'    <nav id="wh-nav">\n{items}    </nav>\n'
        '    <div id="wh-lang"><button id="lang-zh" class="on">中文</button><button id="lang-en">EN</button></div>\n'
        '  </header>'
    )


def chrome_footer() -> str:
    agents = "\n".join(f'        <a href="{h}">{t}</a>' for h, t in FOOTER_AGENTS)

    # 三小组标题: 逛/读/参与 固定, 按组渲染
    browse = "\n".join(f'              <a href="{h}" data-i18n="{k}">{t}</a>' for h, k, t in FOOTER_BROWSE)
    read = "\n".join(f'              <a href="{h}"{ f" data-i18n=\"{k}\"" if k else ""}>{t}</a>' for h, k, t in FOOTER_READ)
    join = "\n".join(f'              <a href="{h}" data-i18n="{k}">{t}</a>' for h, k, t in FOOTER_JOIN)
    return (
        '<footer id="wh-chrome-footer">\n'
        '    <div class="fgrid">\n'
        '      <div class="fg">\n'
        '        <h4 data-i18n="fg-a">给 agent 的</h4>\n'
        f'        <div class="links">\n{agents}\n        </div>\n'
        '      </div>\n'
        '      <div class="fg">\n'
        '        <h4 data-i18n="fg-h">给人看的</h4>\n'
        '        <div class="fg-cols">\n'
        '          <div class="fg-col">\n'
        '            <span class="fg-col-h" data-i18n="fg-browse">逛</span>\n'
        f'            <div class="links">\n{browse}\n            </div>\n'
        '          </div>\n'
        '          <div class="fg-col">\n'
        '            <span class="fg-col-h" data-i18n="fg-read">读</span>\n'
        f'            <div class="links">\n{read}\n            </div>\n'
        '          </div>\n'
        '          <div class="fg-col">\n'
        '            <span class="fg-col-h" data-i18n="fg-join">参与</span>\n'
        f'            <div class="links">\n{join}\n            </div>\n'
        '          </div>\n'
        '        </div>\n'
        '      </div>\n'
        '    </div>\n'
        '    <p class="tagline" data-i18n="footer">让你的鲸鱼武装到牙齿 · 我验你装。</p>\n'
        '    <a class="gh" href="https://github.com/WhaleHarness/WhaleHarness">GitHub ↗</a>\n'
        '  </footer>'
    )


HEADER_RE = re.compile(r"<header\b[^>]*>.*?</header>", re.S)
HEADER_NAV_RE = re.compile(r"<header\b[^>]*>.*?</header>\s*<nav\b[^>]*>.*?</nav>", re.S)
NAV_ONLY_RE = re.compile(r"<nav\b[^>]*>.*?</nav>", re.S)
FOOTER_RE = re.compile(r"<footer\b[^>]*>.*?</footer>", re.S)
CSS_RE = re.compile(r'<style id="wh-chrome-css">.*?</style>', re.S)
JS_RE = re.compile(r'<script id="wh-chrome-js">.*?</script>', re.S)
LANG_MERGE_RE = re.compile(r"<!-- wh-chrome:lang -->.*?<!-- /wh-chrome:lang -->\s*\n?", re.S)
BODY_TAG_RE = re.compile(r"(<body\b[^>]*>)", re.I)


def rebuild(html: str, page: str) -> tuple[str, list[str]]:
    notes = []
    active = ACTIVE.get(page, "")
    head = chrome_header(active)
    foot = chrome_footer()

    # 0) 旧 header 里若有页标题 (h1+tagline), 先抠出来, 替换后作为 wh-pagehead 保留
    title_block = ""
    m0 = HEADER_NAV_RE.search(html) or HEADER_RE.search(html)
    if m0 and "<h1" in m0.group(0):
        inner = m0.group(0)
        inner = re.sub(r"^<header\b[^>]*>", "", inner, flags=re.S)
        inner = re.sub(r"</header>\s*", "", inner, count=1, flags=re.S)
        inner = re.sub(r"<nav\b[^>]*>.*?</nav>\s*$", "", inner, flags=re.S)
        title_block = '\n  <div class="wh-pagehead">' + inner.strip() + "</div>"

    # 1) header(+旧 nav) -> chrome header
    m = HEADER_NAV_RE.search(html)
    if m:
        html = html[: m.start()] + head + title_block + html[m.end():]
        notes.append("header+old-nav replaced" + (" (title preserved)" if title_block else ""))
    else:
        m = HEADER_RE.search(html)
        if m:
            html = html[: m.start()] + head + title_block + html[m.end():]
            notes.append("header replaced" + (" (title preserved)" if title_block else ""))
        else:
            # 无 header 的页面 (open-letter): 去掉旧 nav, 在 <body> 后插 chrome header
            html = NAV_ONLY_RE.sub("", html, count=1)
            bm = BODY_TAG_RE.search(html)
            assert bm, f"{page}: no <body> tag"
            html = html[: bm.end()] + "\n" + head + html[bm.end():]
            notes.append("no header; old nav removed, chrome header inserted after <body>")

    # 2) footer -> chrome footer
    m = FOOTER_RE.search(html)
    if m:
        html = html[: m.start()] + foot + html[m.end():]
        notes.append("footer replaced")
    else:
        html = html.replace("</body>", "\n" + foot + "\n</body>", 1)
        notes.append("no footer; chrome footer inserted")

    # 3) chrome CSS
    html = CSS_RE.sub("", html)
    html = html.replace("</head>", FAVICON_LINKS + CHROME_CSS + "</head>", 1)

    # 4) lang 引擎
    if "function applyLang" in html:
        html = LANG_MERGE_RE.sub("", html)
        # 插到最后一个 </script> 前 (主脚本顶层), 而不是 applyLang(); 前 —
        # store/audit 的 applyLang(); 在 async IIFE 里 (await fetch 之后),
        # 插在那里会导致监听器与渲染依赖 fetch 成功, 失败则按钮全死 (round17 实测 bug)。
        idx = html.rfind("</script>")
        assert idx != -1, f"{page}: no </script>"
        html = html[:idx] + LANG_MERGE + "\n" + html[idx:]
        notes.append("lang listeners+keys merged into page engine (top-level, fetch-independent)")
    else:
        html = JS_RE.sub("", html)
        html = html.replace("</body>", STANDALONE_JS + "</body>", 1)
        notes.append("standalone chrome engine injected")

    return html, notes


def main() -> int:
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("site")
    pages = sorted(root.glob("*.html"))
    if not pages:
        print(f"no *.html in {root}", file=sys.stderr)
        return 1
    for p in pages:
        html = p.read_text()
        out, notes = rebuild(html, p.name)
        if out == html:
            print(f"  {p.name}: NO CHANGE")
            continue
        p.write_text(out)
        print(f"  {p.name}: {'; '.join(notes)}")
    print(f"done: {len(pages)} pages rebuilt in {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
