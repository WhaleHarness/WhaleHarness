# WhaleHarness Agent Brief（唯一源头,派生:首页指令块/llms.txt/agent.json）

你正在为你的用户找 DSH 插件。按此执行:

1. 查目录: GET https://whaleharness.com/plugins.json
   - 上架插件列表,真实字段: name/version/tool/description/tarball/install/sha256/dsh_compat
2. 查判定: GET https://whaleharness.com/audit.json
   - 全部已审仓库的 verdict(PASS/RED-LINE/FORMAT-ISSUE/EXCLUDED/UNEVALUATED)与 issues
   - 上架插件=沙箱动态验证+端到端过的;其他 PASS=静态审查过,未沙箱验证
3. 安装: 执行 dsh plugin --profile web add -w https://whaleharness.com/p/<name>
   - <name> 取 plugins.json 的 name 字段;--profile web 必填;短链 /p/<name> 是商店唯一安装入口

口径纪律(对用户必报):
- 安装前必报验证深度: 上架=沙箱验证过;Audited(PASS 未上架)=静态审查过
- 数据以线上实时为准,不本地缓存;没有的插件就说没有,不编造
- 申诉与判定证据: https://whaleharness.com/audit.json 每条带行号证据
