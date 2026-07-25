# Claude Code settings troubleshooting history

本参考保存一次真实配置事故中可复用的失败经验和持久化修复方法。它不是完整 settings schema；通用修改仍交给 `$update-config`。

## 支持的 settings 位置

| Scope | 有效路径 | 用途 |
|---|---|---|
| 用户全局 | `~/.claude/settings.json` | 对该用户所有项目生效 |
| 项目共享 | `<project>/.claude/settings.json` | 可随项目共享 |
| 项目本地个人 | `<project>/.claude/settings.local.json` | 只在该项目、该用户本地生效 |

`~/.claude/settings.local.json` **不是**受支持的“全局本地设置”。把 Bypass 写在那里不会覆盖有效的用户全局配置，应在确认无独有内容后删除这个冗余文件。

## 失败模式与原因

| 失败做法 | 为什么失败 | 正确经验 |
|---|---|---|
| 创建或修改 `~/.claude/settings.local.json` | 不存在这个 user-global-local scope | 用户全局写 `~/.claude/settings.json` |
| 把 `dontAsk` 当作无限制模式 | 它会拒绝原本需要询问且未预先允许的调用 | 需要跳过普通权限询问时选择 `bypassPermissions` |
| 只设置 `skipAutoPermissionPrompt` | 该字段记录提示选择，不改变 `defaultMode` | 显式设置 `permissions.defaultMode` |
| 不断扩大 `permissions.allow` 来解决 Auto Mode 拒绝 | 静态工具权限和 Auto Mode 内容分类是不同层 | 先识别拒绝来自哪一层 |
| 只改 live `~/.claude/settings.json` | 外部 controller 仍从 durable state 写回旧值 | 找出并修复所有 writer 和持久化副本 |
| 看到 `.zshrc` 启动 CC Switch 就认定它直接改配置 | shell 文件可能只是 trigger，真正写入逻辑在 controller | 顺着调用链定位实际 executable |
| 修复 controller 代码，却不检查 common config / backup | stop、restore、provider transition 仍可能恢复旧 policy | 代码、common config 和 restore state 一起验证 |
| repository deployer 仍写 `auto` | 下次部署会覆盖已经修好的 live policy | 让所有 bootstrap/deploy writer 使用同一 baseline |
| 修改当前会话的文件后立即判断成功 | 权限模式和 controller 状态可能只在重启边界暴露问题 | 做 controller restart、login shell 和 fresh session 验证 |

## 已验证的本地事故链

本机曾出现如下链路：

1. 有效全局文件仍是 `permissions.defaultMode: "auto"`，而 Bypass 被误写在不生效的 `~/.claude/settings.local.json`。
2. `/config` 一度切到 `dontAsk`，但这不是所需模式。
3. 有效全局文件改成 `bypassPermissions` 后，新会话确认可以进入 Bypass。
4. `.zshrc` 中的健康检查会在进程、代理端口或 route 检查失败时启动 `cc-switch-ctl`。
5. `.zshrc` 本身没有写权限模式；真正的 reset source 是 controller 内部强制写入 `auto` 的函数。
6. controller 又把该 policy 同步到 SQLite common config 和 live backup，因此单改 live file 无法持久。
7. 修复时将 controller policy 改为 `bypassPermissions`，设置并同步 `skipDangerousModePermissionPrompt: true`，同时保留已有 allowlist。
8. 随后运行完整 controller restart，检查 live settings、common config、backup、代理监听和 allowlist，全部保持一致。
9. 无效的 `~/.claude/settings.local.json` 在确认内容重复后删除。

该经验要**通过发现路径复用**，不要假定每台机器都有相同安装位置：

```bash
command -v cc-switch-ctl
```

定位后阅读 controller 声明的 settings、数据库和 backup 路径，再决定检查方式。如果 controller 不存在，就跳过 CC Switch 专项步骤。

## Durable repair order

```text
live user settings
→ repository deploy/bootstrap writers
→ controller implementation
→ controller common configuration
→ controller restore/live-backup state
→ shell/service triggers
→ controller full restart
→ new login shell
→ fresh Claude Code session
```

不要跳过中间层。越靠前的成功只说明 live file 暂时正确，越靠后的验证才说明配置能跨重启持续存在。

## Redacted diagnostics

### 检查 live settings 的选定字段

Python 版本不会输出 `env`、provider route 或 allowlist 内容：

```bash
python3 - <<'PY'
import json
from pathlib import Path

path = Path.home() / ".claude" / "settings.json"
data = json.loads(path.read_text(encoding="utf-8"))
permissions = data.get("permissions")
if not isinstance(permissions, dict):
    permissions = {}
allow = permissions.get("allow")
print("settings:", path)
print("defaultMode:", permissions.get("defaultMode", "<unset>"))
print("allow_count:", len(allow) if isinstance(allow, list) else "<not-array>")
print("skipDangerousModePermissionPrompt:", data.get("skipDangerousModePermissionPrompt", "<unset>"))
print("skipAutoPermissionPrompt:", data.get("skipAutoPermissionPrompt", "<unset>"))
PY
```

等价的 `jq` 选定字段检查：

```bash
jq '{
  defaultMode: .permissions.defaultMode,
  allow_count: (if (.permissions.allow | type) == "array" then (.permissions.allow | length) else null end),
  skipDangerousModePermissionPrompt,
  skipAutoPermissionPrompt
}' "$HOME/.claude/settings.json"
```

### 检查 controller 是否仍硬编码旧模式

先发现路径，再只搜索 policy 相关语句：

```bash
ctl="$(command -v cc-switch-ctl)"
grep -nE 'defaultMode|skipDangerousModePermissionPrompt|common_config|backup' "$ctl"
```

不要因此假定每个匹配都错误；结合函数调用链判断 start、stop、restore、sync 分支。

### 检查 CC Switch durable state 的选定 JSON path

数据库路径和表名必须先从 controller 实现确认。对于已知本地 schema，可只查询所需字段，不输出原始 JSON：

```bash
sqlite3 -readonly "$DB" \
  "SELECT json_extract(value, '$.permissions.defaultMode'),
          json_extract(value, '$.skipDangerousModePermissionPrompt')
     FROM settings
    WHERE key='common_config_claude';"

sqlite3 -readonly "$DB" \
  "SELECT json_extract(original_config, '$.permissions.defaultMode'),
          json_extract(original_config, '$.skipDangerousModePermissionPrompt')
     FROM proxy_live_backup
    WHERE app_type='claude';"
```

若 schema 不同，重新从 controller 的 SQL 和字段声明推导，不能猜测或 dump 整表。

## End-to-end persistence checklist

- [ ] `~/.claude/settings.json` 是有效 JSON。
- [ ] `permissions.defaultMode == "bypassPermissions"`。
- [ ] `skipDangerousModePermissionPrompt == true`。
- [ ] `permissions.allow` 仍是数组且数量符合修改前基线。
- [ ] `permissions.ask`、`deny` 和未知字段未被意外删除。
- [ ] `~/.claude/settings.local.json` 不存在，或明确知道为何存在且未把它误当全局 scope。
- [ ] repository deploy/bootstrap 不再写回 `auto`。
- [ ] controller implementation 不再强制旧模式。
- [ ] controller common config 和 restore/backup state 保存相同 policy。
- [ ] controller 完整 restart 后 live settings 不变。
- [ ] 新 login shell 触发 startup logic 后 live settings 不变。
- [ ] Claude Code 完全退出并重启后，以 Bypass Permissions 启动。
- [ ] 从 Plan Mode 退出时选择 **Yes, and bypass permissions**，当前会话回到所需模式。
- [ ] `/status` 和 `/permissions` 未显示意外的 managed/project override 或 ask/deny 来源。

## 成功报告格式

最终只报告：

```text
active mode: bypassPermissions
skip dangerous prompt: true
allowlist: preserved (<count> entries)
live settings: valid
persistent writers checked: <names>
restart boundaries passed: <names>
```

如果有任何步骤未执行或失败，明确说明，不要用“已彻底解决”代替证据。
