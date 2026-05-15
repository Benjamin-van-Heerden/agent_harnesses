---
created_at: '2026-03-08T17:36:21.622162'
username: benjamin_van_heerden
---
# Work Log - Add --nosync flag to mem onboard

## Overarching Goals

Add a `mem onboard --nosync` command that produces a condensed context refresh without reaching out to GitHub or rebasing. This is for mid-session use after context compaction, where the full onboard is too heavy and the sync is unnecessary.

## What Was Accomplished

### Added `--nosync` flag to the `onboard` command

Added a new `--nosync` CLI option that skips GitHub sync/rebase and produces a condensed "context refresh" output instead of the full onboard.

### Implemented `_build_nosync_output` helper

Extracted the nosync output generation into a dedicated function that includes only what's needed after context compaction:

- **Directory trees** — project structure orientation
- **Memories** — project-specific patterns and conventions (crucial post-compaction)
- **Mem quick reference** — compact command cheat sheet
- **Active spec context** — spec details, tasks, and git diff stat (when in a worktree)
- **Work logs** — with a note that additional work may have been done before compaction
- **Agent instruction** — tells the agent to review and continue (no halt-and-ask)

Excludes: generic templates, core docs, important files, drift detection, sync failure handling.

### Result

The nosync output is ~154 lines vs ~845 for the full onboard — significantly lighter on the context window while preserving the essential information an agent needs to resume work.

## Key Files Affected

- `src/commands/onboard.py` — Added `_build_nosync_output()` function and `--nosync` flag to the `onboard` command. The nosync path branches early after config loading, skipping sync, drift detection, and the auto-switch-to-dev logic.

## What Comes Next

- Commit and push changes to dev
- Consider updating CLAUDE.md or the mem template to mention `mem onboard --nosync` as an available command for context refresh
