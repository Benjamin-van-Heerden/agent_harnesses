---
title: Migrate todo memory log and report command families
status: completed
created_at: '2026-05-12T16:26:26.419565'
updated_at: '2026-05-13T09:56:47.111912'
completed_at: '2026-05-13T09:56:47.111905'
---
Move todo, memory, log, and report behavior into typed command subapps. Each family should have main.py, models/, and local utils/ where useful. Preserve GitHub-backed todo sync behavior where retained, project memory CRUD behavior, session work log behavior, and report generation behavior. Temporary report/onboard files should be created lazily by the relevant command, not by setup. Use shared src/models only for models that are used by more than one subapp.

## Completion Notes

Migrated harness todo, memory, log, and report command behavior into command-family subapps. Replaced flat todo, memory, and log modules with src/commands/todo/, src/commands/memory/, and src/commands/log/ containing main.py, per-command modules, and local utils for formatting/resolution. Added src/commands/report/main.py with weekly report generation over .agent_core/logs. Updated the harness entrypoint to register these subapps. Verified with focused Ruff, no standalone product-word usage in harness code/setup/support scripts, no generated cache files, and temp-project smoke tests for todo create/show/claim/delete, memory create/show/update/delete, log create/list/show, weekly report generation, and no .mem directory creation. GitHub-backed todo sync remains for the later sync/GitHub/worktree migration task.