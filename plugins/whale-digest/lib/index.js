import { defineTool } from "@deepseek-ai/dsh-tools";

const name = "whale-digest";
const inject = ["tools"];

const STOP_WORDS = new Set([
  "the", "a", "an", "and", "or", "but", "of", "to", "in", "for", "on", "at", "by",
  "with", "is", "are", "was", "were", "be", "been", "being", "that", "this", "it", "as",
  "from", "的", "了", "和", "是", "在", "与", "及", "对", "将", "一个", "我们", "你们"
]);

function terms(text) {
  return text.toLowerCase().match(/[a-z0-9_'-]+|[\u4e00-\u9fff]{2,}/g) ?? [];
}

function splitSentences(text) {
  return text.match(/[^.!?。！？]+[.!?。！？]*/g)?.map((item) => item.trim()).filter(Boolean) ?? [];
}

function summarize(text, limit) {
  const sentences = splitSentences(text);
  if (sentences.length <= limit) return sentences;

  const frequency = new Map();
  for (const term of terms(text)) {
    if (!STOP_WORDS.has(term) && term.length > 1) frequency.set(term, (frequency.get(term) ?? 0) + 1);
  }

  return sentences
    .map((sentence, index) => ({
      sentence,
      index,
      score: terms(sentence).reduce((total, term) => total + (frequency.get(term) ?? 0), 0)
    }))
    .sort((left, right) => right.score - left.score || left.index - right.index)
    .slice(0, limit)
    .sort((left, right) => left.index - right.index)
    .map(({ sentence }) => sentence);
}

function keywords(text) {
  const counts = new Map();
  for (const term of terms(text)) {
    if (!STOP_WORDS.has(term) && term.length > 1) counts.set(term, (counts.get(term) ?? 0) + 1);
  }
  return [...counts.entries()]
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .slice(0, 5)
    .map(([term]) => term);
}

const tool = defineTool({
  name: "whale_digest",
  description: "Summarize supplied Chinese or English text locally. Use it when the user wants the main points, keywords, or a shorter readable version of text they provide.",
  parameters: {
    text: {
      type: "string",
      required: true,
      description: "The text to summarize."
    },
    max_sentences: {
      type: "number",
      description: "Optional number of summary sentences, from 1 to 10. Defaults to 3."
    }
  },
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        summary: { type: "string", required: true },
        keywords: { type: "array", required: true, items: { type: "string" } },
        source_length: { type: "number", required: true }
      }
    },
    render(_args, value) {
      const keywordLine = value.keywords.length ? `\n\n关键词：${value.keywords.join("、")}` : "";
      return [{ type: "text", text: `${value.summary}${keywordLine}\n\n原文长度：${value.source_length} 字符` }];
    }
  },
  async execute(args) {
    const text = args.text.trim();
    const requested = Number.isFinite(args.max_sentences) ? Math.round(args.max_sentences) : 3;
    const limit = Math.min(10, Math.max(1, requested));
    const selected = summarize(text, limit);
    return {
      summary: selected.join(" "),
      keywords: keywords(text),
      source_length: text.length
    };
  }
});

function apply(ctx) {
  ctx.tools.register(tool);
}

export { apply, inject, name };
