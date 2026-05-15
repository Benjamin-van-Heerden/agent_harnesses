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
PYTHON_BIN="${PYTHON:-python}"

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
    "$PYTHON_BIN" -B "$SUPPORT_DIR/upsert_config.py" "$config_file" "$project_name"
}

ensure_symlink_paths_ignored() {
    local config_file="$STATE_DIR/config.toml"
    local gitignore_file="$TARGET_ROOT/.gitignore"
    "$PYTHON_BIN" -B - "$config_file" "$gitignore_file" <<'PY'
import sys
import tomllib
from pathlib import Path

config_path = Path(sys.argv[1])
gitignore_path = Path(sys.argv[2])

try:
    config = tomllib.loads(config_path.read_text())
except (OSError, tomllib.TOMLDecodeError):
    raise SystemExit(0)

symlink_paths = config.get("worktree", {}).get("symlink_paths", [])
if not isinstance(symlink_paths, list):
    raise SystemExit(0)

entries: list[str] = []
for value in symlink_paths:
    if not isinstance(value, str):
        continue
    path = value.strip().strip("/")
    if not path:
        continue
    entries.extend([path, f"{path}/"])

if not entries:
    raise SystemExit(0)

existing = gitignore_path.read_text().splitlines() if gitignore_path.exists() else []
seen = {line.strip() for line in existing}
missing = [entry for entry in entries if entry not in seen]
if not missing:
    raise SystemExit(0)

lines = existing[:]
if lines and lines[-1].strip():
    lines.append("")
lines.append("# Agent Core worktree symlinks")
lines.extend(missing)
gitignore_path.write_text("\n".join(lines).rstrip() + "\n")
PY
}

branch_names() {
    "$PYTHON_BIN" -B - "$STATE_DIR/config.toml" <<'PY'
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

set_branch_names() {
    "$PYTHON_BIN" -B - "$STATE_DIR/config.toml" "$1" "$2" "$3" <<'PY'
import json
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
values = {
    "dev": sys.argv[2],
    "test": sys.argv[3],
    "main": sys.argv[4],
}
content = path.read_text()
lines = content.splitlines()
section_index = None

for index, line in enumerate(lines):
    if line.strip() == "[branches]":
        section_index = index
        break

if section_index is None:
    if lines and lines[-1].strip():
        lines.append("")
    lines.append("[branches]")
    section_index = len(lines) - 1

section_end = section_index + 1
while section_end < len(lines) and not lines[section_end].strip().startswith("["):
    section_end += 1

present = set()
for index in range(section_index + 1, section_end):
    match = re.match(r"^(\s*)(dev|test|main)\s*=", lines[index])
    if not match:
        continue
    key = match.group(2)
    present.add(key)
    lines[index] = f"{key} = {json.dumps(values[key])}"

insert_at = section_end
for key in ("dev", "test", "main"):
    if key in present:
        continue
    lines.insert(insert_at, f"{key} = {json.dumps(values[key])}")
    insert_at += 1

path.write_text("\n".join(lines).rstrip() + "\n")
PY
}

print_existing_branches() {
    echo "Existing branches:"

    local local_branches
    local_branches="$(git -C "$TARGET_ROOT" for-each-ref --format='%(refname:short)' refs/heads | sort)"
    if [[ -n "$local_branches" ]]; then
        echo "  Local:"
        while IFS= read -r branch; do
            echo "    - $branch"
        done <<< "$local_branches"
    else
        echo "  Local: none"
    fi

    if git -C "$TARGET_ROOT" remote get-url origin >/dev/null 2>&1; then
        local remote_branches
        remote_branches="$(git -C "$TARGET_ROOT" for-each-ref --format='%(refname:short)' refs/remotes/origin | sed '/^origin\/HEAD$/d' | sort)"
        if [[ -n "$remote_branches" ]]; then
            echo "  Origin:"
            while IFS= read -r branch; do
                echo "    - ${branch#origin/}"
            done <<< "$remote_branches"
        else
            echo "  Origin: none"
        fi
    fi
}

prompt_branch_mapping() {
    local branch_output
    if ! branch_output="$(branch_names)"; then
        exit 1
    fi

    local dev_branch
    local test_branch
    local main_branch
    dev_branch="$(printf "%s\n" "$branch_output" | sed -n '1p')"
    test_branch="$(printf "%s\n" "$branch_output" | sed -n '2p')"
    main_branch="$(printf "%s\n" "$branch_output" | sed -n '3p')"

    echo "Configured protected branch mapping:"
    echo "  dev  -> $dev_branch"
    echo "  test -> $test_branch"
    echo "  main -> $main_branch"

    if [[ ! -t 0 ]]; then
        echo "No interactive terminal detected; keeping the configured branch mapping."
        return
    fi

    echo "Press Enter to keep each value, or type an existing/custom branch name."

    local candidate
    read -r -p "dev branch [$dev_branch]: " candidate
    if [[ -n "$candidate" ]]; then
        dev_branch="$candidate"
    fi
    read -r -p "test branch [$test_branch]: " candidate
    if [[ -n "$candidate" ]]; then
        test_branch="$candidate"
    fi
    read -r -p "main branch [$main_branch]: " candidate
    if [[ -n "$candidate" ]]; then
        main_branch="$candidate"
    fi

    local branch
    for branch in "$dev_branch" "$test_branch" "$main_branch"; do
        if ! git -C "$TARGET_ROOT" check-ref-format --branch "$branch" >/dev/null 2>&1; then
            echo "Error: invalid branch name: $branch" >&2
            exit 1
        fi
    done

    set_branch_names "$dev_branch" "$test_branch" "$main_branch"
    echo "Updated .agent_core/config.toml branch mapping."
}

configured_branches_missing() {
    local has_origin="$1"
    local branch_output
    if ! branch_output="$(branch_names)"; then
        exit 1
    fi

    local branch
    while IFS= read -r branch; do
        [[ -n "$branch" ]] || continue
        if ! git -C "$TARGET_ROOT" show-ref --verify --quiet "refs/heads/$branch"; then
            return 0
        fi
        if [[ "$has_origin" == true ]] && ! git -C "$TARGET_ROOT" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
            return 0
        fi
    done <<< "$branch_output"

    return 1
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

    if configured_branches_missing "$has_origin"; then
        echo "Configured protected branches are missing."
        print_existing_branches
        prompt_branch_mapping
    fi

    if ! git -C "$TARGET_ROOT" rev-parse --verify HEAD >/dev/null 2>&1; then
        echo "Error: setup requires at least one commit before protected branches can be created." >&2
        exit 1
    fi

    local branch_output
    if ! branch_output="$(branch_names)"; then
        exit 1
    fi
    local branch
    while IFS= read -r branch; do
        [[ -n "$branch" ]] || continue
        if ! git -C "$TARGET_ROOT" show-ref --verify --quiet "refs/heads/$branch"; then
            if $has_origin && git -C "$TARGET_ROOT" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
                git -C "$TARGET_ROOT" branch --track "$branch" "origin/$branch" >/dev/null 2>&1
            else
                git -C "$TARGET_ROOT" branch "$branch" >/dev/null 2>&1
            fi
            echo "Created local protected branch: $branch"
        fi
        if $has_origin && ! git -C "$TARGET_ROOT" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
            git -C "$TARGET_ROOT" push -u origin "$branch:$branch" >/dev/null 2>&1 || {
                echo "Error: failed to create origin/$branch." >&2
                exit 1
            }
            echo "Created origin protected branch: origin/$branch"
        fi
    done <<< "$branch_output"
}

ensure_update_branch() {
    if ! $UPDATE; then
        return
    fi

    local branch_output
    if ! branch_output="$(branch_names)"; then
        exit 1
    fi

    local dev_branch
    local test_branch
    local main_branch
    dev_branch="$(printf "%s\n" "$branch_output" | sed -n '1p')"
    test_branch="$(printf "%s\n" "$branch_output" | sed -n '2p')"
    main_branch="$(printf "%s\n" "$branch_output" | sed -n '3p')"

    local current_branch
    current_branch="$(git -C "$TARGET_ROOT" branch --show-current)"
    if [[ -z "$current_branch" ]]; then
        echo "Error: setup --update must run on a named branch, not detached HEAD." >&2
        exit 1
    fi

    if [[ "$current_branch" == "$dev_branch" ]]; then
        return
    fi

    if [[ "$current_branch" != "$main_branch" && "$current_branch" != "$test_branch" ]]; then
        return
    fi

    if [[ -n "$(git -C "$TARGET_ROOT" status --porcelain)" ]]; then
        echo "Error: setup --update must switch from $current_branch to $dev_branch before changing the managed harness." >&2
        echo "Your working tree has uncommitted changes. You must commit, stash, or restore them, then rerun setup --update." >&2
        exit 1
    fi

    git -C "$TARGET_ROOT" checkout "$dev_branch" >/dev/null 2>&1 || {
        echo "Error: failed to switch from $current_branch to $dev_branch before updating the managed harness." >&2
        exit 1
    }
    echo "Switched to configured dev branch for harness update: $dev_branch"
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

    "$PYTHON_BIN" -B - "$target_file" "$TEMPLATE_ROOT/AGENTS.md" "$CORE_START_TAG" "$CORE_END_TAG" <<'PY'
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

copy_optional_doc() {
    local slug="$1"
    local source
    if ! source="$(optional_doc_path "$slug")"; then
        echo "Error: unknown optional doc: $slug" >&2
        echo "Available docs:" >&2
        docs_list >&2
        exit 1
    fi
    cp "$source" "$STATE_DIR/docs/$(basename "$source")"
}

docs_add() {
    if [[ "$#" -eq 0 ]]; then
        echo "Error: docs add requires at least one doc slug." >&2
        usage >&2
        exit 1
    fi

    mkdir -p "$STATE_DIR/docs"
    local slug
    for slug in "$@"; do
        copy_optional_doc "$slug"
        echo "Added optional doc: $slug"
    done
}

install_default_docs() {
    mkdir -p "$STATE_DIR/docs"

    local slug
    local source
    local target
    for slug in general testing; do
        if ! source="$(optional_doc_path "$slug")"; then
            continue
        fi
        target="$STATE_DIR/docs/$(basename "$source")"
        if [[ -f "$target" ]]; then
            continue
        fi
        cp "$source" "$target"
        echo "Included default doc: $slug"
    done
}

prompt_optional_docs() {
    if [[ ! -t 0 ]]; then
        return
    fi

    local available=()
    local slug
    while IFS= read -r slug; do
        [[ "$slug" != "general" && "$slug" != "testing" ]] || continue
        [[ ! -f "$STATE_DIR/docs/$slug.md" ]] || continue
        available+=("$slug")
    done < <(docs_list)

    if [[ "${#available[@]}" -eq 0 ]]; then
        return
    fi

    echo "Additional optional docs are available: ${available[*]}"
    echo "Enter slugs separated by spaces to install them, or press Enter to skip."

    local selected
    read -r -p "Optional docs: " selected
    if [[ -z "$selected" ]]; then
        return
    fi

    # shellcheck disable=SC2086
    docs_add $selected
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
ensure_symlink_paths_ignored
ensure_branches_exist
ensure_update_branch
install_harness
ensure_user_mappings
install_agents_file
ensure_claude_file
install_default_docs
prompt_optional_docs

if $UPDATE; then
    echo "Updated project-local harness."
else
    echo "Installed project-local harness."
fi
