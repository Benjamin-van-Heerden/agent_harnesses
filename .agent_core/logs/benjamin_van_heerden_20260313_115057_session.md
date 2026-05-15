---
created_at: '2026-03-13T11:50:57.326369'
username: benjamin_van_heerden
---
# Work Log - Remove mem onboard --nosync and move context into AGENTS.md

## Overarching Goals

Address todo #98: agents don't reliably run `mem onboard --nosync` after context compression events, and there's no hook to force it. The solution is to move essential mem context (core concepts, all commands) directly into AGENTS.md/CLAUDE.md since that file survives compression. This eliminates the need for `--nosync` entirely.

## What Was Accomplished

### Merged mem.md content into AGENTS.md template

Added a new "About mem" section to `src/templates/AGENTS.md` containing all content from `mem.md`: core concepts (specs, tasks, todos, memories, work logs), key commands, todo commands, memory commands, and doc search commands. Removed the "CRITICAL: After Context Compression" section that instructed agents to run `mem onboard --nosync`.

### Removed --nosync from onboard command

Deleted the `--nosync` flag from the `onboard()` function signature, removed the nosync early-return block, and deleted the entire `_build_nosync_output()` function (~200 lines). Also removed the `mem.md` template inclusion from the full onboard path since that content now lives in AGENTS.md (would be redundant).

### Deleted mem.md template

Removed `src/templates/mem.md` entirely — its content now lives in the AGENTS.md template.

### Updated project root AGENTS.md

Synced the project's own AGENTS.md (within MEMCONTENT tags) to match the updated template.

### Claimed todo #98

Closed GitHub issue #98.

## Key Files Affected

- `src/templates/AGENTS.md` — Added "About mem" section with all commands, removed nosync compression section
- `src/commands/onboard.py` — Removed `--nosync` flag, deleted `_build_nosync_output()`, removed `mem.md` template inclusion
- `src/templates/mem.md` — Deleted
- `AGENTS.md` — Updated MEMCONTENT to match new template

## What Comes Next

- No remaining open todos
- The AGENTS.md template is now self-sufficient after compression — agents have all mem commands and concepts available without needing to run any post-compression command
