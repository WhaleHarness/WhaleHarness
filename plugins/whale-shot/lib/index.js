import { mkdir, stat } from "node:fs/promises";
import { join } from "node:path";
import { homedir } from "node:os";
import { chromium } from "playwright-core";
import { defineTool } from "@deepseek-ai/dsh-tools";

const name = "whale-shot";
const inject = ["tools"];

const DEFAULT_DESKTOP = { width: 1280, height: 720 };
const DEFAULT_MOBILE = { width: 390, height: 844 };
const MIN_SIDE = 200;
const MAX_SIDE = 3840;

function shotDir() {
  return process.env.DSH_SHOT_DIR || join(homedir(), ".dsh", "screenshots");
}

function optInt(v, def, min, max, label) {
  if (v === undefined || v === null || v === "") return def;
  const n = Math.round(Number(v));
  if (!Number.isFinite(n) || n < min || n > max) {
    throw new Error(label + " 必须在 " + min + "-" + max + " 之间，收到 " + v);
  }
  return n;
}

async function capture(args) {
  const url = String(args.url || "").trim();
  if (!/^https?:\/\//i.test(url)) {
    throw new Error("url 必填，且必须以 http:// 或 https:// 开头");
  }
  const mobile = args.mobile === true;
  const fullPage = args.full_page === true;
  const def = mobile ? DEFAULT_MOBILE : DEFAULT_DESKTOP;
  const width = optInt(args.width, def.width, MIN_SIDE, MAX_SIDE, "width");
  const height = optInt(args.height, def.height, MIN_SIDE, MAX_SIDE, "height");

  const executablePath = process.env.WHALE_SHOT_CHROMIUM || undefined;
  const browser = await chromium.launch({
    headless: true,
    ...(executablePath ? { executablePath } : {}),
  });
  try {
    const context = await browser.newContext({
      viewport: { width, height },
      deviceScaleFactor: mobile ? 3 : 1,
      ...(mobile
        ? {
            isMobile: true,
            hasTouch: true,
            userAgent:
              "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
          }
        : {}),
    });
    const page = await context.newPage();
    await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
    const dir = shotDir();
    await mkdir(dir, { recursive: true });
    const file = join(
      dir,
      "whale-shot-" + Date.now() + "-" + (mobile ? "mobile" : "desktop") + "-" + width + "x" + height + ".png"
    );
    await page.screenshot({ path: file, fullPage });
    const st = await stat(file);
    return {
      path: file,
      url,
      mode: mobile ? "mobile" : "desktop",
      width,
      height,
      device_scale_factor: mobile ? 3 : 1,
      full_page: fullPage,
      bytes: st.size,
    };
  } finally {
    await browser.close();
  }
}

const shotTool = defineTool({
  name: "whale_screenshot",
  description:
    "Take a screenshot of a URL with a headless browser (Playwright) and save it as a PNG. Supports desktop and mobile emulation (viewport + deviceScaleFactor). Call it when the user wants to capture how a web page looks. Returns the PNG file path on disk.",
  parameters: {
    url: {
      type: "string",
      required: true,
      description: "The URL to screenshot. Must start with http:// or https://."
    },
    width: {
      type: "number",
      description: "Viewport width in pixels, 200-3840. Defaults to 1280 (desktop) or 390 (mobile)."
    },
    height: {
      type: "number",
      description: "Viewport height in pixels, 200-3840. Defaults to 720 (desktop) or 844 (mobile)."
    },
    mobile: {
      type: "boolean",
      description: "Emulate a mobile device (isMobile + touch + deviceScaleFactor 3). Defaults to false."
    },
    full_page: {
      type: "boolean",
      description: "Capture the full scrollable page instead of just the viewport. Defaults to false."
    }
  },
  output: {
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        path: { type: "string", required: true },
        url: { type: "string", required: true },
        mode: { type: "string", required: true },
        width: { type: "number", required: true },
        height: { type: "number", required: true },
        device_scale_factor: { type: "number", required: true },
        full_page: { type: "boolean", required: true },
        bytes: { type: "number", required: true }
      }
    },
    render(_args, value) {
      const size = value.bytes >= 1048576
        ? (value.bytes / 1048576).toFixed(2) + " MB"
        : (value.bytes / 1024).toFixed(1) + " KB";
      return [{
        type: "text",
        text:
          "📸 截图完成（" + value.mode + " " + value.width + "x" + value.height + "@" + value.device_scale_factor + "x，全页=" + value.full_page + "）\n" +
          "文件：" + value.path + "\n" +
          "大小：" + size + "\n" +
          "URL：" + value.url
      }];
    }
  },
  async execute(args) {
    return await capture(args);
  }
});

function apply(ctx) {
  ctx.tools.register(shotTool);
}

export { apply, inject, name };
