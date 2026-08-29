#!/usr/bin/env python3
"""WhaleHarness submission reviewer: structure, deps, and danger-pattern checks.

Usage: python3 review-submission.py <tarball> [--manifest dist/plugins.json]
Implements the automated parts of docs/REVIEW.md. Manual steps (boot,
headless end-to-end) stay manual.

退出码契约(机器契约——发布管道停门依赖此,勿改语义):
  exit 0 = 放行: verdict 为 PROCEED TO MANUAL STEPS 或 EXCLUDED(官方 repo)
  exit 1 = 阻塞: verdict 为 RED-LINE 或 FORMAT-ISSUE
  exit 2 = 用法错误(缺 tarball 参数)
verdict 文本是给人看的,退出码是机器契约:改 verdict 措辞不得改退出码语义。
deploy/publish_plugin.sh 与 deploy/publish_curated.sh 以「审查器退出码非零即中止」
消费本契约;契约变更必须同步跑 tests/reviewer-regression/run_regression.py 全绿。
"""
import json
import re
import sys
import tarfile
from pathlib import Path

# Network sinks: APIs that actually issue an outbound request. A URL literal alone is
# NOT a red line (READMEs, docs, and API constants are legal); only tainted data
# flowing into one of these sinks is a dynamic-exfiltration signal.
NETWORK_SINK = re.compile(r"\bfetch\s*\(|\b(?:http|https)\.(?:request|get)\s*\(|\bXMLHttpRequest\b")

DANGER = [
    # subprocess is handled per-file below (host-capability gate + call-shape),
    # not as a flat global pattern, so it is intentionally absent from this list.
    # path-aware: .credentials as a FILESYSTEM path only; ctx.credentials member
    # calls on the official dsh-credentials service are legitimate (see
    # Anionex/dsh-vision-toolkit appeal, 2026-08-15: reviewer regex had a
    # false positive on ctx.credentials.resolve/describe/set).
    # 防: 读本机凭据外传。误伤面: 官方服务成员调用 + README/文档里的路径字面量(非代码读取)。
    (re.compile(r"(?:^|[\s\"'/\\\\])[^\w]*\.credentials\b|authorized_keys|(?:[/\\~]id_rsa\b|id_rsa\.[a-zA-Z0-9]+\b)|\b\.ssh\b"), "sensitive path"),
]
# eval 独立检测(上下文区分, 见 strip_strings/strip_declare): 防 declare function 类型声明
# 与文档/字符串里 mention eval 的误报; 真 eval 调用仍红。
EVAL_CALL = re.compile(r"\beval\s*\(")
# RegExp.prototype.exec is a normal JS API — flag it as a warning, not a red line.
RE_EXEC = re.compile(r"\.exec\(")
# --- host exemption list ---
# Hosts that are never treated as "foreign": document identifiers, the platform's own
# surfaces, and local/internal loopback. Only a non-exempt destination can make a
# network sink an exfiltration red line. A URL literal alone is never a red line.
EXEMPT_HOST_SUFFIXES = (
    "w3.org",            # XML namespace URLs (SVG/MathML/XHTML) — identifiers, not requests
    "deepseek.com",      # official DeepSeek API surface (api.deepseek.com and subdomains)
    "whaleharness.com",  # this site
    "whaleharness.store",
)
EXEMPT_HOST_EXACT = {
    "dsh.internal",      # DSH in-process loopback service
    "dsh.local",         # DSH local loopback service
    "localhost",
    "127.0.0.1",
}
URL_RE = re.compile(r"https?://[A-Za-z0-9./_?=&:%#+~-]+")

# EXCLUDED now trusts only the --repo slug (under the official deepseek-ai GitHub
# org). A package self-declaring a @deepseek-ai/* name is no longer exempt
# (squatting guard): it can at most earn a manual-confirm warning. No --repo =>
# no exemption (fail closed).
OFFICIAL_REPO_PREFIX = "deepseek-ai/"

# --- host-capability gate + call-shape heuristic (subprocess red line) ---
# A plugin that declares it runs on the host (dsh.runtime includes "host") may
# legitimately spawn child processes; without that declaration, any subprocess
# usage is a red line. Even with the declaration, only fixed-argv spawn-style
# calls downgrade to a manual-review warning — shell-string exec(..), shell:true,
# bash/sh -c, and dynamically-built command strings stay red lines.
# 防: 工具路径(模型可达)任意命令执行 / shell 注入。误伤面: 声明 host 但脚本漏读 dsh.runtime;
#     client UI 路径用子进程另走人工审;固定 argv 常量拼接可能误判。
SUBPROCESS_IMPORT = re.compile(
    r"node:child_process|require\(['\"]child_process['\"]\)|from\s+['\"]child_process['\"]"
)
SUBPROCESS_CALL = re.compile(r"\b(?:execFile(?:Sync)?|spawn(?:Sync)?)\s*\(|(?<![\w.])fork\s*\(")
SHELL_EXEC = re.compile(r"(?<![\w.])exec(?:Sync)?\s*\(")  # bare exec/execSync = shell string
SHELL_FLAG = re.compile(r"shell\s*:\s*true")
SHELL_C = re.compile(r"\b(?:bash|zsh|sh|fish|dash|ksh)\s+-c\b|['\"]-c['\"]")
INTERP_CMD = re.compile(
    r"\b(?:exec(?:File)?(?:Sync)?|spawn(?:Sync)?|fork)\s*\(\s*(?:`[^`]*\$\{|['\"][^'\"]*['\"]\s*\+)"
)

# --- dynamic network exfiltration (red line) ---
# A network sink is only a red line when tainted data flows into it AND the destination
# host is not exempt. Taint: sensitive reads (process.env, ~/.dsh, .credentials, ssh
# keys) and child_process output (stdout/stderr or a variable assigned from a
# exec/spawn/... call). Coarse same-file heuristic, not dataflow.
# 防: 敏感数据/子进程输出经网络外传。误伤面: URL 字面量本身不判;process.env→官方 API/
#     豁免主机不判;同文件变量重名粗判可能误关联。
SENSITIVE_SOURCE = re.compile(
    r"process\.env\b"
    r"|(?:^|[\s\"'/\\])[^\w]*\.(?:dsh|credentials|ssh)\b"
    r"|authorized_keys\b"
    r"|id_rsa\b"
)
CHILD_CALL = re.compile(r"\b(?:exec|execSync|spawn|spawnSync|execFile|execFileSync|fork)\s*\(")
ASSIGN = re.compile(r"\b(?:const|let|var)\s+(\w+)\s*=\s*([^\n;]+)")


def is_official_repo(repo):
    """True only when --repo is a slug under the official deepseek-ai GitHub org."""
    return bool(repo) and repo.startswith(OFFICIAL_REPO_PREFIX)


def declares_host_runtime(pkg):
    """True when package.json declares dsh.runtime (string or list) including 'host'."""
    if not isinstance(pkg, dict):
        return False
    dsh = pkg.get("dsh")
    if not isinstance(dsh, dict):
        return False
    runtime = dsh.get("runtime")
    if isinstance(runtime, str):
        return runtime == "host"
    if isinstance(runtime, list):
        return "host" in runtime
    return False


def _url_host(url):
    """Bare host of a URL literal (port stripped), or None."""
    m = re.match(r"https?://([^/?#]+)", url)
    if not m:
        return None
    return m.group(1).lower().rstrip(".").split(":", 1)[0]


def is_exempt_host(host):
    """True when host is an exempt host or a subdomain of an exempt suffix."""
    host = (host or "").lower().rstrip(".")
    if host in EXEMPT_HOST_EXACT:
        return True
    return any(host == s or host.endswith("." + s) for s in EXEMPT_HOST_SUFFIXES)


def _dynamic_exfil_reasons(src):
    """Red-line reasons for dynamic network exfiltration in one file (comment-stripped).

    Coarse same-file heuristic, not dataflow: taint variable names assigned from a
    sensitive source (process.env, ~/.dsh, .credentials, ssh keys) or a child_process
    call, then flag any network sink whose call window references a tainted name (or a
    sensitive source directly) and whose destination host is not exempt.
    """
    tainted = set()
    for m in ASSIGN.finditer(src):
        name, rhs = m.group(1), m.group(2)
        if SENSITIVE_SOURCE.search(rhs) or CHILD_CALL.search(rhs):
            tainted.add(name)
    if CHILD_CALL.search(src):
        tainted.update({"stdout", "stderr"})

    reasons = []
    for sm in NETWORK_SINK.finditer(src):
        window = src[sm.start(): sm.start() + 600]
        first = URL_RE.search(window)
        host = _url_host(first.group(0)) if first else None
        if host is not None and is_exempt_host(host):
            continue
        lineno = _line_no(src, sm.start())
        if any(re.search(r"\b" + re.escape(name) + r"\b", window) for name in tainted):
            reasons.append(("sensitive/child_process data passed to a network sink", lineno, host))
        elif SENSITIVE_SOURCE.search(window):
            reasons.append(("sensitive source read into a network sink", lineno, host))
    return reasons


def strip_comments(src):
    """Strip // and /* */ comments without eating http(s):// inside URL literals.

    /* */ comments are replaced with an equal number of newlines so line numbers in
    the stripped source stay aligned with the original file (red-line issues cite
    line numbers).
    """
    src = re.sub(r"(?<!:)//[^\n]*", "", src)
    src = re.sub(r"/\*[\s\S]*?\*/", lambda m: "\n" * m.group(0).count("\n"), src)
    return src


def strip_strings(src):
    """Strip string/template literals (keep line numbers).

    Documents, markdown tables, and error messages mention eval() without calling it;
    a bare substring match would red-line those. True eval() calls live outside string
    literals, so stripping literals loses no real call. Escaped quotes inside literals
    are not handled (rare in docs), and eval inside template interpolation is also
    stripped and missed — both accepted tradeoffs.
    """
    def _blank(m):
        return "\n" * m.group(0).count("\n")
    src = re.sub(r"'(?:\\.|[^'\\\n])*'", _blank, src)
    src = re.sub(r'"(?:\\.|[^"\\\n])*"', _blank, src)
    src = re.sub(r"\x60(?:\\.|[^\x60\\])*\x60", _blank, src)
    return src


def strip_declare(src):
    """Strip TypeScript declare function/var/const/let ... ; signatures (keep line numbers).

    Bundled .d.ts / generated worker code declares globals like
    "declare function eval(x: string): any;" — a type declaration, not a call.
    Declarations run to the terminating ';' (their signatures contain no ';'), so
    this removal is safe and also handles multi-line declarations.
    """
    return re.sub(
        r"\bdeclare\s+(?:function|var|const|let|class|namespace|interface|type|enum)\b[^;]*;",
        lambda m: "\n" * m.group(0).count("\n"),
        src,
    )


def _line_no(src, pos):
    """1-based line number of a character offset in src."""
    return src.count("\n", 0, pos) + 1


def _evidence(src, m, width=60):
    """Single-line trimmed snippet of the line a regex match falls on (for issues)."""
    start = src.rfind("\n", 0, m.start()) + 1
    end = src.find("\n", m.start())
    if end == -1:
        end = len(src)
    return src[start:end].strip()[:width]


def check(tarball: str, manifest_path=None, repo=None) -> int:
    red_lines = []
    format_issues = []
    warnings = []
    with tarfile.open(tarball, "r:gz") as tf:
        names = tf.getnames()
        if not any(n.startswith("package/") for n in names):
            format_issues.append("tarball lacks npm-style package/ prefix")
        try:
            pkg = json.loads(tf.extractfile(next(n for n in names if n == "package/package.json")).read())
        except (StopIteration, KeyError, json.JSONDecodeError) as e:
            format_issues.append(f"package.json missing or invalid: {e}")
            pkg = None
        patch = None
        try:
            patch = tf.extractfile(next(n for n in names if n == "package/cordis.patch.yml")).read().decode()
        except StopIteration:
            format_issues.append("cordis.patch.yml missing")
        # exclude macOS AppleDouble metadata (._*) that tar adds without COPYFILE_DISABLE
        names = [n for n in names if "/._" not in n and not n.startswith("._")]
        srcs = {}
        vendor_srcs = {}
        for n in names:
            is_root_js = n.count("/") == 1 and n.endswith(".js")
            # 扫 lib/ 与 dist/(billion-context-dsh 盲区:代码全在 dist/,不扫则静态红线落空)
            is_pkg_src = (
                (n.startswith("package/lib/") or n.startswith("package/dist/"))
                and (n.endswith(".js") or n.endswith(".mjs") or n.endswith(".ts"))
            )
            if is_pkg_src or is_root_js:
                if "/assets/" in n or n.startswith("package/lib/assets/") or n.startswith("package/dist/assets/"):
                    vendor_srcs[n] = tf.extractfile(n).read().decode(errors="ignore")
                else:
                    srcs[n] = tf.extractfile(n).read().decode(errors="ignore")

    pkg_name = pkg.get("name", "") if pkg is not None else ""
    if is_official_repo(repo):
        print(f"reviewed: {tarball}")
        print(f"name: {pkg_name} (official deepseek repo - exempt)")
        print("verdict: EXCLUDED (official repo, not reviewed)")
        return 0

    if pkg is not None:
        name = pkg.get("name", "")
        ver = pkg.get("version", "")
        ok_name = bool(re.match(r"^[a-z][a-z0-9-]*$", name or "")) or bool(re.match(r"^@[a-z0-9-]+/[a-z][a-z0-9-]*$", name or ""))
        if not ok_name:
            format_issues.append(f"bad package name: {name!r}")
        if name.startswith("@deepseek-ai/"):
            warnings.append(f"package name {name} claims the @deepseek-ai/ scope but repo is not official (manual confirm)")
        # 版本口径(2026-08-18 拍板): semver——可选 v 前缀 + 可选 prerelease + 可选 build metadata。
        # DSH 生态官方即 prerelease(deepseek-harness 0.1.0-rc.5, dsh_compat ^0.1.0-rc.6),
        # 拒绝 prerelease 会误拒合法插件; v 前缀(如 v1.0.0)按同版本判定, 存储保持原值不 rewrite。
        if not re.match(r"^v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$", ver or ""):
            format_issues.append(f"bad version: {ver!r}")
        dsh = pkg.get("dsh") or {}
        bundle = dsh.get("bundle") or {}
        if bundle.get("patch") != "./cordis.patch.yml":
            format_issues.append("dsh.bundle.patch must be ./cordis.patch.yml")
        peers = pkg.get("peerDependencies") or {}
        for dep in peers:
            if not dep.startswith("@deepseek-ai/"):
                warnings.append(f"non-official peer dependency: {dep} (manual review)")
        if manifest_path:
            try:
                manifest = json.loads(Path(manifest_path).read_text())
                existing = {p["name"] for p in manifest["plugins"]}
                if name in existing:
                    warnings.append(f"name {name} already in the store (hint: duplicate)")
            except (OSError, json.JSONDecodeError):
                pass

    if patch is not None:
        # rule: every loaded package name must be the package's own name;
        # the row id is an arbitrary bundle id and may differ (legal cordis)
        loaded = re.findall(r"^\s*name:\s*['\"]?([^'\"]+?)['\"]?\s*$", patch, re.M)
        if pkg:
            pname = pkg.get("name")
            deps = set((pkg.get("dependencies") or {}).keys())
            # rule v2 (2026-08-29): a bundle patch may reference its own name OR
            # any package declared in dependencies (official DSH aggregation bundles);
            # undeclared foreign loads stay FORMAT-ISSUE (security boundary kept).
            for nm in loaded:
                if nm != pname and nm not in deps:
                    format_issues.append(f"patch loads undeclared foreign package {nm!r}")
            if pname not in loaded and not any(nm in deps for nm in loaded):
                warnings.append("patch does not reference its own name or any declared dependency")

    all_src = "\n".join(srcs.values())
    if vendor_srcs:
        warnings.append(f"vendored library files ({len(vendor_srcs)} files, {sum(len(v) for v in vendor_srcs.values()) // 1024} KB): manually review — not red-line scanned")

    # DSH schema DSL: required present-but-false kills the boot
    if re.search(r"required\s*:\s*false", all_src):
        format_issues.append("parameter schema uses required: false - DSH rejects it at boot (omit the key for optional params)")
    # NOTE (2026-08-15, subagent-verified against @deepseek-ai/dsh-tools@0.1.0-rc.6):
    # in the author DSL, required: true on a leaf property IS the correct and only supported
    # form (the defineTool compiler collects it into a top-level array); a top-level
    # required: [...] array in source is REJECTED by the DSL. So no rule fires on required: true.
    # required: false is genuinely boot-fatal on both paths - keep the rule above.

    # strip comments, then scan danger patterns per-file (comments must not trigger);
    # record file + line + evidence so authors can reproduce each finding.
    commentless = strip_comments(all_src)
    for path, src in srcs.items():
        fsrc = strip_comments(src)
        for pattern, label in DANGER:
            for m in pattern.finditer(fsrc):
                red_lines.append(f"{label}: {path}:L{_line_no(fsrc, m.start())}: {_evidence(fsrc, m)}")
        # eval: 剥注释+字符串+declare 声明后只剩真调用; 文档/类型声明里的 eval 字样被跳过
        fsrc_eval = strip_declare(strip_strings(fsrc))
        for m in EVAL_CALL.finditer(fsrc_eval):
            red_lines.append(f"eval: {path}:L{_line_no(fsrc_eval, m.start())}: {_evidence(fsrc_eval, m)}")

    # dynamic network exfiltration: per-file, tainted data -> non-exempt sink
    for path, src in srcs.items():
        for reason, lineno, host in _dynamic_exfil_reasons(strip_comments(src)):
            target = f" 外传目标: {host}" if host else ""
            red_lines.append(f"network exfiltration ({reason}): {path}:L{lineno}{target}")

    # subprocess red line: per-file, gated on the host-capability declaration,
    # with a call-shape heuristic (fixed argv vs shell-string/dynamic command).
    host_declared = declares_host_runtime(pkg)
    host_subprocess_files = []
    for path, src in srcs.items():
        fsrc = strip_comments(src)
        if not (SUBPROCESS_IMPORT.search(fsrc) or SUBPROCESS_CALL.search(fsrc)):
            continue
        call_m = (SHELL_EXEC.search(fsrc) or SUBPROCESS_CALL.search(fsrc)
                  or SUBPROCESS_IMPORT.search(fsrc))
        loc = f":L{_line_no(fsrc, call_m.start())}: {_evidence(fsrc, call_m)}"
        suspicious = bool(SHELL_EXEC.search(fsrc) or SHELL_FLAG.search(fsrc)
                          or SHELL_C.search(fsrc) or INTERP_CMD.search(fsrc))
        if not host_declared:
            red_lines.append(f"subprocess usage without dsh.runtime:host declaration: {path}{loc}")
        elif suspicious:
            red_lines.append(f"subprocess shell-string/dynamic command: {path}{loc}")
        else:
            host_subprocess_files.append(path)
    if host_subprocess_files:
        warnings.append(
            f"host plugin child processes ({len(host_subprocess_files)} file(s)): manual review - "
            + ", ".join(host_subprocess_files[:3])
        )

    rex = RE_EXEC.findall(commentless)
    if rex:
        warnings.append(f"RegExp .exec() calls: {len(rex)} (normal JS API, no action)")

    # foreign URL literals anywhere in code (excluding comments) — a warning, not a red line
    url_literals = URL_RE.findall(commentless)
    foreign_lits = sorted(set(u for u in url_literals if not is_exempt_host(_url_host(u))))
    if foreign_lits:
        warnings.append("foreign URL literals in source: " + ", ".join(foreign_lits[:3]))

    print(f"reviewed: {tarball}")
    print(f"name: {pkg.get('name') if pkg else '?'} version: {pkg.get('version') if pkg else '?'}")
    print(f"files: {len(names)}")
    if red_lines or format_issues:
        print("\nISSUES (blocking):")
        for i in red_lines:
            print("  x red-line:", i)
        for i in format_issues:
            print("  x format:", i)
    else:
        print("\nISSUES: none - structure passes")
    if warnings:
        print("\nWARNINGS (manual review):")
        for w in warnings:
            print("  -", w)
    if red_lines:
        verdict = "RED-LINE"
    elif format_issues:
        verdict = "FORMAT-ISSUE"
    else:
        verdict = "PROCEED TO MANUAL STEPS (boot + headless)"
    print("\nverdict:", verdict)
    return 1 if (red_lines or format_issues) else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    manifest = None
    repo = None
    if "--manifest" in args:
        idx = args.index("--manifest")
        manifest = args[idx + 1]
        args = args[:idx] + args[idx + 2:]
    if "--repo" in args:
        idx = args.index("--repo")
        repo = args[idx + 1]
        args = args[:idx] + args[idx + 2:]
    if not args:
        print(__doc__)
        sys.exit(2)
    sys.exit(check(args[0], manifest, repo))
