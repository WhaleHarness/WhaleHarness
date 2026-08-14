import { createHash } from "node:crypto";
import { resolve4 } from "node:dns/promises";
import { connect } from "node:tls";
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

async function checkSite() {
  const out = {
    url: SITE,
    https: null,
    http_code: null,
    dns: [],
    tls_days_left: null,
    manifest: null,
    plugins: [],
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
    for (const p of manifest.plugins) {
      const tarballRes = await fetch(SITE + p.tarball);
      if (!tarballRes.ok) {
        out.plugins.push({ name: p.name, version: p.version, tarball: "HTTP " + tarballRes.status });
        continue;
      }
      const buf = Buffer.from(await tarballRes.arrayBuffer());
      const digest = createHash("sha256").update(buf).digest("hex");
      out.plugins.push({
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
    "Check the WhaleHarness plugin site health: HTTPS status, DNS resolution, TLS certificate expiry, and the integrity (sha256) of every published plugin tarball. Call it when the user asks whether WhaleHarness is up, or wants a health report.",
  parameters: {},
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        url: { type: "string", required: true },
        https: { type: "boolean", required: true },
        http_code: { type: "number", required: true },
        dns: { type: "array", items: { type: "string" } },
        tls_days_left: { type: "number", required: true },
        manifest: { type: "string", required: true },
        plugins: {
          type: "array",
          items: {
            type: "object",
            additionalProperties: false,
            properties: {
              name: { type: "string", required: true },
              version: { type: "string", required: true },
              tarball: { type: "string", required: true },
              sha256_ok: { type: "boolean" }
            }
          }
        },
        checked_at: { type: "string", required: true }
      }
    },
    render(_args, value) {
      const lines = [
        "🐋 WhaleHarness 健康报告",
        "站点 " + value.url + " → HTTP " + value.http_code + (value.https ? " (https ✓)" : " (no https ✗)"),
        "DNS " + value.dns.join(", "),
        "TLS 证书剩余 " + value.tls_days_left + " 天" + (value.tls_days_left > 14 ? "" : "（⚠ 快到期）"),
        "manifest: " + value.manifest,
        "插件完整性:"
      ];
      for (const p of value.plugins) {
        lines.push("  · " + p.name + " v" + p.version + " → " + p.tarball + (p.sha256_ok === false ? "（⚠ sha256 不符）" : p.sha256_ok === true ? "（sha256 ✓）" : ""));
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
