---
title: Add tests for AGENTS.md drift detection and patching
status: completed
created_at: '2026-01-22T09:15:06.483397'
updated_at: '2026-01-22T09:28:07.309784'
completed_at: '2026-01-22T09:28:07.309776'
---
Create tests in tests/ for: (1) Drift detection - file with matching content, file with outdated content, file without tags (legacy), missing file, (2) Patch command - updates mem content preserving user content, dry-run shows changes without modifying, idempotent behavior, handles legacy files. Follow existing test patterns in tests/test_config_drift.py.

## Completion Notes

Created tests/test_agents_drift.py with 13 tests covering: drift detection (missing file, no tags, outdated content, up to date, with user content, missing template), patch command (adds tags, preserves user content, dry run, idempotent, up to date), and init command (wraps in tags, no overwrite). All tests pass.