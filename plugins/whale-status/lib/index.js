import { createHash } from "node:crypto";
import { resolve4 } from "node:dns/promises";
import { connect } from "node:tls";
import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import { homedir } from "node:os";
import { defineTool } from "@deepseek-ai/dsh-tools";

const name = "whale-status";
const inject = ["tools"];

const SITE = "https://whaleharness.com";
const HOST = "whaleharness.com";

async function tlsDaysLeft(host) {
  return await new Promise((resolvePromise, reject) => {
    const sock = connect({ host, port: 443, servername: host }, () => {
      const cert = sock.getPeerCertificate();
      sock.destroy();
      if (!cert || !cert.valid_to) return reject(new Error("no certificate presented"));
      const days = Math.floor((Date.parse(cert.valid_to) - Date.now()) / 86400000);
      resolvePromise(days);
    });
    sock.on("error", reject);
  });
}

function newer(a, b) {
  const pa = String(a).split(".").map(Number);
  const pb = String(b).split(".").map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const x = pa[i] ?? 0;
    const y = pb[i] ?? 0;
    if (x !== y) return x > y;
  }
  return false;
}

// Read every plugin installed in any local profile (not only store plugins).
async function checkLocalPlugins(onlinePlugins) {
  const online = new Map(onlinePlugins.map((p) => [p.name, p.version]));
  const home = process.env.DSH_HOME || join(homedir(), ".dsh");
  const profilesDir = join(home, "profiles");
  const plugins = [];
  const updates = [];
  let profiles;
  try {
    profiles = await readdir(profilesDir);
  } catch {
    return { plugins, updates, note: "no profiles dir at " + profilesDir };
  }
  const seen = new Set();
  for (const profile of profiles) {
    let pkg;
    try {
      pkg = JSON.parse(await readFile(join(profilesDir, profile, "package.json"), "utf8"));
    } catch {
      continue;
    }
    const deps = pkg.dependencies || {};
    for (const [depName, depVer] of Object.entries(deps)) {
      const clean = String(depVer).replace(/^[\^~>=<\s]+/, "");
      if (seen.has(depName)) continue;
      seen.add(depName);
      plugins.push({ name: depName, version: clean, profile });
      const latest = online.get(depName);
      if (latest && newer(latest, clean)) {
        updates.push({ name: depName, installed: clean, latest, profile });
      }
    }
  }
  return { plugins, updates };
}

async function checkSite() {
  const out = {
    url: SITE,
    https: null,
    http_code: null,
    dns: [],
    tls_days_left: null,
    manifest: null,
    store_plugins: [],
    plugins: [],
    updates: [],
    checked_at: new Date().toISOString()
  };
  const res = await fetch(SITE + "/healthz", { redirect: "manual" });
  out.https = res.url.startsWith("https://");
  out.http_code = res.status;
  out.dns = await resolve4(HOST);
  try {
    out.tls_days_left = await tlsDaysLeft(HOST);
  } catch (err) {
    out.tls_days_left = -1;
  }
  try {
    const manifest = await (await fetch(SITE + "/plugins.json")).json();
    out.manifest = manifest.name;
    const storeNames = new Set(manifest.plugins.map((p) => p.name));
    // ecosystem audit verdicts, keyed by package name (repo owner/name -> name)
    const audit = new Map();
    try {
      const ad = await (await fetch(SITE + "/audit.json")).json();
      for (const e of ad.entries || []) {
        const nm = String(e.repo || "").split("/")[1];
        if (nm && !audit.has(nm)) {
          audit.set(nm, { verdict: e.verdict, issues: e.issues || [], version: e.version });
        }
      }
    } catch { /* audit unavailable: mark everything unverified */ }
    const local = await checkLocalPlugins(manifest.plugins);
    out.updates = local.updates;
    out.plugins = local.plugins.map((p) => {
      const a = audit.get(p.name);
      const inStore = storeNames.has(p.name);
      return {
        name: p.name,
        installed: p.version,
        profile: p.profile,
        source: inStore ? "store" : a ? "audited" : "other",
        verification: inStore ? "pass" : a ? (a.verdict === "PASS" ? "pass" : a.verdict === "REJECT" ? "reject" : "unevaluated") : "unverified",
        audit_version: a?.version ?? "",
        issues: a?.issues ?? []
      };
    });
    for (const p of manifest.plugins) {
      const tarballRes = await fetch(SITE + p.tarball + "?src=verify"); // verify traffic, excluded from download stats
      if (!tarballRes.ok) {
        out.store_plugins.push({ name: p.name, version: p.version, tarball: "HTTP " + tarballRes.status });
        continue;
      }
      const buf = Buffer.from(await tarballRes.arrayBuffer());
      const digest = createHash("sha256").update(buf).digest("hex");
      out.store_plugins.push({
        name: p.name,
        version: p.version,
        tarball: "ok",
        sha256_ok: digest === p.sha256
      });
    }
  } catch (err) {
    out.manifest = "unreachable: " + String(err?.message ?? err);
  }
  return out;
}

const statusTool = defineTool({
  name: "whale_status",
  description:
    "Check WhaleHarness site health (HTTPS, DNS, TLS, tarball integrity) AND run a local plugin checkup: every plugin installed in any DSH profile with its verification status (WhaleHarness-audited PASS / REJECT with reasons / not audited) and available updates. Call it when the user asks about site status, installed plugins, or which plugins are safe.",
  parameters: {},
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
        required: ["url", "https", "http_code", "dns", "tls_days_left", "manifest", "store_plugins", "plugins", "checked_at", "updates"],
      properties: {
        url: { type: "string", required: true },
        https: { type: "boolean", required: true },
        http_code: { type: "number", required: true },
        dns: { type: "array", required: true, items: { type: "string" } },
        tls_days_left: { type: "number", required: true },
        manifest: { type: "string", required: true },
        store_plugins: {
          type: "array",
          items: {
            type: "object",
            additionalProperties: false,
            properties: {
              name: { type: "string" },
              version: { type: "string" },
              tarball: { type: "string" },
              sha256_ok: { type: "boolean" }
            }
          }
        },
        plugins: {
          type: "array",
          items: {
            type: "object",
            additionalProperties: false,
            properties: {
              name: { type: "string" },
              installed: { type: "string" },
              profile: { type: "string" },
              source: { type: "string" },
              verification: { type: "string" },
              audit_version: { type: "string" },
              issues: { type: "array", items: { type: "string" } }
            }
          }
        },
        checked_at: { type: "string", required: true },
        updates: {
          type: "array",
          items: {
            type: "object",
            additionalProperties: false,
            properties: {
              name: { type: "string" },
              installed: { type: "string" },
              latest: { type: "string" },
              profile: { type: "string" }
            }
          }
        }
      }
    },
    render(_args, value) {
      const V = { pass: "✅ 验证通过", reject: "❌ 审计 REJECT", unevaluated: "◻ 已审未评估", unverified: "⚠ 未经验证" };
      const lines = [
        "🐋 WhaleHarness 体检报告",
        "站点 " + value.url + " → HTTP " + value.http_code + (value.https ? " (https ✓)" : " (no https ✗)"),
        "DNS " + value.dns.join(", "),
        "TLS 证书剩余 " + value.tls_days_left + " 天" + (value.tls_days_left > 14 ? "" : "（⚠ 快到期）"),
        "manifest: " + value.manifest,
        "本机插件体检:"
      ];
      const localPlugins = value.plugins || [];
      if (localPlugins.length === 0) {
        lines.push("  （未发现本机插件）");
      }
      for (const p of localPlugins) {
        let line = "  · " + p.name + " v" + p.installed + "（" + p.profile + "）→ " + (V[p.verification] || p.verification);
        if (p.verification === "reject" && p.issues.length > 0) {
          line += "：" + p.issues.join("；");
        }
        if (p.source === "store" && p.verification === "pass") {
          line += "（商店在架验证）";
        } else if (p.verification !== "unverified") {
          line += "（审计 " + p.audit_version + "）";
        }
        lines.push(line);
      }
      if (localPlugins.some((p) => p.verification === "reject")) {
        lines.push("报告: https://whaleharness.com/audit-report.md");
      }
      lines.push("商店在架完整性:");
      for (const p of value.store_plugins) {
        lines.push("  · " + p.name + " v" + p.version + " → " + p.tarball + (p.sha256_ok === false ? "（⚠ sha256 不符）" : p.sha256_ok === true ? "（sha256 ✓）" : ""));
      }
      const ups = value.updates || [];
      if (ups.length > 0) {
        lines.push("本机可更新（" + ups.length + " 个）:");
        for (const u of ups) {
          lines.push("  ↑ " + u.name + " " + u.installed + " → " + u.latest + "（" + u.profile + "）");
          lines.push("    dsh plugin --profile " + u.profile + " add -w https://whaleharness.com/p/" + u.name);
        }
      } else {
        lines.push("本机已装插件:全部最新。");
      }
      return [{ type: "text", text: lines.join("\n") }];
    }
  },
  async execute() {
    return await checkSite();
  }
});

function apply(ctx) {
  ctx.tools.register(statusTool);
}

export { apply, inject, name };
