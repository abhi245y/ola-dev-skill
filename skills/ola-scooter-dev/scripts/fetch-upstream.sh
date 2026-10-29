#!/usr/bin/env bash
# Clone or update the two upstream repos into a cache directory, at the commits pinned in
# upstream.json (default), or at their latest default-branch commit with --latest.
#
# Usage: fetch-upstream.sh [--latest] [--dir DIR]
#   DIR defaults to $OLA_UPSTREAM_DIR or ~/.cache/ola-scooter-dev/upstream.
#   Override a remote with OLA_SDK_URL / OLA_CAN_URL (for example a local mirror).
# Prints the checkout paths on success. Needs git and python3. Read-only on the upstream repos.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PIN_FILE="$HERE/../upstream.json"
LATEST=0
DEST="${OLA_UPSTREAM_DIR:-$HOME/.cache/ola-scooter-dev/upstream}"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --latest) LATEST=1 ;;
        --dir) DEST="${2:?--dir needs a path}"; shift ;;
        -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
    esac
    shift
done

# Read the pins with the stdlib only. Prints: name url commit
read_pins() {
    python3 -I - "$PIN_FILE" <<'PY'
import json, sys
pins = json.load(open(sys.argv[1], encoding="utf-8"))["upstreams"]
for name, info in pins.items():
    print(name, info["url"], info["commit"])
PY
}

mkdir -p "$DEST"

while read -r name url commit; do
    case "$name" in
        ola-dash-sdk) url="${OLA_SDK_URL:-$url}" ;;
        ola-can-reference) url="${OLA_CAN_URL:-$url}" ;;
    esac
    dir="$DEST/$name"
    if [ ! -d "$dir/.git" ]; then
        echo "clone $url -> $dir"
        git clone --quiet "$url" "$dir"
    else
        git -C "$dir" fetch --quiet --tags origin
    fi
    if [ "$LATEST" -eq 1 ]; then
        git -C "$dir" checkout --quiet --detach "$(git -C "$dir" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/HEAD)"
        echo "$name: latest $(git -C "$dir" rev-parse --short HEAD) (NOT the pin; tools/sync.py will refuse it)"
    else
        git -C "$dir" checkout --quiet --detach "$commit"
        echo "$name: pinned $(git -C "$dir" rev-parse --short HEAD)"
    fi
    echo "$dir"
done < <(read_pins)
