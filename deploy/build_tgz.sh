#!/bin/bash
# Reproducible plugin tarball builder (v2, 2026-08-19 round26 experiment 结论落地).
# usage: build_tgz.sh <src_dir> <out_tgz> [epoch]
# All file/dir mtimes are pinned to one epoch + tar entries sorted, so identical
# source + command yields byte-identical tarballs across Linux(GNU) and macOS(BSD).
# v1 -> v2 修复(实证):①EPOCH 跨平台(GNU -printf 优先,BSD stat 兜底)②去 --no-mac-metadata
#   ③touch 覆盖目录(不止文件)④--sort=name 固定条目顺序⑤lib 拷包排除 *.tsbuildinfo。
set -e
SRC=$1
OUT=$2
EPOCH=$3
if [ -z "$EPOCH" ]; then
  EPOCH=$(find "$SRC" -type f -printf '%T@
' 2>/dev/null | sort -n | head -1 | cut -d. -f1)
fi
if [ -z "$EPOCH" ]; then
  # macOS/BSD fallback
  EPOCH=$(find "$SRC" -type f -exec stat -f %m {} + 2>/dev/null | sort -n | head -1)
fi
export COPYFILE_DISABLE=1
TMP=$(mktemp -d)
mkdir -p "$TMP/package"
cp "$SRC"/package.json "$TMP/package/" 2>/dev/null || true
cp "$SRC"/cordis.patch.yml "$TMP/package/" 2>/dev/null || true
cp "$SRC"/README.md "$TMP/package/" 2>/dev/null || true
cp "$SRC"/README.* "$TMP/package/" 2>/dev/null || true
cp "$SRC"/LICENSE "$TMP/package/" 2>/dev/null || true
# root main 入口（cordis 合法形态：main=index.js 在根，如 dsh-vision-any）
cp "$SRC"/index.js "$TMP/package/" 2>/dev/null || true
cp "$SRC"/index.mjs "$TMP/package/" 2>/dev/null || true
cp "$SRC"/types.d.ts "$TMP/package/" 2>/dev/null || true
cp "$SRC"/dsh-plugin.json "$TMP/package/" 2>/dev/null || true
if [ -d "$SRC/lib" ]; then
  cp -R "$SRC/lib" "$TMP/package/"
  find "$TMP/package/lib" -name '*.tsbuildinfo' -delete 2>/dev/null || true
fi
if [ -d "$SRC/client" ]; then
  cp -R "$SRC/client" "$TMP/package/"
fi
if [ -d "$SRC/assets" ]; then
  cp -R "$SRC/assets" "$TMP/package/"
fi
if [ -d "$SRC/skills" ]; then
  cp -R "$SRC/skills" "$TMP/package/"
fi
if [ -d "$SRC/bin" ]; then
  cp -R "$SRC/bin" "$TMP/package/"
fi
TS=$(date -u -d "@$EPOCH" +%Y%m%d%H%M.%S 2>/dev/null || date -r "$EPOCH" +%Y%m%d%H%M.%S)
find "$TMP/package" -exec touch -t "$TS" {} +
if tar --sort=name -cf /dev/null --files-from /dev/null 2>/dev/null; then
  # GNU tar: --sort=name 固定条目顺序
  tar --sort=name --no-xattrs -cf "$OUT.tar" -C "$TMP" package
else
  # bsdtar(macOS): 无 --sort=name, 只去 xattr
  tar --no-xattrs -cf "$OUT.tar" -C "$TMP" package
fi
# gzip -n: 去掉 gzip 头的时间戳/文件名 — 同源码同命令 → 外层 sha 恒定 (round745)
gzip -n -9 -c "$OUT.tar" > "$OUT"
rm -f "$OUT.tar"
rm -rf "$TMP"
echo "built $OUT (epoch $EPOCH)"
