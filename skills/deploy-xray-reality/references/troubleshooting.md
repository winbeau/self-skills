# 故障排查

排查顺序固定：**服务是否在跑 → 流量是否到达主机 → 握手是否成功 → 转发是否正常**。跳步会浪费大量时间，尤其不要在客户端参数上反复调整，而实际上流量根本没到服务器。

## 第 1 层：服务状态

```bash
systemctl is-active xray
systemctl status xray --no-pager -l
journalctl -u xray -n 50 --no-pager
ss -tlnp | grep xray
/usr/local/bin/xray run -test -c /usr/local/etc/xray/config.json
```

| 现象 | 原因与处理 |
|---|---|
| `Active: failed`，日志 `permission denied` | unit 缺 `AmbientCapabilities=CAP_NET_BIND_SERVICE`，非 root 用户无法绑定 1024 以下端口 |
| `address already in use` | 端口被占。`ss -tlnp` 找出占用进程，换端口或停掉对方 |
| 启动即退出，日志有 JSON 报错 | 配置语法错。`xray run -test` 会给出具体行 |
| `failed to read config` | 配置文件权限不对，`xray` 用户读不到。`chown xray:xray` |

## 第 2 层：流量是否到达

这一层最常被跳过，也最常是真凶。判据是**服务端日志有没有出现 `accepted`**。

```bash
journalctl -u xray -f
# 另一侧让客户端发起连接，观察是否有记录
```

日志完全没有记录 = 流量没到主机。按这个顺序查，不要颠倒：

1. **VPS 面板安全组**。云厂商的安全组独立于主机防火墙，是最常见的拦截点。检查入站是否放行了目标端口的 TCP。
2. **云网络 ACL / VPC 规则**（如果有）。
3. **主机防火墙**：

```bash
sudo ufw status
sudo iptables -L INPUT -n --line-numbers
sudo nft list ruleset 2>/dev/null | head -40
```

4. **从外部验证端口可达**。在另一台机器上：

```bash
nc -vz -w 5 <server_ip> 443
curl -sv --max-time 8 telnet://<server_ip>:443
```

连接被拒绝（RST）说明包到了主机但没有服务在听；超时无响应说明被中途丢弃，问题在防火墙或链路。

## 第 3 层：握手

服务端有 `accepted` 但客户端连不通，问题在参数或 dest。

服务端和客户端必须严格一致的三项：

| 服务端字段 | 客户端字段 | 说明 |
|---|---|---|
| `realitySettings.serverNames[0]` | `sni` | 不一致直接握手失败 |
| `privateKey` 对应的公钥 | `pbk` | 客户端用公钥，不是私钥 |
| `shortIds[]` 中的某一项 | `sid` | 必须是服务端列表里存在的值 |

核对公钥是否与服务端私钥匹配：

```bash
sudo /usr/local/bin/xray x25519 -i "$(sudo grep -oP '"privateKey":\s*"\K[^"]+' /usr/local/etc/xray/config.json)"
```

输出的公钥必须与链接里的 `pbk` 完全一致。

其他握手类问题：

- **dest 从服务器不可达**，或 dest 停止支持 TLS 1.3 / X25519。重跑 `scripts/probe_dest.sh` 复核。
- **客户端时间偏差过大**。REALITY 对时间敏感，偏差超过几分钟会失败。`timedatectl` 检查两端。
- **客户端版本过低**。v2rayN 需要 6.x 以上；低版本没有 REALITY 或 Vision 选项，导入链接时会静默丢字段。导入后检查节点详情里 `flow` 是否为 `xtls-rprx-vision`。

## 第 4 层：能连但不正常

| 现象 | 排查 |
|---|---|
| 速度远低于服务器带宽 | 确认 BBR 生效：`sysctl net.ipv4.tcp_congestion_control`；确认有 AES-NI：`grep -o aes /proc/cpuinfo \| head -1` |
| 延迟正常但吞吐上不去 | 多为链路拥塞或 QoS，不是配置问题。换时段对比，或测同机房其他 IP |
| 部分网站不通 | 服务端路由规则拦了。检查 `routing.rules`，本 Skill 默认屏蔽了私有地址和 BitTorrent |
| UDP / QUIC 不通 | 检查客户端是否开了 UDP 转发；部分网络会整体丢弃 QUIC，可在客户端禁用 QUIC 回落 TCP |
| 时通时断，且服务端日志无记录 | 服务器 IP 可能已被针对性阻断。换 dest 无效，需要换 IP |

## 回滚

配置变更前脚本都会留带时间戳的备份：

```bash
ls -la /usr/local/etc/xray/config.json.bak.*
sudo cp -a /usr/local/etc/xray/config.json.bak.<时间戳> /usr/local/etc/xray/config.json
sudo /usr/local/bin/xray run -test -c /usr/local/etc/xray/config.json
sudo systemctl restart xray
```

## 完全卸载

```bash
sudo systemctl disable --now xray
sudo rm -f /etc/systemd/system/xray.service /etc/sysctl.d/99-xray-tune.conf
sudo systemctl daemon-reload
sudo rm -rf /usr/local/etc/xray /usr/local/share/xray /var/log/xray /usr/local/bin/xray
sudo userdel xray 2>/dev/null || true
sudo sysctl --system >/dev/null
```
