#!/usr/bin/env bash
# Add, list, or revoke clients on an installed Xray REALITY node. Requires root.
#
# Usage:
#   sudo bash add_client.sh --email alice [--uuid UUID]
#   sudo bash add_client.sh --list
#   sudo bash add_client.sh --remove alice

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CONFIG=/usr/local/etc/xray/config.json
PARAMS=/usr/local/etc/xray/params.env
EMAIL=""
UUID=""
ACTION=add
REMOVE_EMAIL=""

while [ $# -gt 0 ]; do
  case $1 in
    --email)  EMAIL=$2; shift 2 ;;
    --uuid)   UUID=$2; shift 2 ;;
    --config) CONFIG=$2; shift 2 ;;
    --list)   ACTION=list; shift ;;
    --remove) ACTION=remove; REMOVE_EMAIL=$2; shift 2 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 1 ;;
  esac
done

[ "$(id -u)" -eq 0 ] || { echo "error: must run as root" >&2; exit 1; }
[ -f "$CONFIG" ] || { echo "error: $CONFIG not found" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "error: python3 is required" >&2; exit 1; }

if [ "$ACTION" = list ]; then
  python3 - "$CONFIG" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1]))
for c in cfg["inbounds"][0]["settings"]["clients"]:
    print(f"{c.get('email', '(no label)'):20} {c['id']}")
PY
  exit 0
fi

BACKUP="$CONFIG.bak.$(date +%Y%m%d%H%M%S)"
cp -a "$CONFIG" "$BACKUP"

if [ "$ACTION" = remove ]; then
  [ -n "$REMOVE_EMAIL" ] || { echo "error: --remove needs a label" >&2; exit 1; }
  python3 - "$CONFIG" "$REMOVE_EMAIL" <<'PY'
import json, sys
path, email = sys.argv[1], sys.argv[2]
cfg = json.load(open(path))
clients = cfg["inbounds"][0]["settings"]["clients"]
kept = [c for c in clients if c.get("email") != email]
if len(kept) == len(clients):
    sys.exit(f"error: no client labelled {email!r}")
if not kept:
    sys.exit("error: refusing to remove the last client")
cfg["inbounds"][0]["settings"]["clients"] = kept
json.dump(cfg, open(path, "w"), indent=2)
PY
else
  [ -n "$EMAIL" ] || { echo "error: --email is required" >&2; exit 1; }
  [ -n "$UUID" ] || UUID=$(/usr/local/bin/xray uuid)
  python3 - "$CONFIG" "$EMAIL" "$UUID" <<'PY'
import json, sys
path, email, uuid = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = json.load(open(path))
clients = cfg["inbounds"][0]["settings"]["clients"]
if any(c.get("email") == email for c in clients):
    sys.exit(f"error: client {email!r} already exists")
if any(c["id"] == uuid for c in clients):
    sys.exit("error: UUID already in use")
clients.append({"id": uuid, "flow": "xtls-rprx-vision", "email": email})
json.dump(cfg, open(path, "w"), indent=2)
PY
fi

chmod 600 "$CONFIG"
chown xray:xray "$CONFIG" 2>/dev/null || true

if ! OUT=$(/usr/local/bin/xray run -test -c "$CONFIG" 2>&1); then
  echo "$OUT" >&2
  cp -a "$BACKUP" "$CONFIG"
  echo "error: config invalid, rolled back from $BACKUP" >&2
  exit 1
fi

systemctl restart xray
sleep 2
systemctl is-active --quiet xray || { echo "error: xray failed to restart" >&2; exit 1; }
echo "==> service restarted (backup: $BACKUP)"

if [ "$ACTION" = remove ]; then
  echo "==> revoked: $REMOVE_EMAIL"
  exit 0
fi

if [ -f "$PARAMS" ]; then
  # shellcheck disable=SC1090
  . "$PARAMS"
  echo
  echo "==> share link for $EMAIL"
  bash "$SCRIPT_DIR/make_link.sh" \
    "$SERVER_IP" "$PORT" "$UUID" "$DEST" "$PUBLIC_KEY" "$SHORT_ID" "${REMARK:-xray-reality}-$EMAIL"
else
  echo "note: $PARAMS not found; build the link manually with uuid $UUID" >&2
fi
