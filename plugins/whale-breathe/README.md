# whale-breathe

> WhaleHarness 鲸鱼呼吸法 —— 给 DeepSeek Harness 装一口深海里的新鲜空气。

`whale-breathe` 是一个 DSH（DeepSeek Harness）插件，向模型注册一个名为
`whale_breathe` 的工具：在用户焦虑、过载或只是需要在任务之间喘口气时，
返回一段鲸鱼节奏的呼吸引导。

## 特点

- **纯本地、零副作用**：不发起任何网络请求，不使用 `eval` / `child_process`，
  不读取凭据或文件系统。符合 WhaleHarness 投稿「安全红线」。
- **可配置**：可选 `minutes`（1–10，默认 1）和 `note`（一句话备注）。
- **可逆挂载**：作为 Cordis bundle 插入，卸载时随插件树一并回卷。

## 安装

```bash
dsh plugin --profile web add -w https://whaleharness.com/plugins/whale-breathe-0.1.0.tgz?src=install
```

或对模型说：「帮我做个一分钟的鲸鱼呼吸。」

## 示例输出

```
鲸鱼呼吸法 · 1 分钟

跟着鲸群的节奏慢下来，循环下面四拍：
吸气 4 秒，想象鲸鱼缓缓上浮。
屏息 4 秒，停在温柔的水层里。
呼气 6 秒，像鲸鱼潜回深处。
停顿 2 秒，听一听海面之下的安静。

深海不赶时间，你也不必把呼吸压缩成任务。
```

## 许可证

MIT
