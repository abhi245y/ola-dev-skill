#!/bin/sh
# install.sh: install the Ola Scooter Dev skill from its GitHub release.
#
# Usage:
#   install.sh [--agent NAME] [--project DIR] [--version vX.Y.Z] [--uninstall]
#   install.sh --from-file ZIP        local zip; its SHA256SUMS must sit in the same folder
#
#   NAME: claude (default), codex, gemini, cursor, agents-md, all
#
# Downloads the release zip and SHA256SUMS, checks the checksum, unzips into the agent's
# skills folder. An existing skill folder is moved to NAME.bak.TIMESTAMP before replacing.
# Running it again with the same release changes nothing. Writes only under $HOME, and into
# the project (skill folder, GEMINI.md, AGENTS.md, .cursor/rules) when --project is given.
# POSIX sh. Needs curl or wget, unzip or python3, and sha256sum or shasum.
set -eu

REPO="${OLA_SKILL_REPO:-abhi245y/ola-dev-skill}"
NAME=ola-scooter-dev
TAG="(ola-scooter-dev pointer)"
TS="$(date +%Y%m%d%H%M%S)"
AGENT=claude
PROJECT=
VERSION=latest
FROM_FILE=
UNINSTALL=0

die() { printf 'error: %s\n' "$*" >&2; exit 1; }
note() { printf '%s\n' "$*"; }

usage() {
    cat <<'EOF'
Usage: install.sh [--agent NAME] [--project DIR] [--version vX.Y.Z] [--uninstall]
       install.sh --from-file ZIP

  --agent NAME     claude (default), codex, gemini, cursor, agents-md, or all
  --project DIR    install into DIR (.claude/, .agents/, pointer files) instead of $HOME
  --version TAG    release to install, for example v0.1.0 (default: latest release)
  --from-file ZIP  install a local release zip; SHA256SUMS must sit next to it
  --uninstall      remove what this script installed for the agent
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --agent|--project|--version|--from-file)
            [ $# -ge 2 ] || die "$1 needs a value"
            case "$1" in
                --agent) AGENT="$2" ;;
                --project) PROJECT="$2" ;;
                --version) VERSION="$2" ;;
                --from-file) FROM_FILE="$2" ;;
            esac
            shift 2
            ;;
        --uninstall) UNINSTALL=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) die "unknown option: $1 (try --help)" ;;
    esac
done

: "${HOME:?HOME is not set}"
case "$AGENT" in
    claude|codex|gemini|cursor|agents-md|all) ;;
    *) die "unknown agent: $AGENT (claude, codex, gemini, cursor, agents-md, all)" ;;
esac
if [ "$VERSION" != latest ]; then
    printf '%s' "$VERSION" | grep -Eq '^v[0-9]+\.[0-9]+\.[0-9]+$' || die "--version must look like v1.2.3"
fi
if [ -n "$PROJECT" ]; then
    [ -d "$PROJECT" ] || die "--project: $PROJECT is not a directory"
    PROJECT="$(cd "$PROJECT" && pwd)"
fi
if [ -n "$PROJECT" ] && [ "$AGENT" = codex ]; then
    die "codex reads ~/.codex/skills only; drop --project"
fi
if [ -n "$FROM_FILE" ] && [ ! -f "$FROM_FILE" ]; then
    die "--from-file: $FROM_FILE not found"
fi

if [ "$AGENT" = all ]; then AGENTS="claude codex gemini cursor agents-md"; else AGENTS="$AGENT"; fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT INT TERM

# Where each agent keeps the skill folder.
skill_dir() {
    case "$1" in
        claude)
            if [ -n "$PROJECT" ]; then echo "$PROJECT/.claude/skills/$NAME"; else echo "$HOME/.claude/skills/$NAME"; fi ;;
        codex) echo "$HOME/.codex/skills/$NAME" ;;
        *)
            if [ -n "$PROJECT" ]; then echo "$PROJECT/.agents/skills/$NAME"; else echo "$HOME/.local/share/$NAME"; fi ;;
    esac
}

# A path as the pointer should spell it: relative inside a project, absolute otherwise.
ref() {
    if [ -n "$PROJECT" ]; then printf './%s' "${1#"$PROJECT"/}"; else printf '%s' "$1"; fi
}

pointer_line() { printf '%s\n' "- Ola scooter dash work: read \`$1/SKILL.md\` first. $TAG"; }

backup() {
    cp -p "$1" "$1.bak.$TS"
    note "backup: $1.bak.$TS"
}

add_pointer_file() { # file, folder
    if [ -f "$1" ] && grep -qF "$TAG" "$1"; then
        note "pointer already in $1"
        return 0
    fi
    if [ -f "$1" ]; then
        backup "$1"
        printf '\n' >> "$1"
    fi
    pointer_line "$(ref "$2")" >> "$1"
    note "added pointer to $1"
}

write_cursor_rule() { # folder
    f="$PROJECT/.cursor/rules/$NAME.mdc"
    mkdir -p "$(dirname "$f")"
    {
        printf '%s\n' '---' 'description: Ola S1 scooter dash development (ola-scooter-dev skill)' 'alwaysApply: false' '---'
        pointer_line "$(ref "$1")"
    } > "$TMP/mdc"
    if [ -f "$f" ] && cmp -s "$TMP/mdc" "$f"; then
        note "up to date: $f"
        return 0
    fi
    if [ -f "$f" ] && ! grep -qF "$TAG" "$f"; then backup "$f"; fi
    cat "$TMP/mdc" > "$f"
    note "wrote $f"
}

strip_pointer_file() { # file
    [ -f "$1" ] || return 0
    grep -qF "$TAG" "$1" || return 0
    backup "$1"
    grep -vF "$TAG" "$1" > "$TMP/strip" || true
    cat "$TMP/strip" > "$1"
    note "removed pointer from $1"
}

sha256_of() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        die "need sha256sum or shasum"
    fi
}

fetch() { # url dest
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL -o "$2" "$1" || die "download failed: $1"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$2" "$1" || die "download failed: $1"
    else
        die "need curl or wget"
    fi
}

# Unzip the release into $TMP/extract and leave the skill folder in SRC.
SRC=
get_release() {
    if [ -n "$FROM_FILE" ]; then
        zip_name="$(basename "$FROM_FILE")"
        sums_src="$(dirname "$FROM_FILE")/SHA256SUMS"
        [ -f "$sums_src" ] || die "SHA256SUMS not found next to $FROM_FILE"
        cp "$FROM_FILE" "$TMP/$zip_name"
        cp "$sums_src" "$TMP/SHA256SUMS"
    else
        if [ "$VERSION" = latest ]; then
            base="https://github.com/$REPO/releases/latest/download"
        else
            base="https://github.com/$REPO/releases/download/$VERSION"
        fi
        fetch "$base/SHA256SUMS" "$TMP/SHA256SUMS"
        count="$(awk '$2 ~ /^ola-scooter-dev-.*\.zip$/ {n++} END {print n+0}' "$TMP/SHA256SUMS")"
        [ "$count" -eq 1 ] || die "SHA256SUMS must list exactly one ola-scooter-dev zip (found $count)"
        zip_name="$(awk '$2 ~ /^ola-scooter-dev-.*\.zip$/ {print $2}' "$TMP/SHA256SUMS")"
        fetch "$base/$zip_name" "$TMP/$zip_name"
    fi

    expected="$(awk -v f="$zip_name" '$2 == f {print $1}' "$TMP/SHA256SUMS")"
    [ -n "$expected" ] || die "no checksum for $zip_name in SHA256SUMS"
    actual="$(sha256_of "$TMP/$zip_name")"
    [ "$expected" = "$actual" ] || die "checksum mismatch for $zip_name (expected $expected, got $actual)"
    note "checksum OK: $zip_name"

    mkdir "$TMP/extract"
    if command -v unzip >/dev/null 2>&1; then
        unzip -qo "$TMP/$zip_name" -d "$TMP/extract" </dev/null
    elif command -v python3 >/dev/null 2>&1; then
        python3 -I -m zipfile -e "$TMP/$zip_name" "$TMP/extract"
    else
        die "need unzip or python3"
    fi
    SRC="$TMP/extract/$NAME"
    [ -f "$SRC/SKILL.md" ] || die "zip does not contain $NAME/SKILL.md"
}

install_skill() { # folder
    if [ -d "$1" ] && diff -rq "$SRC" "$1" >/dev/null 2>&1; then
        note "up to date: $1"
        return 0
    fi
    if [ -e "$1" ]; then
        # Outside the skills folders, so an old copy never loads as a second skill.
        bdir="${XDG_STATE_HOME:-$HOME/.local/state}/$NAME/backups/$TS-$$"
        mkdir -p "$bdir"
        mv "$1" "$bdir/"
        note "backup: $bdir/$(basename "$1")"
    fi
    mkdir -p "$(dirname "$1")"
    cp -R "$SRC" "$1.new.$$"
    mv "$1.new.$$" "$1"
    note "installed: $1"
}

# Pointer lines are for agents that read a project file rather than a skills folder.
wire_pointer() { # agent, folder
    case "$1" in
        claude|codex) return 0 ;;
    esac
    if [ -z "$PROJECT" ]; then
        case "$1" in
            gemini) note "Add this line to GEMINI.md in your project:" ;;
            agents-md) note "Add this line to AGENTS.md in your project:" ;;
            cursor) note "Save this as .cursor/rules/$NAME.mdc in your project (after the front matter):" ;;
        esac
        pointer_line "$2"
        return 0
    fi
    case "$1" in
        gemini) add_pointer_file "$PROJECT/GEMINI.md" "$2" ;;
        agents-md) add_pointer_file "$PROJECT/AGENTS.md" "$2" ;;
        cursor) write_cursor_rule "$2" ;;
    esac
}

uninstall_agent() { # agent
    dir="$(skill_dir "$1")"
    if [ -f "$dir/SKILL.md" ] && grep -q "^name: $NAME\$" "$dir/SKILL.md"; then
        rm -rf "$dir"
        note "removed: $dir"
    else
        note "nothing installed at $dir"
    fi
    [ -n "$PROJECT" ] || return 0
    case "$1" in
        gemini) strip_pointer_file "$PROJECT/GEMINI.md" ;;
        agents-md) strip_pointer_file "$PROJECT/AGENTS.md" ;;
        cursor)
            rule="$PROJECT/.cursor/rules/$NAME.mdc"
            if [ -f "$rule" ] && grep -qF "$TAG" "$rule"; then
                rm -f "$rule"
                note "removed: $rule"
            fi
            ;;
    esac
}

if [ "$UNINSTALL" -eq 1 ]; then
    for a in $AGENTS; do
        if [ -n "$PROJECT" ] && [ "$a" = codex ]; then continue; fi
        uninstall_agent "$a"
    done
    exit 0
fi

get_release
for a in $AGENTS; do
    if [ -n "$PROJECT" ] && [ "$a" = codex ]; then
        note "skipped codex: it reads only ~/.codex/skills"
        continue
    fi
    dir="$(skill_dir "$a")"
    install_skill "$dir"
    wire_pointer "$a" "$dir"
done

note ""
note "Done. Start a new session and ask: \"What Ola skills do you have?\""
