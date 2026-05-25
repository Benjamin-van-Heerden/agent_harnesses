---
created_at: '2026-05-25T16:50:25.730355'
username: benjamin_van_heerden
---
Work Log - Completed spec remote branch cleanup

## Overarching Goals

Fix a coding harness cleanup gap where a spec PR merged manually through the GitHub UI could leave its remote spec branch behind. The immediate symptom was that `git branch -a` still showed `origin/dev-benjamin_van_heerden-migrate_legal_harness_to_native_agent_core_structure` even though the corresponding spec had already been completed.

## What Was Accomplished

### Diagnosed the missing cleanup path

Inspected the coding harness sync and merge flows. The harness-managed merge path already deleted the remote branch through `delete_remote_branch()`, but the onboard/sync path that detects externally merged PRs only marked the local spec completed and removed the local worktree/local branch. It did not delete the remote branch.

Also confirmed that the specific stale branch still existed on GitHub with:

```bash
git ls-remote --heads origin dev-benjamin_van_heerden-migrate_legal_harness_to_native_agent_core_structure
```

That meant the problem was not just a stale local tracking ref.

### Added remote cleanup for externally merged specs

Updated `_complete_merged_specs()` so when sync sees a `merge_ready` spec PR has been merged externally, it now deletes the recorded remote spec branch as well as the local worktree/local branch.

After deleting a remote branch, sync now runs `git prune()` best-effort so stale `origin/...` tracking refs are removed from local `git branch -a` output.

### Added cleanup for already-completed specs

Added `_cleanup_completed_spec_branches()` so normal sync also revisits specs that are already marked `completed`. This covers older remnants like the completed legal harness native migration branch, where the spec state was already completed before this cleanup logic existed.

The cleanup only runs from the main repo on the configured `dev` branch, skips spec worktrees, skips protected branches, removes matching local worktrees/local branches when present, deletes the matching remote branch when present, and counts only actual cleanup actions.

### Adjusted GitHub helper semantics

Changed `delete_remote_branch()` to return `True` when it deleted a branch and `False` when the branch was already absent. This lets sync avoid reporting cleanup when there was nothing to remove, while preserving the existing behavior of raising a `GitHubError` for non-404 GitHub failures.

### Installed harness update

Ran `python -B coding/setup.py --update` from the project root to propagate the coding template changes into the installed `.agent_core/harness` runtime. This refreshed installed sync and GitHub helper modules and updated `.agent_core/config.toml`'s harness `last_updated_at` timestamp.

Verification completed:

- `uvx ruff check coding/.agent_core/harness/src/commands/sync/main.py coding/.agent_core/harness/src/utils/github.py`
- `uv run ty check coding/.agent_core/harness/src/commands/sync/main.py coding/.agent_core/harness/src/utils/github.py`

## Key Files Affected

- `coding/.agent_core/harness/src/commands/sync/main.py` - deletes remote branches for externally merged specs, adds completed-spec branch cleanup, prunes remote-tracking refs after remote deletion, and reports completed branch cleanup counts.
- `coding/.agent_core/harness/src/utils/github.py` - makes `delete_remote_branch()` return whether it deleted a branch while treating missing branches as a non-error `False`.
- `.agent_core/harness/src/commands/sync/main.py` - refreshed installed runtime copy from the coding template.
- `.agent_core/harness/src/utils/github.py` - refreshed installed runtime copy from the coding template.
- `.agent_core/config.toml` - updated by setup with the latest harness `last_updated_at` timestamp.
