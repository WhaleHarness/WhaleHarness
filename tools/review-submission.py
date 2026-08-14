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
    (re.compile(r"child_process|execFile|spawnSync|\.exec\("), "subprocess usage"),
    (re.compile(r"\beval\s*\("), "eval"),
    (re.compile(r"fetch\s*\(|http\.request|https\.request|XMLHttpRequest"), "network call"),
    (re.compile(r"\.credentials|authorized_keys|id_rsa|\b\.ssh\b"), "sensitive path"),
]
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
        srcs = {}
        for n in names:
            if n.startswith("package/lib/") and (n.endswith(".js") or n.endswith(".mjs") or n.endswith(".ts")):
                srcs[n] = tf.extractfile(n).read().decode(errors="ignore")

    if pkg is not None:
        name = pkg.get("name", "")
        ver = pkg.get("version", "")
        if not re.match(r"^[a-z][a-z0-9-]*$", name or ""):
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
        insert_ids = re.findall(r"^\s*-\s*id:\s*(\S+)", patch, re.M)
        for pid in insert_ids:
            if pkg and pid != pkg.get("name"):
                issues.append(f"patch inserts foreign id {pid!r}")
        if pkg and pkg.get("name") not in insert_ids:
            warnings.append("patch does not insert the package's own id")

    all_src = "\n".join(srcs.values())

    # DSH schema DSL: required present-but-false kills the boot
    if re.search(r"required\s*:\s*false", all_src):
        issues.append("parameter schema uses required: false - DSH rejects it at boot (omit the key for optional params)")

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
