# WhaleHarness 插件审核清单（站方流程，公开）

> 每个投稿按此清单逐项执行,全部通过才上架。审核过程公开(投稿箱公开可读、
> 退回原因公开、构建日志公开)。精选上架(GitHub 生态收录)与投稿箱走同一把尺子。

## 0. 收件
- 投稿箱:/srv/whaleharness-submissions/submit/<token>/<name>-<version>.tgz(只收 .tgz/.tar.gz,5MB,nginx 强制)
- 精选上架:clone 上游仓库,要求宽松许可(MIT/Apache/BSD),tarball 保留原 LICENSE 与作者信息

## 1. 结构检查(自动)
- [ ] tarball 顶层 package/ 目录(npm 格式),无 macOS ._ 元数据文件
- [ ] package.json 含 name、version、dsh.bundle.patch;scoped 包名合法
- [ ] cordis.patch.yml 加载的包名 = 自身包名(id 可不同)
- [ ] 包名不与商店现有插件冲突

## 2. 依赖审计(自动)
- [ ] peerDependencies 只列 @deepseek-ai/* 官方包
- [ ] 红线:无 child_process/execFile/spawn(工具路径一票否决)、无 eval、无凭据读取、无外网外传(URL 字面量扫描)
- [ ] RegExp .exec() 属正常 API,不误报;vendored 库(lib/assets)单独人工审
- [ ] 同功能类投稿:与商店现有插件对比工具面/持久化/安全设计,两者以上相同则退回并写明差异不足

## 3. 隔离验证(VPS Docker 沙箱)
- [ ] stage1(有网):非 root + cap-drop + no-new-privileges 安装插件与依赖
- [ ] stage2(禁网):--network none + 只读根 + 蜜罐凭据在场,boot 通过且 dump-config 出现插件行
- [ ] 恶意插件在此环节:无凭据可偷、无网络可外传,偷蜜罐即实锤
- [ ] 端到端(补齐后):审核专用限额 key + nftables 白名单代理下真实调用工具

## 4. 行为检查
- [ ] 工具输出不误导、不冒充站方;错误路径不崩溃;返回链接用 https://whaleharness.com

## 5. 可复现构建与溯源
- [ ] deploy/build_tgz.sh 打包(统一 mtime + no-xattrs,同源两次 sha256 一致)
- [ ] 条目写 source{repo,commit} 与 sha256;任何人可用同源同命令复现

## 6. 上架与通知
- [ ] tarball 上传 /srv/whaleharness/plugins/ + plugins.json 条目 + agent.json 重生成 + /p/ 短链
- [ ] 线上验证:200 + sha256 对账 + 短链 302
- [ ] 通知作者:自家 GitHub Discussions 公告 + @作者(平台级通知),写明验证事实/权利(随时下架)/更新同步

## 退回
- 未通过项写成退回原因,公开贴回投稿箱同目录 REVIEW-<name>.md,附修改建议
