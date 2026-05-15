---
created_at: '2026-03-11T10:57:01.062904'
username: benjamin_van_heerden
---
# Work Log - Add noswitch_branches config and mem report command

## Overarching Goals

Implement two standalone todos: (1) add a `noswitch_branches` config option so onboard doesn't auto-switch to dev for long-lived deployment branches, and (2) add a `mem report` command that generates weekly work reports from logs.

## What Was Accomplished

### Added noswitch_branches config (todo #97)

Added a `dict[str, str]` mapping to `MemBranchConfig` where keys are child branches and values are parent branches (e.g. `company_xyz = "main"`). When on a noswitch branch:

- `ensure_on_dev_branch()` skips auto-switching
- `git_fetch_and_pull()` rebases onto `origin/{parent}` instead of using the feature-branch or ff-only paths (no auto-push)
- `get_branch_status()` treats it like a protected branch (no "no spec associated" warning)
- Onboard displays `**Noswitch Branch:** rebasing onto \`{parent}\`` in project info and a contextual message in the specs section
- Config generation renders as `[branches.noswitch_branches]` TOML table (commented-out example when empty)
- Patch command extracts, preserves, and detects missing `noswitch_branches` using the same pattern as `tree_dirs`

### Added mem report command (todo #96)

Created `mem report` command that:

- Finds all logs for the current user in the current work week (Monday–Sunday)
- Prints them formatted to stdout with box-drawing borders
- Writes a report template to `.mem/tmp/` with placeholders for the agent to fill in
- Supports `--last-week` flag to report on the previous Monday–Sunday window
- Template lives at `src/templates/week_report.md`

### Claimed both todos

Both GitHub issues (#96, #97) were closed.

## Key Files Affected

- `src/config/models.py` — Added `noswitch_branches` field to `MemBranchConfig` and `BranchNames` dataclass
- `src/config/main_config.py` — Added `noswitch_branches` param to `generate_default_config_toml()`
- `src/commands/patch.py` — Extract/preserve/detect noswitch_branches during patching
- `src/utils/specs.py` — Updated `ensure_on_dev_branch()` and `get_branch_status()` for noswitch branches
- `src/commands/sync.py` — Added noswitch branch rebase path in `git_fetch_and_pull()`
- `src/commands/onboard.py` — Added noswitch branch display in project info and specs section
- `src/commands/report.py` — New file: report command with `--last-week` option
- `src/templates/week_report.md` — New file: report template
- `main.py` — Registered report command

## What Comes Next

- Commit and push changes to dev
