import { defineTool } from "@deepseek-ai/dsh-tools";

const FORTUNES = [
  "海面之上是浪，海面之下是路。",
  "鲸不追浪，浪自来。",
  "大音希声，大鲸潜深。",
  "你听到的每一声鲸歌，都是深海对浅海的回信。",
  "别怕下潜：压力最大的地方，浮力也最大。",
  "鲸群从不解释方向，它们只是游成方向。"
];

const name = "whale-fortune";
const inject = ["tools"];

const fortuneTool = defineTool({
  name: "whale_fortune",
  description:
    "Draw one deep-sea aphorism from the WhaleHarness fortune pool. Call it when the user asks for inspiration, a motto, or a moment of reflection.",
  parameters: {
    topic: {
      type: "string",
      description: "Optional theme to mention; affects nothing, whales are above themes."
    }
  },
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        fortune: { type: "string", required: true },
        url: { type: "string", required: true }
      }
    },
    render(_args, value) {
      return [{
        type: "text",
        text: value.fortune + "\n\n—— WhaleHarness 鲸鱼箴言 · " + value.url
      }];
    }
  },
  async execute(args) {
    const seed = Date.now() % FORTUNES.length;
    return {
      fortune: FORTUNES[seed],
      url: "https://whaleharness.com"
    };
  }
});

function apply(ctx) {
  ctx.tools.register(fortuneTool);
}

export { apply, inject, name };
