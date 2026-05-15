---
title: Migrate spec command family into a typed subapp
status: completed
created_at: '2026-05-12T16:25:55.617703'
updated_at: '2026-05-13T09:46:38.317971'
completed_at: '2026-05-13T09:46:38.317963'
---
Move the spec command family from the flat src/commands/spec.py shape into a command subapp with main.py, per-command modules, models/, and utils/. Include spec new/list/show/assign/complete/abandon behavior. Keep helpers local to commands/spec/utils unless they are truly shared by other subapps. Introduce typed models for spec command inputs/outputs/frontmatter where useful. Preserve worktree workflow constraints and branch alias behavior. Verify each spec command through the local harness entrypoint.

## Completion Notes

Migrated the harness spec command family from a flat module into src/commands/spec/ with main.py, per-command modules for new/list/show/complete/abandon/assign, local models/result.py, and local utils/formatting.py. Wired the harness entrypoint to register the spec subapp from src.commands.spec.main. Added a typed SpecCommandResult and kept formatting helpers local to the spec family. Updated state/specs.py so complete and abandon move specs into .agent_core/specs/completed/ and .agent_core/specs/abandoned/. Left spec assign registered with an explicit not-yet-migrated guard because worktree/GitHub behavior is scheduled for the later sync/GitHub/worktree task. Verified with focused Ruff, no standalone product-word usage in harness code/setup/support scripts, and temp-project smoke tests for spec new/list/show/complete/abandon plus the assign guard.