// whale-memory v0.1.0 — explicit cross-session memory for DSH.
// Persistence: the official storage-domain service (survives sandboxes;
// the storage hub is mounted by web profiles). No subprocess, no network,
// no credential access — WhaleHarness red lines apply to our own code.
import { defineTool } from "@deepseek-ai/dsh-tools";
import { defineDomain, domainTable } from "@deepseek-ai/dsh-storage-domain";
import { z } from "zod";

const name = "whale-memory";
const inject = ["tools"];

const MAX_KEYS = 1000;
const MAX_VALUE_BYTES = 65536;
const KEY_RE = /^[A-Za-z0-9._:-]{1,128}$/;

const memoryRowSchema = z.object({
  value: z.string(),
  updatedAt: z.string()
});

const memoryDomainSpec = defineDomain({
  name: "whale_memory",
  version: 0,
  tables: { memories: domainTable(memoryRowSchema) }
});

let domainHandle = null;

async function table() {
  if (domainHandle === null) {
    throw new Error("whale-memory storage is unavailable in this profile (the storage service is not mounted); it works in web profiles");
  }
  return domainHandle.table("memories");
}

function validateKey(key) {
  const k = String(key ?? "").trim();
  if (!KEY_RE.test(k)) throw new Error("invalid key: use 1-128 chars of A-Za-z0-9._:-");
  return k;
}

function textOut(lines) {
  const nl = String.fromCharCode(10);
  return [{ type: "text", text: lines.join(nl) }];
}

const setTool = defineTool({
  name: "whale_memory_set",
  description:
    "Remember something across DSH sessions. Store one named memory (key + value) in the local whale-memory store; any session on this machine can recall it later with whale_memory_get. Overwrites the previous value under the same key.",
  parameters: {
    key: {
      type: "string",
      required: true,
      description: "Memory name. 1-128 chars of letters, digits, dot, underscore, colon, hyphen."
    },
    value: {
      type: "string",
      required: true,
      description: "Memory content. Up to 64KB of text."
    }
  },
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        key: { type: "string", required: true },
        updated_at: { type: "string", required: true }
      }
    },
    render(_args, value) {
      return textOut(["🐋 鲸群记忆已记下 " + value.key + "（" + value.updated_at + "）", "任何 DSH 会话可用 whale_memory_get 取回。"]);
    }
  },
  async execute(args) {
    const key = validateKey(args.key);
    const value = String(args.value ?? "");
    if (Buffer.byteLength(value, "utf8") > MAX_VALUE_BYTES) throw new Error("value too large (max 64KB)");
    const t = await table();
    if (t.get(key) === undefined && t.size >= MAX_KEYS) {
      throw new Error("memory store is full (" + MAX_KEYS + " keys); delete some with whale_memory_delete first");
    }
    const now = new Date().toISOString();
    await t.put(key, { value, updatedAt: now });
    return { key, updated_at: now };
  }
});

const getTool = defineTool({
  name: "whale_memory_get",
  description:
    "Recall one named memory written earlier by any DSH session on this machine (via whale_memory_set). Returns found=false when the key has never been set.",
  parameters: {
    key: {
      type: "string",
      required: true,
      description: "Memory name to recall."
    }
  },
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        key: { type: "string", required: true },
        found: { type: "boolean", required: true },
        value: { type: "string" },
        updated_at: { type: "string" }
      }
    },
    render(_args, value) {
      if (!value.found) return textOut(["🐋 鲸群记忆里没有 " + value.key + "。", "先用 whale_memory_set 记下它。"]);
      return textOut(["🐋 记忆 " + value.key + "（" + value.updated_at + "）：", value.value ?? ""]);
    }
  },
  async execute(args) {
    const key = validateKey(args.key);
    const t = await table();
    const entry = t.get(key);
    if (entry === undefined) return { key, found: false };
    return { key, found: true, value: entry.value, updated_at: entry.updatedAt };
  }
});

const listTool = defineTool({
  name: "whale_memory_list",
  description:
    "List every named memory in the local whale-memory store (keys and last-updated times), newest first. Lets any session see what previous sessions decided to remember.",
  parameters: {},
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        keys: {
          type: "array",
          required: true,
          items: {
            type: "object",
            additionalProperties: false,
            properties: {
              key: { type: "string", required: true },
              updated_at: { type: "string", required: true }
            }
          }
        }
      }
    },
    render(_args, value) {
      const keys = value.keys ?? [];
      if (keys.length === 0) return textOut(["🐋 鲸群记忆还是空的。", "用 whale_memory_set 写下第一条。"]);
      const lines = ["🐋 鲸群记忆（" + keys.length + " 条，最新在前）："];
      for (const item of keys) lines.push("  · " + item.key + " — " + item.updated_at);
      return textOut(lines);
    }
  },
  async execute() {
    const t = await table();
    const keys = [...t.entries()].map(([key, entry]) => ({ key, updated_at: entry.updatedAt }));
    keys.sort((a, b) => (b.updated_at ?? "").localeCompare(a.updated_at ?? ""));
    return { keys };
  }
});

const deleteTool = defineTool({
  name: "whale_memory_delete",
  description:
    "Forget one named memory from the local whale-memory store. Returns true when the key existed and was removed, false when it was already absent.",
  parameters: {
    key: {
      type: "string",
      required: true,
      description: "Memory name to forget."
    }
  },
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        key: { type: "string", required: true },
        deleted: { type: "boolean", required: true }
      }
    },
    render(_args, value) {
      return textOut(value.deleted
        ? ["🐋 已忘记 " + value.key + "。"]
        : ["🐋 记忆里本来就没有 " + value.key + "。"]);
    }
  },
  async execute(args) {
    const key = validateKey(args.key);
    const t = await table();
    const existed = t.get(key) !== undefined;
    if (existed) await t.delete(key);
    return { key, deleted: existed };
  }
});

function apply(ctx) {
  ctx.tools.register(setTool);
  ctx.tools.register(getTool);
  ctx.tools.register(listTool);
  ctx.tools.register(deleteTool);
  // Optional service: web profiles mount the storage hub; headless ones
  // may not. Tools degrade with a clear error instead of breaking boot.
  ctx.inject(["storageDomain"], (domainCtx) => {
    domainCtx.storageDomain.open(memoryDomainSpec).then((handle) => {
      domainHandle = handle;
    });
  });
}

export { apply, inject, name };
