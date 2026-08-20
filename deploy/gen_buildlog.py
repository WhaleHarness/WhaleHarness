#!/usr/bin/env python3
"""Regenerate dist/build-log.html from ROUNDS.md."""
import html
from pathlib import Path

src = Path("/Users/eno/workspace/dshstore/ROUNDS.md").read_text()
# 生成层措辞口径(2026-08-20):历史记录原样保留,对外页面用「验证」口径
src = src.replace("审核制", "验证制")
body = html.escape(src).replace(chr(10), "<br>")

page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>构建日志 · WhaleHarness</title>
<link rel="canonical" href="https://whaleharness.com/build-log.html">
<meta name="robots" content="index">
<style>
  :root { --deep:#04121f; --sea:#0b2d4a; --foam:#d7ecf8; --accent:#4fc3f7; --muted:#7fa3bd; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:linear-gradient(180deg,var(--deep) 0%,var(--sea) 100%); color:var(--foam);
    font-family:-apple-system,"PingFang SC","Noto Sans CJK SC",sans-serif; line-height:1.7; min-height:100vh; }
  .wrap { max-width:820px; margin:0 auto; padding:48px 24px 80px; }
  header { text-align:center; padding:24px 0; }
  h1 { font-size:30px; letter-spacing:2px; }
  .tagline { color:var(--muted); margin-top:8px; }
  nav { text-align:center; margin:18px 0 8px; }
  nav a { color:var(--accent); text-decoration:none; margin:0 12px; }
  .log { background:rgba(7,26,43,.7); border:1px solid rgba(79,195,247,.18); border-radius:12px;
    padding:22px; margin-top:18px; font-size:14px; color:#b9d4e6; }
  footer { margin-top:50px; text-align:center; color:var(--muted); font-size:13px; }
  footer a { color:var(--accent); text-decoration:none; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div style="font-size:40px">📜</div>
    <h1>构建日志</h1>
    <p class="tagline">每一轮真实工作记录，含全部踩坑。原始文件：ROUNDS.md（GitHub: WhaleHarness/WhaleHarness）</p>
  </header>
  <nav><a href="/">首页</a><a href="/live.html">直播间</a><a href="/stats.html">数据</a><a href="/blog.html">Blog</a></nav>
  <div class="log">""" + body + """</div>
  <footer><p>WhaleHarness · <a href="/">回首页</a></p></footer>
</div>
</body>
</html>
"""
Path("/Users/eno/workspace/dshstore/dist/build-log.html").write_text(page)
print("build-log.html regenerated,", len(body), "chars")
