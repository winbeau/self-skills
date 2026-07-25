---
name: deploy-xray-reality
description: Deploy a fastest-path Xray VLESS + XTLS-Vision + REALITY node on a Linux VPS and emit a ready-to-import v2rayN share link. Covers host probing, REALITY dest selection and validation, key generation, a hardened non-root systemd service, BBR tuning, end-to-end throughput verification, additional client provisioning, and failure diagnosis. Use when the user asks to 搭建/注册/部署 Xray, set up a VLESS REALITY node, turn a VPS into a proxy server, produce a v2rayN or v2rayNG 链接/订阅, add users to an existing Xray node, or debug a REALITY node that will not connect. Do not use for Clash or sing-box configuration, Shadowsocks-only setups, certificate- and CDN-based transports such as WebSocket+TLS or gRPC, or Windows client-side application setup.
---

# Xray VLESS + REALITY 节点部署

在一台 Linux VPS 上部署 VLESS + XTLS-Vision + REALITY，并交付可直接导入 v2rayN 的分享链接。

选这个组合是因为它在「最快」这个目标下最优：Vision 走 splice 零拷贝、只有一层 TLS、不经 CDN 中转。同时 REALITY 借用真实站点的证书，不需要域名和证书申请，部署路径最短。

用户说「最快的方案」时，默认理解为**传输性能最快**，而不是「部署步骤最省」。两者在这里恰好一致，不必追问。

## 不适用

- 客户端侧配置（v2rayN/v2rayNG 的界面操作、路由规则、分流），本 Skill 只交付链接。
- 需要域名和证书的传输方式（WebSocket+TLS、gRPC、CDN 中转）。这些比 REALITY 慢，只在必须过 CDN 或必须伪装成网站时才考虑。
- Clash、sing-box、Shadowsocks 专用配置。
- 已有面板（x-ui、3x-ui、Marzban）的机器，改用面板自身的增删逻辑，不要用本 Skill 覆盖配置。

## 执行位置

先确认目标机器是当前 shell 所在主机还是远程主机：

- **就是本机**：直接执行本 Skill 的脚本。
- **远程主机**：先用 `tmux-ssh-remote` Skill 建立持久会话，再在该会话内执行同一套流程。不要用一次性 `ssh host "cmd"` 串联多步，中间状态会丢。

## 硬约束

1. **不要自己跑需要密码的 `sudo`。** 先测 `sudo -n true`。免密就直接装；需要密码就把完整命令交给用户，让其在输入框内以 `! sudo bash <脚本路径>` 执行，输出会回到对话里。不要尝试猜密码或用 `echo | sudo -S`。
2. **不要跳过 `xray run -test`。** Xray 会对危险的 dest 直接告警（如 apple/icloud 系可能导致服务器 IP 被封），这是选 dest 的权威判据。
3. **交付前必须实测。** 只看 `systemctl is-active` 不够，必须跑通一次真实握手和吞吐对比。
4. **私钥不出服务器。** `privateKey` 只写进服务端配置；客户端链接里只放 `pbk`（公钥）。不要把私钥回显给用户或写进文档。
5. **分享链接内含 UUID，等于账号凭证。** 交付时明确说明不能公开分发，并说明多人使用应各自分配 UUID。

## 工作流

### 1. 探测主机

```bash
whoami; id -u; uname -m; cat /etc/os-release | head -3
which xray v2ray sing-box
systemctl list-units --type=service | grep -iE 'xray|v2ray|sing-box'
ss -tlnp
curl -s -4 https://api.ipify.org; echo
curl -s -6 --max-time 5 https://api64.ipify.org; echo
curl -s https://ipinfo.io
sysctl net.ipv4.tcp_congestion_control
```

需要确认的事实：架构（脚本只覆盖 x86_64 与 arm64）、是否已有代理服务在跑、目标端口是否被占用、公网 IPv4、是否有 IPv6、机房位置、BBR 是否已开。

已有 Xray 在跑时先问清楚是覆盖还是新增节点，不要直接改现有配置。

### 2. 选 REALITY dest

```bash
scripts/probe_dest.sh
```

脚本对候选站点检查 TLS 1.3、X25519 密钥交换、HTTP/2 ALPN 和握手延迟，按延迟排序，并对已知风险域名打标。

选择标准，按优先级：

1. 必须同时满足 TLS 1.3 + X25519 + h2，缺一不可。
2. 未被标记为风险（`xray run -test` 告警的域名一律排除）。
3. 从**服务器**看延迟最低，通常是同区域的站点。
4. 在客户端所在地区不被封锁——SNI 本身要看起来合理。

延迟差在 50ms 以内时按稳定性选，不必死抠最低值。选定后在第 3 步的 `xray run -test` 里复核一次告警。

详见 [references/dest-selection.md](references/dest-selection.md)。

### 3. 生成密钥与配置

```bash
scripts/setup_reality.sh --dest addons.mozilla.org --workdir ./xray-build --remark "LA-Reality"
```

脚本会下载对应架构的 Xray 二进制、生成 UUID / x25519 密钥对 / shortId、渲染服务端配置、跑 `xray run -test` 校验，并输出 `params.env` 与 `share-link.txt`。

可选参数：`--port`（默认 443）、`--uuid`（默认随机）、`--server-ip`（默认自动探测）。

**保持 443 端口。** Xray 对非 443 端口会直接告警 `Listening on non-443 ports may get your IP blocked by the GFW`——REALITY 的伪装前提就是流量看起来像访问 443 上的正常 HTTPS 站点，换端口会破坏这一点。只有 443 已被占用且无法腾出时才改，并向用户说明代价。

`xray run -test` 出现任何告警都要先解决再继续：dest 相关的回到第 2 步换 dest，端口相关的改回 443。

### 4. 安装服务

需要 root。按硬约束 1 处理提权：

```bash
sudo bash scripts/install_service.sh --workdir ./xray-build
```

脚本负责：二进制装到 `/usr/local/bin/xray`，配置装到 `/usr/local/etc/xray/config.json`（模式 600），建独立 `xray` 系统用户，写 systemd unit 并用 `CAP_NET_BIND_SERVICE` 绑定 443 而非以 root 运行，开启 BBR + fq 及 TCP 缓冲区调优，ufw 处于 active 时放行端口，最后 enable 并启动。

已存在配置会带时间戳备份，不会静默覆盖。

### 5. 端到端验证

```bash
scripts/verify_reality.sh --workdir ./xray-build
```

脚本在本地起一个临时客户端连自己的服务端，验证握手、出口连通性，并做经代理与直连的吞吐对比，结束后自动清理。

判读要点：

- **在服务器本机跑时，经代理的出口 IP 必然等于服务器 IP**，这不能证明转发正确。真正的判据是握手成功 + 吞吐接近直连 + 服务端日志出现 `accepted` 记录。
- 代理开销正常在 5% 以内。开销明显偏大先查 CPU 是否被 AES 软件加密拖住（`grep -o aes /proc/cpuinfo | head -1` 确认有 AES-NI）。
- 本机验证**不覆盖公网可达性**。交付时必须明确说明这一点，并提示防火墙排查顺序：VPS 面板安全组 → 云厂商网络 ACL → 主机 ufw/iptables。

### 6. 交付

给出分享链接、参数对照表，以及：

- 已验证什么、未验证什么（尤其是公网可达性）。
- 客户端版本要求：v2rayN 6.x 及以上才支持 `xtls-rprx-vision` + REALITY，旧版导入会丢参数。
- 凭证安全提示。
- 运维命令：改配置 `/usr/local/etc/xray/config.json`，重启 `sudo systemctl restart xray`，看日志 `sudo journalctl -u xray -f`。

## 增加客户端

给别人用时分配独立 UUID，便于单独吊销：

```bash
sudo bash scripts/add_client.sh --email alice
```

脚本向已安装配置追加一个 client、校验、重启服务，并输出该用户专属链接。不要让多人共用同一 UUID——共用之后无法单独踢人，也无法按用户区分流量。

## 成功标准

同时满足才算完成：

1. `systemctl is-active xray` 返回 `active`，且 `ss -tlnp` 显示目标端口由 xray 监听。
2. `xray run -test` 无告警通过。
3. `verify_reality.sh` 握手成功，吞吐相对直连损耗在合理范围。
4. 服务端日志无 error。
5. 已 `systemctl enable`，重启后自动拉起。
6. 用户拿到链接，且已被告知公网可达性未验证。

## 故障判断

| 现象 | 首查方向 |
|---|---|
| 客户端连不上，服务端日志无任何记录 | 流量没到主机。查 VPS 面板安全组 → 云 ACL → ufw，顺序不要颠倒 |
| 服务端日志有 `accepted` 但客户端超时 | 客户端参数错，重点核对 `pbk`、`sid`、`sni` 三者与服务端一致 |
| 客户端报 REALITY 握手失败 | dest 从服务器不可达，或 dest 已不支持 TLS1.3/X25519。重跑 `probe_dest.sh` |
| 服务起不来，日志 `permission denied` bind | unit 缺 `AmbientCapabilities=CAP_NET_BIND_SERVICE`，或端口被占 |
| 能连但速度慢 | 先看 BBR 是否生效，再看是否落到了 CPU 无 AES-NI 的机器 |
| v2rayN 导入后没有 flow 字段 | 客户端版本过低，升级到 6.x 以上 |
| 时通时断 | 服务器 IP 可能已被针对性阻断，换 IP 比换 dest 有效 |

更多见 [references/troubleshooting.md](references/troubleshooting.md)。

## 环境注意

- 脚本在 zsh 下也会被 `bash` 执行，但**手工敲带 `?` 的 URL 时必须加引号**，否则 zsh 会当通配符报 `no matches found`。
- `curl -w` 输出与 `--max-time` 组合时，超时会返回部分字段，判读前先确认退出码。
