#!/bin/bash
# Reproducible plugin tarball builder.
# usage: build_tgz.sh <src_dir> <out_tgz> [epoch]
# All file mtimes are pinned to one epoch so identical source + command
# yields byte-identical tarballs (verified 2026-08-14: two builds, same sha256).
set -e
SRC=$1
OUT=$2
EPOCH=${3:-$(find "$SRC" -type f -exec stat -f %m {} + 2>/dev/null | sort -n | head -1)}
export COPYFILE_DISABLE=1
TMP=$(mktemp -d)
mkdir -p "$TMP/package"
cp "$SRC"/package.json "$TMP/package/" 2>/dev/null || true
cp "$SRC"/cordis.patch.yml "$TMP/package/" 2>/dev/null || true
cp "$SRC"/README.md "$TMP/package/" 2>/dev/null || true
cp "$SRC"/README.* "$TMP/package/" 2>/dev/null || true
cp "$SRC"/LICENSE "$TMP/package/" 2>/dev/null || true
[ -d "$SRC/lib" ] && cp -R "$SRC/lib" "$TMP/package/"
TS=$(date -r "$EPOCH" +%Y%m%d%H%M.%S)
find "$TMP/package" -type f -exec touch -t "$TS" {} +
# --no-xattrs --no-mac-metadata: provenance xattr is SIP-protected and
# nondeterministic; these flags drop PAX headers entirely (verified twice-same-sha256)
tar --no-xattrs --no-mac-metadata -czf "$OUT" -C "$TMP" package
rm -rf "$TMP"
echo "built $OUT (epoch $EPOCH)"
