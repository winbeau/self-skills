---
name: set-config
description: Apply and troubleshoot the user's personal Claude Code settings baseline. Use when the user asks to set, restore, audit, or persist their Claude config; enforce global bypassPermissions while preserving permission rules; diagnose settings that revert after restart, deployment, shell startup, or provider switching; or investigate cc-switch writers and backups. This is a personal preset and incident runbook. Delegate generic settings.json editing, scopes, hooks, plugins, MCP, and schema mechanics to $update-config.
---

# set-config

这是用户个人 Claude Code 配置基线和持久化排障手册。它负责说明**目标状态、已知失败模式、外部重写源和验证顺序**；不要复制一套通用 `settings.json` 编辑器。

所有实际配置修改先调用 `$update-config`，由它负责选择 scope、先读后改、合并 JSON、处理 hooks / plugins / MCP / env，以及校验配置。本 Skill 只向它提供个人基线和额外的持久化检查。

## 个人全局基线

默认目标文件是 `~/.claude/settings.json`，按以下不变量做**合并**，不可整文件替换：

```text
permissions.defaultMode = "bypassPermissions"
skipDangerousModePermissionPrompt = true
permissions.allow = 原样保留
其他 permissions 字段 = 原样保留
其他顶层字段 = 原样保留
```

具体规则：

- 保留完整的 `permissions` 对象，特别是 `allow`、`ask`、`deny`、`additionalDirectories` 和未知字段。
- 不要把本机当前 allowlist 写死成模板，也不要为了应用 preset 清空或扩充它。
- 不要用 `skipAutoPermissionPrompt` 选择权限模式；它只记录 Auto Mode 提示的选择状态。
- 不要创建 `~/.claude/settings.local.json`。Claude Code 没有这个 user-global-local scope。
- 用户若明确要求项目级设置，交给 `$update-config` 按项目 scope 处理，不要把个人全局 preset 强塞进项目文件。

## Settings scope 地图

```text
用户全局：    ~/.claude/settings.json
项目共享：    <project>/.claude/settings.json
项目本地个人：<project>/.claude/settings.local.json
```

排障时不仅看某一个文件，还要用 `/status`、`/permissions` 或当前版本提供的等价界面确认实际加载源。权限规则可能来自多个 scope；不要只凭某个 scalar 的值推断完整 resolved policy。

## 不要混淆的权限概念

- `dontAsk` 不是 Bypass。它不再弹窗，但未预先允许的操作会被拒绝。
- `bypassPermissions` 跳过普通工具权限确认，但不代表解除平台安全约束、外部发布确认或所有强制交互。
- `skipDangerousModePermissionPrompt: true` 记录用户已接受 Bypass 的危险模式提示；它本身不选择 Bypass。
- `skipAutoPermissionPrompt` 记录 Auto Mode 相关提示状态；它本身既不选择 Auto，也不选择 Bypass。
- `permissions.allow` 与 Auto Mode 的内容分类是不同层。扩大 allowlist 不能修复内容分类导致的拒绝。
- Bypass 下仍要保留 allowlist：它在切换到其他模式、审计和未来配置变更时仍有价值。
- `permissions.defaultMode` 是会话启动默认值，不保证 Plan Mode 退出后自动恢复。退出 Plan 时应在审批界面选择 **Yes, and bypass permissions**；新会话也应以允许 Bypass 的配置启动。

## 应用或修复流程

1. 判断请求是个人全局 preset，还是普通项目级配置。
2. 调用 `$update-config`，读取目标文件后再修改。
3. 只检查所需的非敏感字段，不输出完整 `env`、provider、hook 或 MCP 配置。
4. 合并个人基线，保留数组、未知对象和无关顶层字段。
5. 若用户报告“重启后又变回去了”，不要在 live file 修改成功后就结束；继续审计所有 writer。
6. 修复持续写入源及其 durable state，使它们和 live settings 使用同一政策。
7. 校验 JSON、resolved settings 和关键字段。
8. 完整重启相关 controller，再启动一个全新的 Claude Code 会话验证。
9. 报告最终 mode、危险提示标志、allowlist 数量和检查过的重写边界；不要打印密钥或原始配置。

## Reset-source 审计

按这个顺序定位：

1. `/status` 中的 active settings sources 和 managed policy。
2. `/permissions` 中 resolved rules 及来源。
3. Claude 启动参数、alias/function、`--settings`、`--permission-mode` 和有关环境变量。
4. `deploy.sh`、bootstrap 脚本、dotfiles 管理器、systemd/user service 等配置写入者。
5. shell 启动文件。先区分它是直接写 settings，还是只启动另一个 controller。
6. provider switch/controller 的实际可执行文件；用 `command -v` 定位后阅读实现，不要猜固定路径。
7. controller 的数据库、common config、live backup、restore state。若这些仍保存旧值，只改 live file 一定会复发。
8. controller 完整 restart、新 login shell、Claude Code 全新会话。

值在部署、provider 切换、shell 启动或 controller 重启后复原时，读取 [settings troubleshooting history](references/settings-troubleshooting.md)。

## Secret handling

- 不打印整个 `settings.json`；其中可能有 token、provider route、hooks 或 MCP credential。
- 不 dump CC Switch provider 行、common config 或 backup 的原始 JSON。
- 只输出 mode、布尔标志、allowlist 数量、字段是否存在和必要的 source 名称。
- 不把 token、provider ID、route URL 或当前 allowlist 内容固化进 Skill。
- 文档和命令优先使用 `$HOME`、`<project>` 和 discovery commands，避免不必要的绝对安装路径。
