import { defineTool } from "@deepseek-ai/dsh-tools";

const FORTUNES = [
  "海面之上是浪，海面之下是路。",
  "鲸不追浪，浪自来。",
  "大音希声，大鲸潜深。",
  "你听到的每一声鲸歌，都是深海对浅海的回信。",
  "别怕下潜：压力最大的地方，浮力也最大。",
  "鲸群从不解释方向，它们只是游成方向。",
  "涨潮时别数脚印，退潮时也别怪沙滩。",
  "灯塔不照亮整片海，只照亮你该避开的礁。",
  "盐从不喊咸，海却因它成海。",
  "沉船不是海的错，是船问了海答不了的问题。",
  "海沟最深处，也最安静。",
  "雾再大，看罗盘，别盯雾。",
  "鲸落不是终点，是海底的一场开饭。",
  "浮标晃得最凶的地方，水未必最深。",
  "冰山露给你看的部分，从来不是撞沉你的部分。",
  "退潮的水洼里，也盛得下自己的月亮。",
  "别教海水往哪流，选好你站的那条洋流。",
  "海不教鱼怎么游，鱼生来会水。",
  "潮汐表不说谎，只在你看得懂时才有用。",
  "锚沉到底，船自然停。",
  "浪大不是海发火，是风借海说话。",
  "退潮带走沙，带不走岸。",
  "海螺里装着海，贴耳才听得见。",
  "帆顺风时快，逆风时才知道它值钱。",
  "海图再旧，也比船长的记忆准。",
  "别在退潮时量海，海没变浅，是你站错了时候。",
  "一只鲸鱼从不问海有多深，它只问往哪游。",
  "鲸歌是深海的普通话，波浪是它的方言。",
  "白鲸不是白，是深到发光。",
  "鲸群游过的地方，深海记得。",
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