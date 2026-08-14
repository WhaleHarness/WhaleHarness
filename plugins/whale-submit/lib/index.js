import { readFile, readdir, stat } from "node:fs/promises";
import { basename, resolve, join, relative, sep } from "node:path";
import { defineTool } from "@deepseek-ai/dsh-tools";

const name = "whale-submit";
const inject = ["tools"];

const BOX = "https://whaleharness.com/submit/whalepod2026";
const MAX_BYTES = 5 * 1024 * 1024;

// -- minimal tar (ustar) writer, npm-style package/ prefix -----------------
function octal(value, width) {
  const s = value.toString(8);
  if (s.length > width - 1) throw new Error("field overflow");
  return s.padStart(width - 1, "0") + "\0";
}

function headerBlock(entryName, size, typeflag) {
  const h = Buffer.alloc(512);
  h.write(entryName.slice(0, 100), 0, "utf8");
  h.write(octal(0o644, 8), 100, "utf8");
  h.write(octal(0, 8), 108, "utf8");
  h.write(octal(0, 8), 116, "utf8");
  h.write(octal(size, 12), 124, "utf8");
  h.write(octal(0, 12), 136, "utf8");
  h.write("        ", 148, "utf8"); // chksum placeholder
  h.write(typeflag, 156, "utf8");
  h.write("", 157, "utf8");
  h.write("ustar\0", 257, "utf8");
  h.write("00", 263, "utf8");
  h.write("", 265, "utf8");
  h.write("", 297, "utf8");
  h.write(octal(0, 8), 329, "utf8");
  h.write(octal(0, 8), 337, "utf8");
  h.write("", 345, "utf8");
  h.write("", 500, "utf8");
  let sum = 0;
  for (const b of h) sum += b;
  h.write(octal(sum, 8), 148, "utf8");
  return h;
}

async function collectEntries(dir) {
  const entries = [];
  async function walk(cur) {
    const rel = relative(dir, cur);
    const prefix = rel === "" ? "package" : join("package", rel);
    const items = await readdir(cur);
    for (const item of items) {
      const full = join(cur, item);
      const st = await stat(full);
      if (st.isDirectory()) {
        entries.push({ name: prefix + "/" + item + "/", size: 0, typeflag: "5", data: null, full });
        await walk(full);
      } else if (st.isFile()) {
        entries.push({ name: prefix + "/" + item, size: st.size, typeflag: "0", data: null, full });
      }
    }
  }
  await walk(dir);
  const blobs = [];
  for (const e of entries) {
    blobs.push(e.typeflag === "5" ? { name: e.name, data: null, typeflag: "5" } : {
      name: e.name, data: await readFile(e.full), typeflag: "0"
    });
  }
  return blobs;
}

function buildTarball(blobs) {
  const parts = [];
  let total = 0;
  for (const { name: entryName, data, typeflag } of blobs) {
    const size = typeflag === "5" ? 0 : data.length;
    parts.push(headerBlock(entryName, size, typeflag));
    total += 512;
    if (typeflag === "0") {
      parts.push(data);
      const pad = (512 - (data.length % 512)) % 512;
      if (pad > 0) parts.push(Buffer.alloc(pad));
      total += data.length + pad;
    }
  }
  parts.push(Buffer.alloc(1024)); // two zero blocks, end of archive
  total += 1024;
  if (total > MAX_BYTES) throw new Error("tarball exceeds 5MB submission limit");
  return Buffer.concat(parts, total);
}

async function submitPackage(args) {
  const dir = resolve(args.path);
  if (/^[a-z][a-z0-9-]*$/.test(args.name) === false) {
    throw new Error("invalid package name (lowercase letters, digits, hyphens)");
  }
  if (/^\d+\.\d+\.\d+$/.test(args.version) === false) {
    throw new Error("invalid version (x.y.z)");
  }
  let st;
  try {
    st = await stat(dir);
  } catch {
    throw new Error("path does not exist: " + args.path);
  }
  if (!st.isDirectory()) throw new Error("path must be a directory");
  for (const rel of [".", ".."]) void rel;
  const files = await readdir(dir);
  if (!files.includes("package.json")) {
    throw new Error("directory has no package.json — not a plugin package");
  }
  const blobs = await collectEntries(dir);
  const tarball = buildTarball(blobs);
  const fileName = args.name + "-" + args.version + ".tgz";
  const url = BOX + "/" + fileName;
  const res = await fetch(url, { method: "PUT", body: tarball });
  if (res.status === 201 || res.status === 200) {
    return {
      status: "submitted",
      url,
      bytes: tarball.length,
      files: blobs.length,
      review: "审核公开透明：投稿箱可读，站方 72 小时内给出结果。"
    };
  }
  throw new Error("submission rejected by box: HTTP " + res.status);
}

const submitTool = defineTool({
  name: "whale_submit",
  description:
    "Package a local plugin directory as a tarball and submit it to the WhaleHarness public submission box. Call it when the user wants to publish their own DSH plugin to https://whaleharness.com. Requires a local directory containing package.json.",
  parameters: {
    path: {
      type: "string",
      required: true,
      description: "Absolute or relative path to the plugin directory to submit."
    },
    name: {
      type: "string",
      required: true,
      description: "Package name: lowercase letters, digits, hyphens."
    },
    version: {
      type: "string",
      required: true,
      description: "Semver-like version, e.g. 0.1.0."
    }
  },
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        status: { type: "string", required: true },
        url: { type: "string", required: true },
        bytes: { type: "number", required: true },
        files: { type: "number", required: true },
        review: { type: "string", required: true }
      }
    },
    render(_args, value) {
      return [{
        type: "text",
        text: "投稿成功 ✅ " + value.files + " 个文件，" + value.bytes + " 字节。\n公开投稿箱：" + value.url + "\n" + value.review
      }];
    }
  },
  async execute(args) {
    return await submitPackage(args);
  }
});

function apply(ctx) {
  ctx.tools.register(submitTool);
}

export { apply, inject, name };
