---
created_at: '2026-05-21T10:18:51.776275'
username: benjamin_van_heerden
---
Work Log - Preserve Spec Directory Artifacts On Completion

## Overarching Goals

Ensure coding harness specs can contain additional spec-owned artifacts, such as research markdown files, without losing them when the spec is moved to `completed/` or `abandoned/`.

## What Was Accomplished

### Preserved the whole spec directory during status moves

Changed `specs.update_status()` so status transitions that move a spec now move the entire spec directory to the target status directory first, then rewrite `spec.md` at its new location with updated frontmatter.

Previously, the function wrote only a new `spec.md` into `.agent_core/specs/completed/<slug>/` and removed the original active spec directory. That deleted any additional files stored next to `spec.md`, such as `legal_migration_research.md`.

The new behavior preserves files and subdirectories owned by the spec directory, including `tasks/` and ad hoc research artifacts.

### Added regression coverage

Added a focused test that creates a spec with:

- `spec.md`;
- `legal_migration_research.md`;
- `tasks/01_task.md`.

The test completes the spec through `specs.update_status()` and asserts the research file and task file survive under `.agent_core/specs/completed/<slug>/`.

Verification performed:

- `uvx ruff check coding/.agent_core/harness/src/state/specs.py coding/tests/test_multi_user_assignment.py`
- `uv run pytest coding/tests/test_multi_user_assignment.py -k "duplicate_slugs or preserves_additional_spec_files"`
- `uv run ty check coding/.agent_core/harness/src/state/specs.py coding/tests/test_multi_user_assignment.py`
- `git diff --check`

## Key Files Affected

- `coding/.agent_core/harness/src/state/specs.py` - moved whole spec directories during completed/abandoned status transitions before rewriting `spec.md`.
- `coding/tests/test_multi_user_assignment.py` - added regression coverage for preserving extra files and tasks when a spec is moved to completed.
- `.agent_core/logs/benjamin_van_heerden_20260521_101851_session.md` - this work log.
