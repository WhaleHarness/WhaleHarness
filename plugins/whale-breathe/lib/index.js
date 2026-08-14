import { defineTool } from "@deepseek-ai/dsh-tools";

// WhaleHarness · whale-breathe
// A fully local, side-effect-free tool. No network calls, no dynamic code
// execution, no credential or filesystem access — compliant with the site's
// security red lines.

const name = "whale-breathe";
const inject = ["tools"];

const whaleBreatheTool = defineTool({
  name: "whale_breathe",
  description:
    "Offer a short, whale-paced breathing exercise to help the user (or a collaborator) reset focus or calm down. Call it when someone is stressed, overwhelmed, or simply needs a mindful pause between tasks.",
  parameters: {
    minutes: {
      type: "number",
      description: "How many minutes to breathe for. Defaults to 1, clamped to 1..10."
    },
    note: {
      type: "string",
      description: "Optional one-line note about why a pause helps right now."
    }
  },
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        script: { type: "string", required: true },
        url: { type: "string", required: true }
      }
    },
    render(_args, value) {
      return [{
        type: "text",
        text: value.script + "\n\n—— WhaleHarness 鲸鱼呼吸法 · " + value.url
      }];
    }
  },
  async execute(args) {
    const minutes = Math.max(1, Math.min(10, Math.round(args.minutes || 1)));
    const note = args.note ? "（" + args.note + "）" : "";
    const rhythm = [
      "吸气 4 秒，想象鲸鱼缓缓上浮。",
      "屏息 4 秒，停在温柔的水层里。",
      "呼气 6 秒，像鲸鱼潜回深处。",
      "停顿 2 秒，听一听海面之下的安静。"
    ].join("\n");
    const script =
      "鲸鱼呼吸法 · " + minutes + " 分钟" + note + "\n\n" +
      "跟着鲸群的节奏慢下来，循环下面四拍：\n" + rhythm + "\n\n" +
      "深海不赶时间，你也不必把呼吸压缩成任务。";
    return { script, url: "https://whaleharness.com" };
  }
});

function apply(ctx) {
  ctx.tools.register(whaleBreatheTool);
}

export { apply, inject, name };
