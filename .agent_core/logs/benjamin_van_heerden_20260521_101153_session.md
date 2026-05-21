---
created_at: '2026-05-21T10:11:53.970887'
username: benjamin_van_heerden
---
Work Log - Idempotent Issue Sync Action Counts

## Overarching Goals

Investigate why a freshly migrated project showed `Issue sync complete. Actions: 2` on every coding harness onboard, explain what the action count meant, and fix the harness so repeated no-op GitHub issue reconciliation does not look like real work.

## What Was Accomplished

### Clarified repeated action counts

Traced the onboard output to `sync_all() -> issues() -> _sync_specs() + _sync_todos()` in the coding harness. The sync code previously called `update_issue()` for every local spec or todo with a matching open GitHub issue, then incremented the action counter unconditionally. That meant a migrated project with two already-linked open records could report `Actions: 2` on every onboard even when remote issue title, body, labels, and state were already correct.

### Made issue sync idempotent

Updated spec and todo issue synchronization so linked open issues are only edited when their current remote state differs from desired local state. The comparison now checks:

- issue title;
- issue body;
- exact label set;
- issue state for todos, where claimed todos should close the issue.

The action counter now represents actual creations, imports, or remote edits instead of repeated no-op edit calls.

### Added focused regression coverage

Added tests covering both sides of the behavior:

- a matching remote spec issue produces zero actions and does not call `update_issue()`;
- a stale remote todo issue still produces one action and calls `update_issue()`.

Verification performed:

- `uvx ruff check coding/.agent_core/harness/src/commands/sync/main.py coding/tests/test_sync_issues.py`
- `uv run pytest coding/tests/test_sync_issues.py`
- `uv run ty check coding/.agent_core/harness/src/commands/sync/main.py coding/tests/test_sync_issues.py`
- `git diff --check`

## Key Files Affected

- `coding/.agent_core/harness/src/commands/sync/main.py` - added remote issue comparison helpers and gated spec/todo `update_issue()` calls behind real state changes.
- `coding/tests/test_sync_issues.py` - new focused unit tests for no-op and stale issue sync behavior.
- `.agent_core/logs/benjamin_van_heerden_20260521_101153_session.md` - this work log.

## What Comes Next

Propagate the coding harness template update into installed projects after the change is committed and pushed. In the affected migrated project, a subsequent onboard should report `Actions: 0` unless there is an actual local/remote issue drift to reconcile.
