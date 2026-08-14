import { defineTool } from "@deepseek-ai/dsh-tools";

const PRAISES = [
  "鲸群为你转身：这一下，海面都亮了。",
  "座头鲸认证：干得漂亮，浪花都替你鼓掌。",
  "深渊之心也要夸你一句：稳。",
  "白鲸点头，抹香鲸记笔记：这是高手。",
  "整个鲸鱼表扬局一致通过：此功当载入鲸史。",
  "虎鲸路过，回头看了一眼，说：可以。"
];

const name = "whale-praise";
const inject = ["tools"];

const praiseTool = defineTool({
  name: "whale_praise",
  description:
    "Praise a human deed with cetacean-grade encouragement from WhaleHarness. Call it when the user or any collaborator deserves recognition.",
  parameters: {
    deed: {
      type: "string",
      required: true,
      description: "The deed worth praising, in one short sentence."
    }
  },
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        praise: { type: "string", required: true },
        url: { type: "string", required: true }
      }
    },
    render(_args, value) {
      return [{
        type: "text",
        text: value.praise + "\n\n—— WhaleHarness 鲸鱼表扬局 · " + value.url
      }];
    }
  },
  async execute(args) {
    let h = 0;
    for (const ch of args.deed) h = (h * 31 + ch.codePointAt(0)) >>> 0;
    return {
      praise: PRAISES[h % PRAISES.length],
      url: "https://whaleharness.com"
    };
  }
});

function apply(ctx) {
  ctx.tools.register(praiseTool);
}

export { apply, inject, name };
