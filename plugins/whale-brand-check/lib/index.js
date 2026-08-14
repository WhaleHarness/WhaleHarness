import { defineTool } from "@deepseek-ai/dsh-tools";

const name = "whale-brand-check";
const inject = ["tools"];

const BANNED = ["赋能", "抓手", "闭环", "颠覆", "卷", "yyds", "重磅", "爆炸", "震撼"];
const METAPHORS = ["鲸", "海", "浪", "鱼", "深", "船员", "上船", "潜"];

function check(text) {
  const issues = [];
  const words = text.toLowerCase();
  const banned = BANNED.filter((w) => text.includes(w));
  if (banned.length > 0) issues.push("禁用词：" + banned.join("、"));
  const exclaim = (text.match(/！|!/g) ?? []).length;
  if (exclaim > 3) issues.push("感叹号 " + exclaim + " 个（规范：不喊口号，≤3）");
  let metaphorCount = 0;
  for (const m of METAPHORS) {
    const count = (text.match(new RegExp(m, "g")) ?? []).length;
    metaphorCount += count;
  }
  if (metaphorCount > 3) issues.push("海洋比喻 " + metaphorCount + " 处（规范：每次最多一处）");
  const hasLink = text.includes("whaleharness.com") || text.includes("dsh plugin");
  if (!hasLink) issues.push("没有真实链接或安装命令（规范：每条必带）");
  const firstLine = text.split(/\n/)[0] ?? "";
  if (firstLine.length > 60) issues.push("首段 " + firstLine.length + " 字（规范：先结论后理由，别铺垫）");
  let score = 100;
  score -= banned.length * 20;
  score -= Math.max(0, exclaim - 3) * 10;
  score -= Math.max(0, metaphorCount - 3) * 5;
  if (!hasLink) score -= 15;
  if (firstLine.length > 60) score -= 10;
  score = Math.max(0, score);
  return {
    issues,
    score,
    verdict: score >= 80 ? "可发" : score >= 60 ? "小改后发" : "回炉"
  };
}

const brandTool = defineTool({
  name: "whale_brand_check",
  description:
    "Check a piece of WhaleHarness-facing copy against the whale-brand voice rules (deep, calm, witty): banned words, exclamation density, metaphor count, link presence, and lead-in length. Returns issues, a score, and a verdict.",
  parameters: {
    text: {
      type: "string",
      required: true,
      description: "The copy to review, as plain text."
    }
  },
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        issues: { type: "array", items: { type: "string" } },
        score: { type: "number", required: true },
        verdict: { type: "string", required: true }
      }
    },
    render(_args, value) {
      const lines = [
        "🐋 品牌体检 " + value.score + " 分 → " + value.verdict
      ];
      for (const issue of value.issues) lines.push("  · " + issue);
      return [{ type: "text", text: lines.join("\n") }];
    }
  },
  async execute(args) {
    return check(args.text);
  }
});

function apply(ctx) {
  ctx.tools.register(brandTool);
}

export { apply, inject, name };
