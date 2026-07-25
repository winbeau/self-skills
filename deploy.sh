#!/usr/bin/env bash
# Deploy repository-managed tools and Skills through symlinks.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="claude"

usage() {
  cat <<'EOF'
Usage: ./deploy.sh [--target claude|codex|both]

Environment overrides:
  CLAUDE_HOME  Claude configuration root (default: ~/.claude)
  CODEX_HOME   Codex configuration root (default: ~/.codex)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      [[ $# -ge 2 ]] || { echo "deploy.sh: --target requires a value" >&2; exit 2; }
      TARGET="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "deploy.sh: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$TARGET" in
  claude|codex|both) ;;
  *) echo "deploy.sh: target must be claude, codex, or both" >&2; exit 2 ;;
esac

CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
BIN_DIR="${HOME}/bin"
STAMP="$(date +%Y%m%d%H%M%S)"

echo "==> Repository: $REPO"
echo "==> Target: $TARGET"
mkdir -p "$BIN_DIR"

backup_conflict() {
  local target="$1"
  if [[ -e "$target" || -L "$target" ]]; then
    if [[ -L "$target" ]]; then
      rm -f "$target"
    else
      local backup="${target}.bak.${STAMP}"
      mv "$target" "$backup"
      echo "    backed up: $target -> $backup"
    fi
  fi
}

link_file() {
  local source="$1" target="$2"
  mkdir -p "$(dirname "$target")"
  if [[ -L "$target" && "$(readlink -f "$target" 2>/dev/null || true)" == "$(readlink -f "$source")" ]]; then
    return
  fi
  backup_conflict "$target"
  ln -s "$source" "$target"
}

deploy_skills() {
  local root="$1" label="$2"
  local skills_dir="$root/skills"
  mkdir -p "$skills_dir"
  echo "==> Linking Skills for $label -> $skills_dir"
  for skill in "$REPO"/skills/*/; do
    [[ -f "$skill/SKILL.md" ]] || continue
    local name
    name="$(basename "$skill")"
    link_file "${skill%/}" "$skills_dir/$name"
    echo "    linked skill: $name"
  done

  # Remove only legacy links that point into this repository and whose source no longer exists.
  for link in "$skills_dir"/*; do
    [[ -L "$link" ]] || continue
    local raw
    raw="$(readlink "$link")"
    if [[ "$raw" == "$REPO/skills/"* && ! -e "$link" ]]; then
      rm -f "$link"
      echo "    removed stale repository link: $(basename "$link")"
    fi
  done
}

echo "==> Linking CLI tools -> $BIN_DIR"
for tool in "$REPO"/bin/*; do
  [[ -f "$tool" ]] || continue
  chmod +x "$tool"
  link_file "$tool" "$BIN_DIR/$(basename "$tool")"
  echo "    linked bin: $(basename "$tool")"
done
chmod +x "$REPO/skills/notify-win/scripts/notify-win"
link_file "$REPO/skills/notify-win/scripts/notify-win" "$BIN_DIR/notify-win"
echo "    linked bin: notify-win"

if [[ "$TARGET" == "claude" || "$TARGET" == "both" ]]; then
  deploy_skills "$CLAUDE_DIR" "Claude Code"

  echo "==> Linking global Claude prompt"
  link_file "$REPO/global/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"

  echo "==> Configuring Claude terminal and permission baseline"
  python3 - "$CLAUDE_DIR/settings.json" <<'PY'
import json
import os
import shutil
import sys

path = sys.argv[1]
settings = {}
if os.path.exists(path):
    try:
        with open(path, encoding="utf-8") as handle:
            settings = json.load(handle)
    except json.JSONDecodeError:
        shutil.copyfile(path, path + ".bak")
        print("    invalid settings.json backed up as settings.json.bak")

settings["tui"] = "default"
env = settings.get("env") or {}
env["CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN"] = "1"
settings["env"] = env
permissions = settings.get("permissions")
if not isinstance(permissions, dict):
    permissions = {}
permissions["defaultMode"] = "bypassPermissions"
settings["permissions"] = permissions
settings["skipDangerousModePermissionPrompt"] = True
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as handle:
    json.dump(settings, handle, indent=2, ensure_ascii=False)
    handle.write("\n")
print("    settings.json updated")
PY
fi

if [[ "$TARGET" == "codex" || "$TARGET" == "both" ]]; then
  deploy_skills "$CODEX_DIR" "Codex"
fi

echo
echo "==> Done"
if [[ "$TARGET" == "claude" || "$TARGET" == "both" ]]; then
  echo "    Restart Claude Code for terminal scroll changes, or run /tui default now."
fi
