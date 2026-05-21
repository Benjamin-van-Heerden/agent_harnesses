---
created_at: '2026-05-21T14:13:14.847832'
username: benjamin_van_heerden
---
Work Log - Onboard Mutation Audit And Test Cleanup

## Overarching Goals

Investigate why running `onboard` in another repository visibly churned `.agent_core/`, make onboard surface meaningful `.agent_core` mutations, stop the dangerous branch-checkout behavior that caused the churn, suppress expected tmp-only audit noise, and bring the coding harness tests back into line with the current command behavior.

## What Was Accomplished

### Identified the real onboard churn

Traced the visible file tree churn to normal `onboard` running `sync_all(no_git=False)`, which called `sync_git_state()`, which in turn called `protected_branch_sync()`. The old implementation checked out each protected branch (`dev`, `test`, `main`) to synchronize them, then returned to `dev`. In projects where `.agent_core/` differs across protected branches, that made the working tree visibly delete/recreate/replace files even when final `git status` ended clean.

Updated the protected branch sync behavior so onboard no longer checks out or mutates non-current protected branches. It now fetches remote refs, verifies required branch availability, syncs the current branch when needed, and refuses if a non-current protected branch has local-only commits that require deliberate human inspection. A regression test verifies `main` and `test` can be remote-ahead without their `.agent_core` files appearing in the `dev` working tree.

### Added and refined onboard `.agent_core` mutation auditing

Added an onboard mutation audit that snapshots `.agent_core/` before and after onboard and reports created, modified, and deleted paths in stdout. The audit initially reported directory metadata changes, which made normal Git directory timestamp churn look like content mutation. The audit now treats directory entries as stable unless they are created or deleted, while file contents are still compared by hash.

The audit output was reordered so any `.agent_core` changes appear before the final “read the onboard output” instruction. The final version omits the audit block entirely when the only changes are expected `.agent_core/tmp/` output files, such as newly written onboard context files and old onboard tmp cleanup.

### Cleaned up stale tests

Ran the full coding harness test suite and found stale tests that no longer matched the current harness surface. Updated them to match the current workflow:

- task commands now use the current `--spec` option shape;
- task completion tests pass the hidden explicit-permission flag where required;
- spec completion tests create a work log before completing a spec;
- PR merge tests pass the actual PR URL instead of copying `spec.md` into the main checkout and dirtying the tree;
- local smoke tests no longer exercise `todo new` without a GitHub token, because todo creation now creates linked GitHub issues;
- temp project helpers create all configured protected branches;
- onboard log-selection and dirty-worktree expectations were updated to current behavior;
- obsolete migration tests targeting a deleted `coding/main.py migrate --to-harness` surface were removed.

### Verification

Verification completed during the session:

- `uvx ruff check` on edited harness/test files passed.
- `uv run ty check` on edited harness/test files passed.
- Focused onboard audit tests passed.
- Focused local command and onboard tests passed.
- Focused remote GitHub lifecycle test passed after aligning it with the required work-log workflow.
- `git diff --check` passed.

The last complete full-suite run before the final GitHub lifecycle test adjustment reported `28 passed, 1 failed`; the remaining failure was then fixed and verified with the focused GitHub lifecycle test. A final full-suite rerun was started but the user accepted the state before it completed.

## Key Files Affected

- `coding/.agent_core/harness/src/utils/git.py` - changed protected branch sync so onboard does not checkout or mutate non-current protected branches.
- `coding/.agent_core/harness/src/commands/onboard/main.py` - wired the `.agent_core` mutation audit into onboard and ordered the audit before the final read-output instruction.
- `coding/.agent_core/harness/src/commands/onboard/mutations.py` - added mutation snapshot/diff/render helpers, ignored directory mtime-only churn, and suppressed tmp-only mutation blocks.
- `coding/tests/test_git_sync.py` - added regression coverage proving protected branch sync does not checkout or mutate non-current protected branches.
- `coding/tests/test_onboard.py` - added and updated onboard audit coverage, dirty-worktree expectations, log selection expectations, and tmp-only suppression assertions.
- `coding/tests/helpers.py` - fixed test helper project root usage and ensured temp git projects create all protected branches.
- `coding/tests/test_github_flow.py` - updated remote lifecycle test to current task/log/spec/merge workflow.
- `coding/tests/test_local_commands.py` - updated local smoke test for current dev-branch, task, memory, log, and onboard behavior.
- `coding/tests/test_migration.py` and `coding/tests/test_remote_migration.py` - removed obsolete tests for the deleted legacy migration CLI surface.

## Errors and Barriers

The first audit implementation conflated directory metadata churn with meaningful file changes. That made it look like dozens of `.agent_core` paths were modified when many entries were only directories whose metadata changed during Git operations. The audit was corrected to ignore directory mtime-only changes.

The initial branch-sync fix still fast-forwarded non-current protected branch refs. The user correctly challenged this; onboard should inspect remote refs, not mutate non-current branches. The implementation was tightened so non-current protected branch refs are not updated during onboard.

The full test suite exposed several stale tests unrelated to the core onboard fix. These were updated or removed rather than weakening current production behavior.
