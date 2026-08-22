# whale-shot

在 DSH 会话里用无头浏览器（Playwright）给任意 URL 截图，存成 PNG 并返回文件路径。支持桌面 / 移动模拟。

## Install

```sh
dsh plugin --profile web add -w https://whaleharness.com/plugins/whale-shot-0.1.0.tgz?src=install
```

安装后需准备 Chromium（二选一）：

```sh
# 方式 A：playwright 自带的 chromium
npx playwright install chromium

# 方式 B：复用系统 chrome/chromium，用环境变量指定路径
export WHALE_SHOT_CHROMIUM=/usr/bin/google-chrome
```

## Usage

装好后模型获得 `whale_screenshot` 工具，会话里说「截一下 https://whaleharness.com」，或直接调用：

```
whale_screenshot(url="https://whaleharness.com")
whale_screenshot(url="https://whaleharness.com", mobile=true)            # 移动模拟（390x844@3x，触屏+移动 UA）
whale_screenshot(url="https://whaleharness.com", width=1920, height=1080) # 自定义视口
whale_screenshot(url="https://whaleharness.com", full_page=true)          # 整页截图
```

## 参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| url | string | 是 | 目标 URL，必须 http(s):// 开头 |
| width | number | 否 | 视口宽度，200-3840，桌面默认 1280、移动默认 390 |
| height | number | 否 | 视口高度，200-3840，桌面默认 720、移动默认 844 |
| mobile | boolean | 否 | 移动模拟（isMobile + 触屏 + deviceScaleFactor 3），默认 false |
| full_page | boolean | 否 | 整页截图，默认 false（只截视口） |

## 输出

工具返回 PNG 的绝对路径（默认 `~/.dsh/screenshots/whale-shot-<ts>-<mode>-<w>x<h>.png`，可用 `DSH_SHOT_DIR` 覆盖目录）。宿主能直接读取该路径的 PNG 文件。

## 注意

- 依赖 `playwright-core`（轻量，不带浏览器），Chromium 需单独准备（见上）。
- 截图存本地磁盘，不自动上传。
