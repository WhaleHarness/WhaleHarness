# whale-status

在 DSH 会话里给 WhaleHarness 做体检：HTTPS、DNS、TLS 证书剩余天数、全部插件 tarball 的 sha256 完整性。

## Install

```sh
dsh plugin --profile web add -w https://whaleharness.com/plugins/whale-status-0.1.0.tgz?src=install
```

## Usage

会话里说「检查一下 WhaleHarness 状态」，或让模型调用 `whale_status`。

全部检查只用 Node 内置模块（fetch / dns / tls / crypto），无外部依赖。
