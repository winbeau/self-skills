# Deploy Xray REALITY

`deploy-xray-reality` turns a Linux VPS into a VLESS + XTLS-Vision + REALITY node and hands back a share link that imports directly into v2rayN.

## Typical request

```text
使用 $deploy-xray-reality 在这台服务器上装 Xray，我要最快的方案，最后给我 v2rayN 链接。
```

"最快" is read as *fastest transport*, not *fewest steps*. Vision + REALITY happens to be both: splice-based zero-copy forwarding, a single TLS layer, no CDN hop, and no domain or certificate to obtain.

## Why this transport

| | VLESS + Vision + REALITY | VMess / Trojan + WS + TLS + CDN |
|---|---|---|
| TLS layers | 1 | 2 |
| Data path | `splice()` zero-copy | userspace copy each direction |
| Extra hop | none | CDN edge |
| Domain + certificate | not needed | required |
| Best for | raw speed | must traverse a CDN, or must look like a website |

Measured on a Los Angeles VPS with a 10 MB transfer: 50.75 MB/s proxied against 51.18 MB/s direct — about 0.85% overhead.

## Pipeline

Four scripts, run in order. Only step 2 needs root.

```bash
# 1. pick a borrowed site
skills/deploy-xray-reality/scripts/probe_dest.sh

# 2. generate keys and config (unprivileged)
skills/deploy-xray-reality/scripts/setup_reality.sh \
  --dest addons.mozilla.org --workdir ./xray-build --remark "LA-Reality"

# 3. install the service (root)
sudo bash skills/deploy-xray-reality/scripts/install_service.sh --workdir ./xray-build

# 4. prove it actually forwards
skills/deploy-xray-reality/scripts/verify_reality.sh --workdir ./xray-build
```

`probe_dest.sh` checks each candidate for TLS 1.3, X25519 key exchange, and HTTP/2 ALPN, sorts by latency, and flags domains known to attract targeted blocking.

`setup_reality.sh` downloads the matching Xray build, generates the UUID / x25519 keypair / shortId, renders the config, validates it with `xray run -test`, and writes `params.env` and `share-link.txt` (both mode 600).

`install_service.sh` installs to `/usr/local/`, creates a dedicated `xray` system user, binds port 443 through `CAP_NET_BIND_SERVICE` instead of running as root, enables BBR with `fq`, opens ufw when active, and backs up any existing config with a timestamp.

`verify_reality.sh` starts a throwaway local client, checks the handshake, and compares proxied against direct throughput before cleaning up.

## Managing users

Give every person their own UUID so access can be revoked individually.

```bash
sudo bash skills/deploy-xray-reality/scripts/add_client.sh --email alice   # prints alice's link
sudo bash skills/deploy-xray-reality/scripts/add_client.sh --list
sudo bash skills/deploy-xray-reality/scripts/add_client.sh --remove alice
```

Config edits are validated before the restart and rolled back from a timestamped backup if `xray run -test` rejects them.

## Two rules the validator enforces

Both surface as `xray run -test` warnings, and both are about avoiding targeted blocking of the server IP:

- **Do not borrow apple/icloud-family dests.** `probe_dest.sh` marks these `RISKY`.
- **Stay on port 443.** REALITY's cover story is "an ordinary HTTPS connection to port 443"; a different port breaks it.

Never proceed with a warning left unresolved.

## What verification does and does not cover

`verify_reality.sh` runs entirely on the host, so it proves the handshake, forwarding, and throughput — but **not** that port 443 is reachable from the internet. When a client cannot connect and the server log shows no `accepted` entries, check in this order:

1. VPS provider security group
2. Cloud network ACL
3. Host firewall (`ufw` / `iptables`)

Running from the server itself also means the proxied egress IP necessarily equals the server IP; that equality alone proves nothing.

## Client requirement

v2rayN 6.x or newer. Older builds silently drop `flow` and the REALITY fields on import — after importing, confirm the node shows `xtls-rprx-vision`.

## Security notes

The private key stays in the server config and in `params.env` (mode 600, root-owned once installed). Only the public key `pbk` goes into the share link.

A share link embeds a UUID and is a credential. It should not be posted anywhere public, and multiple people should never share one UUID — a shared UUID cannot be revoked or attributed per user.

Further detail: [dest selection](../../skills/deploy-xray-reality/references/dest-selection.md) and [troubleshooting](../../skills/deploy-xray-reality/references/troubleshooting.md).
