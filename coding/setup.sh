#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/Benjamin-van-Heerden/agent_harnesses.git"
TEMPLATE_SUBPATH="coding"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd || printf '')"
TARGET_ROOT="$(pwd)"
STATE_DIR="$TARGET_ROOT/.agent_core"
HARNESS_TARGET="$STATE_DIR/harness"
CORE_START_TAG="<AGENT_CORE>"
CORE_END_TAG="</AGENT_CORE>"
CLONE_DIR=""

UPDATE=false
if [[ "${1:-}" == "--update" ]]; then
    UPDATE=true
fi

cleanup() {
    if [[ -n "$CLONE_DIR" ]]; then
        rm -rf "$CLONE_DIR"
    fi
}
trap cleanup EXIT

resolve_template_root() {
    if [[ -n "$SCRIPT_DIR" && -d "$SCRIPT_DIR/.agent_core/harness" ]]; then
        printf "%s\n" "$SCRIPT_DIR"
        return
    fi

    if ! command -v git >/dev/null 2>&1; then
        echo "Error: git is required to fetch the agent harness template." >&2
        exit 1
    fi

    CLONE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/agent-harnesses-setup-XXXXXX")"
    echo "Fetching latest agent harness templates..." >&2
    git clone --depth 1 --quiet "$REPO_URL" "$CLONE_DIR"

    local template_root="$CLONE_DIR/$TEMPLATE_SUBPATH"
    if [[ ! -d "$template_root/.agent_core/harness" ]]; then
        echo "Error: template subdirectory '$TEMPLATE_SUBPATH' not found in $REPO_URL." >&2
        exit 1
    fi
    printf "%s\n" "$template_root"
}

TEMPLATE_ROOT="$(resolve_template_root)"
HARNESS_SOURCE="$TEMPLATE_ROOT/.agent_core/harness"
SUPPORT_DIR="$TEMPLATE_ROOT/setup_support"
OPTIONAL_DOCS_DIR="$TEMPLATE_ROOT/optional_docs"

ensure_state_dirs() {
    local dirs=(
        "$STATE_DIR"
        "$STATE_DIR/specs"
        "$STATE_DIR/todos"
        "$STATE_DIR/memories"
        "$STATE_DIR/logs"
        "$STATE_DIR/docs"
    )
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
}

usage() {
    cat <<'EOF'
Usage:
  setup.sh [--update]
  setup.sh docs list
  setup.sh docs add <slug> [slug ...]
  setup.sh docs update [slug ...]

Docs commands copy optional docs into .agent_core/docs/.
When docs update is run without slugs, it updates installed docs that still
match a document in the harness optional_docs directory.
EOF
}

install_harness() {
    rm -rf "$HARNESS_TARGET"
    mkdir -p "$STATE_DIR"
    cp -R "$HARNESS_SOURCE" "$HARNESS_TARGET"
}

ensure_config() {
    local config_file="$STATE_DIR/config.toml"
    local project_name
    project_name="$(basename "$TARGET_ROOT")"
    PYTHONDONTWRITEBYTECODE=1 python3 "$SUPPORT_DIR/upsert_config.py" "$config_file" "$project_name"
}

branch_names() {
    PYTHONDONTWRITEBYTECODE=1 python3 - "$STATE_DIR/config.toml" <<'PY'
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

config = tomllib.loads(Path(sys.argv[1]).read_text())
branches = config.get("branches", {})
missing = [name for name in ("dev", "test", "main") if not branches.get(name)]
if missing:
    print(f"Missing required [branches] key(s): {', '.join(missing)}", file=sys.stderr)
    raise SystemExit(1)
for name in ("dev", "test", "main"):
    print(branches[name])
PY
}

ensure_branches_exist() {
    if ! command -v git >/dev/null 2>&1; then
        echo "Error: git is required but was not found on PATH." >&2
        exit 1
    fi
    if ! git -C "$TARGET_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
        echo "Error: setup must be run from an initialized git repository." >&2
        exit 1
    fi

    local has_origin=false
    if git -C "$TARGET_ROOT" remote get-url origin >/dev/null 2>&1; then
        has_origin=true
        git -C "$TARGET_ROOT" fetch --prune origin >/dev/null 2>&1 || {
            echo "Error: failed to fetch origin while validating protected branches." >&2
            exit 1
        }
    fi

    local missing=()
    local branch_output
    if ! branch_output="$(branch_names)"; then
        exit 1
    fi
    local branch
    while IFS= read -r branch; do
        [[ -n "$branch" ]] || continue
        if ! git -C "$TARGET_ROOT" show-ref --verify --quiet "refs/heads/$branch"; then
            missing+=("$branch (local)")
        fi
        if $has_origin && ! git -C "$TARGET_ROOT" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
            missing+=("origin/$branch")
        fi
    done <<< "$branch_output"

    if [[ "${#missing[@]}" -gt 0 ]]; then
        echo "Error: required protected branch(es) missing: ${missing[*]}" >&2
        echo "Create the configured dev/test/main branches before running setup." >&2
        exit 1
    fi
}

ensure_user_mappings() {
    local mappings_file="$STATE_DIR/user_mappings.toml"
    if [[ -f "$mappings_file" ]]; then
        return
    fi
    printf "# GitHub username to git user mappings\n" > "$mappings_file"
}

install_agents_file() {
    local target_file="$TARGET_ROOT/AGENTS.md"
    local core_block
    core_block="$(cat "$TEMPLATE_ROOT/AGENTS.md")"

    if [[ ! -f "$target_file" ]]; then
        printf "%s\n" "$core_block" > "$target_file"
        return
    fi

    PYTHONDONTWRITEBYTECODE=1 python3 - "$target_file" "$TEMPLATE_ROOT/AGENTS.md" "$CORE_START_TAG" "$CORE_END_TAG" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

target = Path(sys.argv[1])
template = Path(sys.argv[2]).read_text().strip() + "\n"
start = sys.argv[3]
end = sys.argv[4]
content = target.read_text()

start_index = content.find(start)
end_index = content.find(end)

if start_index != -1 and end_index != -1 and end_index > start_index:
    end_index = end_index + len(end)
    updated = content[:start_index] + template.strip() + content[end_index:]
else:
    updated = template + "\n" + content

target.write_text(updated)
PY
}

ensure_claude_file() {
    local target_file="$TARGET_ROOT/CLAUDE.md"
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        cp "$TARGET_ROOT/AGENTS.md" "$target_file"
        return
    fi
    rm -f "$target_file"
    ln -s "AGENTS.md" "$target_file"
}

optional_doc_path() {
    local slug="$1"
    if [[ "$slug" == *"/"* || "$slug" == "."* || "$slug" == *".md" ]]; then
        return 1
    fi
    local path="$OPTIONAL_DOCS_DIR/$slug.md"
    if [[ ! -f "$path" ]]; then
        return 1
    fi
    printf "%s\n" "$path"
}

docs_list() {
    local doc
    find "$OPTIONAL_DOCS_DIR" -maxdepth 1 -type f -name "*.md" -print | sort | while read -r doc; do
        basename "$doc" .md
    done
}

docs_add() {
    if [[ "$#" -eq 0 ]]; then
        echo "Error: docs add requires at least one doc slug." >&2
        usage >&2
        exit 1
    fi

    mkdir -p "$STATE_DIR/docs"
    local slug
    local source
    for slug in "$@"; do
        if ! source="$(optional_doc_path "$slug")"; then
            echo "Error: unknown optional doc: $slug" >&2
            echo "Available docs:" >&2
            docs_list >&2
            exit 1
        fi
        cp "$source" "$STATE_DIR/docs/$(basename "$source")"
        echo "Added optional doc: $slug"
    done
}

docs_update() {
    mkdir -p "$STATE_DIR/docs"

    if [[ "$#" -gt 0 ]]; then
        docs_add "$@"
        return
    fi

    local updated=false
    local source
    local target
    for source in "$OPTIONAL_DOCS_DIR"/*.md; do
        [[ -f "$source" ]] || continue
        target="$STATE_DIR/docs/$(basename "$source")"
        if [[ -f "$target" ]]; then
            cp "$source" "$target"
            echo "Updated optional doc: $(basename "$source" .md)"
            updated=true
        fi
    done

    if [[ "$updated" == false ]]; then
        echo "No installed optional docs to update."
    fi
}

handle_docs_command() {
    local subcommand="${1:-}"
    case "$subcommand" in
        list)
            docs_list
            ;;
        add)
            shift
            docs_add "$@"
            ;;
        update)
            shift
            docs_update "$@"
            ;;
        *)
            usage >&2
            exit 1
            ;;
    esac
}

if [[ "${1:-}" == "docs" ]]; then
    shift
    handle_docs_command "$@"
    exit 0
fi

ensure_state_dirs
ensure_config
ensure_branches_exist
install_harness
ensure_user_mappings
install_agents_file
ensure_claude_file

if $UPDATE; then
    echo "Updated project-local harness."
else
    echo "Installed project-local harness."
fi
