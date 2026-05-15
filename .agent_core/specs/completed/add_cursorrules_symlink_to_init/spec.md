---
title: Add .cursorrules symlink to init
status: completed
assigned_to: Benjamin-van-Heerden
issue_id: 57
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/57
branch: dev-benjamin_van_heerden-add_cursorrules_symlink_to_init
pr_url: https://github.com/Benjamin-van-Heerden/mem/pull/58
created_at: '2026-01-23T12:14:23.648196'
updated_at: '2026-01-23T12:24:27.472415'
completed_at: '2026-01-23T12:24:27.470816'
last_synced_at: '2026-01-23T12:15:22.602526'
local_content_hash: 83412744521715a64fa002b533d1e36ef113b9a757883359ca193c3d4ec7a99d
remote_content_hash: 83412744521715a64fa002b533d1e36ef113b9a757883359ca193c3d4ec7a99d
---
## Overview

When `mem init` runs, it creates an `AGENTS.md` file and a `CLAUDE.md` symlink pointing to it. This spec adds a `.cursorrules` symlink that also points to `AGENTS.md`, so Cursor IDE users get the same agent instructions automatically.

## Goals

- Add `.cursorrules` symlink creation to `mem init`
- Follow the same pattern as the existing `CLAUDE.md` symlink

## Technical Approach

In `src/commands/init.py`, update the `create_agents_files()` function to:

1. Add a `.cursorrules` symlink that points to `AGENTS.md`
2. Follow the same pattern as `CLAUDE.md`: only create if it doesn't exist and `AGENTS.md` exists
3. Use relative symlink path for portability

The change is ~3-4 lines of code, mirroring the existing CLAUDE.md symlink logic.

## Success Criteria

- Running `mem init` creates `.cursorrules -> AGENTS.md` symlink
- Existing `.cursorrules` files are not overwritten
- Tests pass

## Notes

Location: `src/commands/init.py` in the `create_agents_files()` function around line 159.
