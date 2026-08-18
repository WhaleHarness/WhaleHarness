# whale-store

WhaleHarness 商店浏览器（DSH 插件，host 侧）。装好后，会话里的 agent 获得三个只读工具，完成「查目录 → 看判定 → 安装」：

- `whale_store_list`（= 任务的 list_plugins）：列出全部上架插件（名称/版本/描述/安装命令），数据实时来自 https://whaleharness.com/plugins.json 。
- `whale_store_search`（= 任务的 search_plugins）：按关键词在 name/description/description_en 上做大小写不敏感文本匹配。预留 `category` 参数（plugins.json 尚无分类字段，当前忽略）。
- `whale_store_install`（= 任务的 install）：按精确名称返回审计判定（audit.json 按 source.repo 匹配）+ 完整安装命令 + 短链安装命令 + 短链 URL。

## 安全边界

- 只读两个线上数据源：`/plugins.json` 与 `/audit.json`（均为 GET，whaleharness.com）。
- 只输出安装命令文本，不代跑安装，无 child_process / eval / 凭据读取 / 动态外传。
- 数据以线上实时为准，不打包进插件。

## 安装本插件

```
dsh plugin --profile web add -w https://whaleharness.com/p/whale-store
```

## 打包（npm 风格）

```
COPYFILE_DISABLE=1 tar -czf whale-store-0.1.0.tgz -s ',^,package/,' -C whale-store package.json cordis.patch.yml README.md lib
```
