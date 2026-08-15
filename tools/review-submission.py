#!/usr/bin/env python3
"""WhaleHarness submission reviewer: structure, deps, and danger-pattern checks.

Usage: python3 review-submission.py <tarball> [--manifest dist/plugins.json]
Implements the automated parts of docs/REVIEW.md. Manual steps (boot,
headless end-to-end) stay manual.
"""
import json
import re
import sys
import tarfile
from pathlib import Path

DANGER = [
    (re.compile(r"node:child_process|require\(['\"]child_process['\"]\)|from\s+['\"]child_process['\"]|execFileSync?|spawnSync|\bfork\s*\("), "subprocess usage"),
    (re.compile(r"\beval\s*\("), "eval"),
    (re.compile(r"fetch\s*\(|http\.request|https\.request|XMLHttpRequest"), "network call"),
    # path-aware: .credentials as a FILESYSTEM path only; ctx.credentials member
    # calls on the official dsh-credentials service are legitimate (see
    # Anionex/dsh-vision-toolkit appeal, 2026-08-15: reviewer regex had a
    # false positive on ctx.credentials.resolve/describe/set).
    (re.compile(r"(?:^|[\s\"'/\\\\])[^\w]*\.credentials\b|authorized_keys|id_rsa|\b\.ssh\b"), "sensitive path"),
]
# RegExp.prototype.exec is a normal JS API — flag it as a warning, not a red line.
RE_EXEC = re.compile(r"\.exec\(")
ALLOWED_NET = {"https://whaleharness.com", "https://whaleharness.store"}


def check(tarball: str, manifest_path=None) -> int:
    issues = []
    warnings = []
    with tarfile.open(tarball, "r:gz") as tf:
        names = tf.getnames()
        if not any(n.startswith("package/") for n in names):
            issues.append("tarball lacks npm-style package/ prefix")
        try:
            pkg = json.loads(tf.extractfile(next(n for n in names if n == "package/package.json")).read())
        except (StopIteration, KeyError, json.JSONDecodeError) as e:
            issues.append(f"package.json missing or invalid: {e}")
            pkg = None
        patch = None
        try:
            patch = tf.extractfile(next(n for n in names if n == "package/cordis.patch.yml")).read().decode()
        except StopIteration:
            issues.append("cordis.patch.yml missing")
        # exclude macOS AppleDouble metadata (._*) that tar adds without COPYFILE_DISABLE
        names = [n for n in names if "/._" not in n and not n.startswith("._")]
        srcs = {}
        vendor_srcs = {}
        for n in names:
            is_root_js = n.count("/") == 1 and n.endswith(".js")
            if (n.startswith("package/lib/") and (n.endswith(".js") or n.endswith(".mjs") or n.endswith(".ts"))) or is_root_js:
                if "/assets/" in n or n.startswith("package/lib/assets/"):
                    vendor_srcs[n] = tf.extractfile(n).read().decode(errors="ignore")
                else:
                    srcs[n] = tf.extractfile(n).read().decode(errors="ignore")

    if pkg is not None:
        name = pkg.get("name", "")
        ver = pkg.get("version", "")
        ok_name = bool(re.match(r"^[a-z][a-z0-9-]*$", name or "")) or bool(re.match(r"^@[a-z0-9-]+/[a-z][a-z0-9-]*$", name or ""))
        if not ok_name:
            issues.append(f"bad package name: {name!r}")
        if not re.match(r"^\d+\.\d+\.\d+$", ver or ""):
            issues.append(f"bad version: {ver!r}")
        dsh = pkg.get("dsh") or {}
        bundle = dsh.get("bundle") or {}
        if bundle.get("patch") != "./cordis.patch.yml":
            issues.append("dsh.bundle.patch must be ./cordis.patch.yml")
        peers = pkg.get("peerDependencies") or {}
        for dep in peers:
            if not dep.startswith("@deepseek-ai/"):
                warnings.append(f"non-official peer dependency: {dep} (manual review)")
        if manifest_path:
            try:
                manifest = json.loads(Path(manifest_path).read_text())
                existing = {p["name"] for p in manifest["plugins"]}
                if name in existing:
                    issues.append(f"name {name} already in the store")
            except (OSError, json.JSONDecodeError):
                pass

    if patch is not None:
        # rule: every loaded package name must be the package's own name;
        # the row id is an arbitrary bundle id and may differ (legal cordis)
        loaded = re.findall(r"^\s*name:\s*['\"]?([^'\"]+?)['\"]?\s*$", patch, re.M)
        if pkg:
            pname = pkg.get("name")
            for nm in loaded:
                if nm != pname:
                    issues.append(f"patch loads foreign package {nm!r}")
            if pname not in loaded:
                warnings.append("patch does not load the package's own name")

    all_src = "\n".join(srcs.values())
    if vendor_srcs:
        warnings.append(f"vendored library files ({len(vendor_srcs)} files, {sum(len(v) for v in vendor_srcs.values()) // 1024} KB): manually review — not red-line scanned")

    # DSH schema DSL: required present-but-false kills the boot
    if re.search(r"required\s*:\s*false", all_src):
        issues.append("parameter schema uses required: false - DSH rejects it at boot (omit the key for optional params)")
    # NOTE (2026-08-15, subagent-verified against @deepseek-ai/dsh-tools@0.1.0-rc.6):
    # in the author DSL, required: true on a leaf property IS the correct and only supported
    # form (the defineTool compiler collects it into a top-level array); a top-level
    # required: [...] array in source is REJECTED by the DSL. So no rule fires on required: true.
    # required: false is genuinely boot-fatal on both paths - keep the rule above.

    # strip comments, then scan danger patterns (comments must not trigger)
    commentless = re.sub(r"//[^\n]*", "", all_src)
    commentless = re.sub(r"/\*[\s\S]*?\*/", "", commentless)
    for pattern, label in DANGER:
        hits = pattern.findall(commentless)
        if hits:
            if label == "network call":
                urls = re.findall(r"https?://[A-Za-z0-9./_?=&-]+", commentless)
                foreign = [u for u in urls if not any(u.startswith(a) for a in ALLOWED_NET)]
                if not foreign:
                    continue
                issues.append(f"network calls to foreign hosts: {foreign[:3]}")
            else:
                issues.append(f"{label}: {len(hits)} occurrence(s)")
    rex = RE_EXEC.findall(commentless)
    if rex:
        warnings.append(f"RegExp .exec() calls: {len(rex)} (normal JS API, no action)")

    # foreign URL literals anywhere in code (excluding comments)
    url_literals = re.findall(r"https?://[A-Za-z0-9./_?=&-]+", commentless)
    foreign_lits = sorted(set(u for u in url_literals if not any(u.startswith(a) for a in ALLOWED_NET)))
    if foreign_lits:
        warnings.append("foreign URL literals in source: " + ", ".join(foreign_lits[:3]))

    print(f"reviewed: {tarball}")
    print(f"name: {pkg.get('name') if pkg else '?'} version: {pkg.get('version') if pkg else '?'}")
    print(f"files: {len(names)}")
    if issues:
        print("\nISSUES (blocking):")
        for i in issues:
            print("  x", i)
    else:
        print("\nISSUES: none - structure passes")
    if warnings:
        print("\nWARNINGS (manual review):")
        for w in warnings:
            print("  -", w)
    print("\nverdict:", "REJECT" if issues else "PROCEED TO MANUAL STEPS (boot + headless)")
    return 1 if issues else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    manifest = None
    if "--manifest" in args:
        idx = args.index("--manifest")
        manifest = args[idx + 1]
        args = args[:idx] + args[idx + 2:]
    if not args:
        print(__doc__)
        sys.exit(2)
    sys.exit(check(args[0], manifest))
