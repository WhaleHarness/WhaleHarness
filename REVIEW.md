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
- 审查的扫描面 = 打包收集规则纳入的源码(现规则:package.json / cordis.patch.yml / LICENSE / README* / lib/)。代码只放在 src/、dist/ 或仓库根级而未被收集时,该包等于空扫——**这时的 PASS 只表示「未发现红线」,不等于「审过代码」**。我们已**全量实测**此缺口(2026-09-15,对 1,246 条 PASS 逐条复跑):**661 条(53.0%)** 属此情形(打包件里一行代码都没有——src/ 509 + 根级 *.js 117 + 其他目录 31 + dist/ 3 + 完全无代码 1);把真实源码补上扫描面后,其中 **208 条(31.5%)** 变 RED-LINE——但**「空扫」不等于「有问题」**,另外 453 条补上源码后仍是 PASS,**正确的读法是「我们没审到」,不是「它有红线」**。另需说明:**PASS 是生成时点结论**,规则后续变更不回溯存量判定(2026-09-13 扩 eval 语义族即为一例)。修法(把收集面与扫描面对齐)涉及已发布判定,公开前先做影响面评估与灰度。
## 已知误伤的规模(2026-09-16 补充)

两轮独立复核后,我们**已识别的历史误伤约 596 条**:

- **约 484 条**——非插件仓库被当成插件投稿来审(该线抽样命中率约 73%)
- **91 条**——合法的 semver 预发布版本(如 `0.1.0-rc.1`)被拒(该线约 68%)
- **21 条**——敏感路径规则把「文本里提到某个路径」当成「真的读取了它」(该类仅因此判红的 33 条里,逐条复核确认 21 条为文本误伤)
- **7 个已上架插件**——2026-09-13 我们扩张一条检测规则(eval 语义族)后,用当前审查器复跑**已不再是 PASS**;而它们的货架状态与 plugins.json **均未改动**
- **661 条 PASS(53.0%)**——打包面窄于扫描面,**根本没扫到代码**(见上节);补上真实源码后其中 **208 条**变 RED-LINE,**其余 453 条仍 PASS**

**这些计数不改变任何既有判定**——它们是披露,不是改判。另需说明:其中一条判定(合法预发布版本)自 **2026-08-29** 起挂了 **16 天**才被复核发现,原因是**判定只增不改、规则修复不回溯存量**。

**如果你认为自己在其中**:请在 https://github.com/WhaleHarness/WhaleHarness/discussions 提出,附仓库名与 commit,我们会**逐条复核并公开结论**。
