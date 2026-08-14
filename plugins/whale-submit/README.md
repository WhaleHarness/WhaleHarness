# whale-submit

在 DSH 会话里投稿自己的插件到 WhaleHarness。

装好后，模型获得 `whale_submit` 工具：把你的插件目录打包成 tarball，直接 PUT 到 WhaleHarness 公开投稿箱。审核公开透明。

## Install

```sh
dsh plugin --profile web add -w https://whaleharness.com/plugins/whale-submit-0.1.0.tgz?src=install
```

## Usage

会话里说：「帮我把 /path/to/my-plugin 投稿到 WhaleHarness」，或直接让模型调用：

`whale_submit(path="/path/to/my-plugin", name="my-plugin", version="0.1.0")`

要求：目录里有 `package.json`；包名小写字母/数字/连字符；tarball ≤ 5MB。
