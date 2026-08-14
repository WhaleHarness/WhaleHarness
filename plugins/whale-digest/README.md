# whale-digest

`whale_digest` is an offline extractive summarizer for DeepSeek Harness. It accepts Chinese or English text and returns a short summary, five frequent keywords, and the original character count.

## Why it is safe

The plugin uses only deterministic local text processing. It has no runtime dependencies beyond `@deepseek-ai/dsh-tools`, makes no network requests, starts no child processes, evaluates no code, and does not read local files or credentials.

## Install

```sh
dsh plugin --profile web add -w whale-digest-0.1.0.tgz
```

## Example

Ask DSH: “Summarize this text in two sentences: …”

The model can call `whale_digest` with:

```json
{
  "text": "Long text goes here.",
  "max_sentences": 2
}
```
