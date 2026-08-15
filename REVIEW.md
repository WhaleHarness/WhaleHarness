# WhaleHarness 审查方法（Review Method）

本文件是 whaleharness.com 审核制商店与生态审计的公开方法说明。
审查器源码:tools/review-submission.py(本仓库,任何人可复现)。
审计数据:https://whaleharness.com/audit.json(机器可读,条目含 repo/version/commit/verdict/issues)。

## 裁决分档(2026-08-15 起)

- RED-LINE(安全红线):subprocess/eval/网络外传/敏感路径——红色标记
- FORMAT-ISSUE(打包格式):版本号格式、patch 声明、结构、required:false——橙色标记
- EXCLUDED(官方包豁免):仅当仓库 slug 以 deepseek-ai/ 开头(不信包名自声明,防 squatting)
- 红线优先:同包两类并存按 RED-LINE 计

## subprocess 红线:host 声明门 + 调用形态

- 声明门:package.json 的 dsh.runtime 需为 "host"(或数组含 "host");未声明而使用 child_process → RED-LINE
- 过门后按调用形态分档:
  - 合法(降 warning 人工复核):spawn/spawnSync/execFile/execFileSync/fork 固定 argv 形态,无 shell:true、无 bash/sh -c、无命令串拼接/模板插值
  - 可疑(维持 RED-LINE):exec/execSync 动态串、shell:true、bash/sh -c、命令串插变量或拼接
- 外传关联:同一源码文件内 child_process 与 fetch/http.request 到非本站域并存 → 直接 RED-LINE,无论声明门

## 可复现与可申诉

- 同一 tarball + 本审查器,任何人重跑得同一结论;结论绑定 repo+version+commit
- 裁决可申诉:在 https://github.com/WhaleHarness/WhaleHarness/discussions 提出,
  附复现证据;曾有误判被作者复现纠正(Anionex/dsh-vision-toolkit#33)
- 被标 FORMAT-ISSUE 的修复指南:https://whaleharness.com/audit-fixes.html

## 已知边界(诚实声明)

- 静态审查不执行插件代码;boot/端到端验证只对商店在架插件执行(沙箱+蜜罐)
- 调用形态判定是启发式,不是形式化证明;人工复核仍是终审
