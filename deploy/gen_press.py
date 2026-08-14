import html, pathlib
md_dir = pathlib.Path("/Users/eno/workspace/dshstore/marketing")
files = ["copy-x.md", "copy-long.md", "invite.md", "copy-b.md", "copy-dm.md", "round2.md"]
sections = []
NL = chr(10)
for f in files:
    p = md_dir / f
    if not p.exists():
        print("skip", f)
        continue
    text = p.read_text()
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else f
    body = NL.join(lines[1:]).strip()
    sections.append("  <section>" + NL + "    <h2>" + html.escape(title) + "</h2>" + NL + "    <div class=\"card\"><pre class=\"txt\">" + html.escape(body) + "</pre></div>" + NL + "  </section>")

head = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>推广物料 · WhaleHarness</title>
<style>
  :root { --deep:#04121f; --sea:#0b2d4a; --foam:#d7ecf8; --accent:#4fc3f7; --muted:#7fa3bd; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:linear-gradient(180deg,var(--deep) 0%,var(--sea) 100%); color:var(--foam);
    font-family:-apple-system,"PingFang SC","Noto Sans CJK SC",sans-serif; line-height:1.7; min-height:100vh; }
  .wrap { max-width:860px; margin:0 auto; padding:48px 24px 80px; }
  header { text-align:center; padding:24px 0; }
  h1 { font-size:34px; letter-spacing:2px; }
  .tagline { color:var(--muted); margin-top:8px; }
  nav { text-align:center; margin:20px 0 8px; }
  nav a { color:var(--accent); text-decoration:none; margin:0 12px; }
  section { margin-top:40px; }
  h2 { font-size:22px; border-bottom:1px solid rgba(79,195,247,.25); padding-bottom:8px; }
  .card { background:rgba(7,26,43,.7); border:1px solid rgba(79,195,247,.18); border-radius:12px;
    padding:20px 22px; margin-top:14px; }
  .txt { font-family:ui-monospace,monospace; font-size:13px; color:#b9d4e6; white-space:pre-wrap; word-break:break-word; }
  .warn { border-left:3px solid var(--accent); background:rgba(79,195,247,.06); padding:12px 16px;
    margin-top:14px; color:var(--muted); font-size:14px; }
  footer { margin-top:60px; text-align:center; color:var(--muted); font-size:13px; }
  footer a { color:var(--accent); text-decoration:none; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div style="font-size:44px">📣</div>
    <h1>推广物料</h1>
    <p class="tagline">鲸群 AGENT 写的稿子，直接复制就能贴。事实全部核对过，不含编造。</p>
  </header>
  <nav><a href="/">首页</a><a href="/live.html">直播间</a><a href="/press.html">推广物料</a><a href="/submit.html">投稿</a></nav>
  <div class="warn">口径：产品名 <b>WhaleHarness</b>；插件叫「鲸群成员」，用户叫「船员」，安装叫「上船」。禁用词：赋能、抓手、闭环、颠覆、卷、yyds。</div>
"""

tail = """
  <footer>
    <p>WhaleHarness · 深海里的插件鲸群 · <a href="/">回首页</a></p>
  </footer>
</div>
</body>
</html>
"""
pathlib.Path("/Users/eno/workspace/dshstore/dist/press.html").write_text(head + NL.join(sections) + tail)
print("press.html written with", len(sections), "sections")
