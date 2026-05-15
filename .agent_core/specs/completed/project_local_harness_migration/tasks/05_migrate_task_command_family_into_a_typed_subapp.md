---
title: Migrate task command family into a typed subapp
status: completed
created_at: '2026-05-12T16:26:16.890646'
updated_at: '2026-05-13T09:51:35.769210'
completed_at: '2026-05-13T09:51:35.769204'
---
Move the task command family from flat src/commands/task.py into commands/task/ with main.py, per-command modules, models/, and utils/. Preserve active-spec resolution, --spec behavior, task ordering, amendments, completion, rename, list, and show behavior. Use typed models for task frontmatter and command results. Keep spec-specific interactions explicit and import shared spec models/helpers only when cross-subapp sharing is actually needed. Verify task commands through the local harness entrypoint.

## Completion Notes

Migrated the harness task command family from a flat module into src/commands/task/ with main.py, per-command modules for new/list/show/complete/amend/rename, local models/result.py, and local utils/formatting.py. Wired the harness entrypoint to register the task subapp from src.commands.task.main. Added typed TaskCommandResult and kept formatting helpers local to the task family. Added state operations for amend and rename; amend resets status to todo, clears completed_at, updates timestamp, and appends amendment notes, while rename updates title and renames the ordered task file preserving its numeric prefix. Verified with focused Ruff, no standalone product-word usage in harness code/setup/support scripts, and temp-project smoke tests for task new/show/complete/list/amend/rename including file rename verification.