import { defineTool } from "@deepseek-ai/dsh-tools";

const name = "whale-store";
const inject = ["tools"];

const SITE = "https://whaleharness.com";
const SHORT_LINK_BASE = "https://whaleharness.com/p/";
const INSTALL_SHORT_PREFIX = "dsh plugin --profile web add -w ";

async function fetchJson(url) {
  const res = await fetch(url, { redirect: "follow" });
  if (!res.ok) {
    throw new Error("WhaleHarness fetch failed: " + url + " -> HTTP " + res.status);
  }
  return await res.json();
}

async function loadCatalog() {
  const data = await fetchJson(SITE + "/plugins.json");
  return Array.isArray(data.plugins) ? data.plugins : [];
}

async function loadAuditIndex() {
  const data = await fetchJson(SITE + "/audit.json");
  const entries = Array.isArray(data.entries) ? data.entries : [];
  const index = new Map();
  for (const e of entries) {
    const repo = String(e.repo || "");
    if (repo && !index.has(repo)) {
      index.set(repo, {
        verdict: String(e.verdict || ""),
        issues: Array.isArray(e.issues) ? e.issues.map((s) => String(s)) : [],
        version: String(e.version || ""),
        commit: String(e.commit || "")
      });
    }
  }
  return index;
}

function shortLink(pname) {
  return SHORT_LINK_BASE + String(pname);
}

function shortInstall(pname) {
  return INSTALL_SHORT_PREFIX + shortLink(pname);
}

function toListItem(p) {
  return {
    name: String(p.name || ""),
    version: String(p.version || ""),
    description: String(p.description || ""),
    description_en: String(p.description_en || ""),
    install: String(p.install || ""),
    install_short: shortInstall(p.name)
  };
}

const pluginItemSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    name: { type: "string", required: true },
    version: { type: "string", required: true },
    description: { type: "string", required: true },
    description_en: { type: "string" },
    install: { type: "string", required: true },
    install_short: { type: "string", required: true }
  }
};

const listTool = defineTool({
  name: "whale_store_list",
  description:
    "List every verified plugin currently on the WhaleHarness store (https://whaleharness.com/plugins.json) with its name, version, description, and install command. Call it when the user asks what plugins are available or wants to browse the catalog.",
  parameters: {},
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        plugins: { type: "array", items: pluginItemSchema },
        count: { type: "number", required: true },
        checked_at: { type: "string", required: true }
      }
    },
    render(_args, value) {
      const lines = ["🐋 WhaleHarness 上架插件（" + value.count + " 个，实时来自 plugins.json）:"];
      for (const p of value.plugins) {
        lines.push("  · " + p.name + " v" + p.version + " — " + p.description);
      }
      lines.push("安装：调用 whale_store_install(name) 获取判定与精确安装命令。");
      return [{ type: "text", text: lines.join("\n") }];
    }
  },
  async execute() {
    const plugins = await loadCatalog();
    return {
      plugins: plugins.map(toListItem),
      count: plugins.length,
      checked_at: new Date().toISOString()
    };
  }
});

const searchTool = defineTool({
  name: "whale_store_search",
  description:
    "Search the WhaleHarness store by keyword: case-insensitive match against plugin name and description (Chinese and English). The optional 'category' filter is reserved for a future category field and is currently ignored (plugins.json has no category yet). Call it when the user wants to find plugins for a purpose or topic.",
  parameters: {
    query: {
      type: "string",
      required: true,
      description: "Keyword to match against plugin name and description."
    },
    category: {
      type: "string",
      description: "Reserved: category filter. The store has no category field yet, so this is ignored."
    }
  },
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        query: { type: "string", required: true },
        category: { type: "string", required: true },
        matches: { type: "array", items: pluginItemSchema },
        count: { type: "number", required: true }
      }
    },
    render(_args, value) {
      if (value.count === 0) {
        return [{
          type: "text",
          text: "🐋 搜索“" + value.query + "”无匹配。换关键词，或用 whale_store_list 看全部。"
        }];
      }
      const lines = ["🐋 搜索“" + value.query + "”：" + value.count + " 个匹配:"];
      for (const p of value.matches) {
        lines.push("  · " + p.name + " v" + p.version + " — " + p.description);
      }
      lines.push("安装：调用 whale_store_install(name) 获取判定与精确安装命令。");
      return [{ type: "text", text: lines.join("\n") }];
    }
  },
  async execute(args) {
    const query = String(args.query || "").trim().toLowerCase();
    const category = String(args.category || "");
    const plugins = await loadCatalog();
    const matches = plugins
      .filter((p) => {
        if (!query) return true;
        const hay = [p.name, p.description, p.description_en]
          .map((s) => String(s || "").toLowerCase())
          .join("\n");
        return hay.includes(query);
      })
      .map(toListItem);
    return { query: String(args.query || ""), category, matches, count: matches.length };
  }
});

const installTool = defineTool({
  name: "whale_store_install",
  description:
    "Get the exact install command (full and short-link form) for a WhaleHarness store plugin, together with its audit verdict from https://whaleharness.com/audit.json. It only reads the catalog and audit data and prints the command — it never runs the install itself, so the calling agent executes the printed command with its own bash tool. Call it when the user wants to install a specific plugin.",
  parameters: {
    name: {
      type: "string",
      required: true,
      description: "Exact store plugin name, e.g. whale-status or dsh-genui."
    }
  },
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        name: { type: "string", required: true },
        version: { type: "string", required: true },
        audit: {
          type: "object",
          additionalProperties: false,
          properties: {
            matched: { type: "boolean", required: true },
            repo: { type: "string", required: true },
            verdict: { type: "string", required: true },
            version: { type: "string", required: true },
            commit: { type: "string", required: true },
            issues: { type: "array", items: { type: "string" } }
          }
        },
        install: { type: "string", required: true },
        install_short: { type: "string", required: true },
        url: { type: "string", required: true }
      }
    },
    render(_args, value) {
      const a = value.audit;
      const lines = [
        "🐋 whale-store 安装指引：",
        "  · " + value.name + " v" + value.version
      ];
      if (a.matched) {
        lines.push("  判定：" + a.verdict + "（来源 audit.json，repo " + a.repo + (a.version ? " v" + a.version : "") + (a.commit ? " @" + a.commit : "") + "）");
      } else {
        lines.push("  判定：上架验证通过（站方完整验证环；生态 audit.json 无此 repo 的独立条目" + (a.repo ? "：" + a.repo : "") + "）");
      }
      if (a.issues.length > 0) {
        lines.push("  审计问题：" + a.issues.join("；"));
      }
      lines.push("  安装（完整）：" + value.install);
      lines.push("  安装（短链）：" + value.install_short);
      lines.push("  短链：" + value.url);
      return [{ type: "text", text: lines.join("\n") }];
    }
  },
  async execute(args) {
    const target = String(args.name || "").trim();
    const plugins = await loadCatalog();
    const p = plugins.find((x) => String(x.name) === target);
    if (!p) {
      throw new Error("plugin not in store: " + (target || "(empty)") + " — use whale_store_list or whale_store_search to browse the catalog");
    }
    const auditIndex = await loadAuditIndex();
    const repo = String((p.source && p.source.repo) || "");
    const entry = auditIndex.get(repo);
    let audit;
    if (entry) {
      audit = {
        matched: true,
        repo,
        verdict: entry.verdict,
        version: entry.version,
        commit: entry.commit,
        issues: entry.issues
      };
    } else {
      audit = { matched: false, repo, verdict: "store-verified", version: "", commit: "", issues: [] };
    }
    return {
      name: String(p.name),
      version: String(p.version || ""),
      audit,
      install: String(p.install || ""),
      install_short: shortInstall(p.name),
      url: shortLink(p.name)
    };
  }
});

function apply(ctx) {
  ctx.tools.register(listTool);
  ctx.tools.register(searchTool);
  ctx.tools.register(installTool);
}

export { apply, inject, name };
