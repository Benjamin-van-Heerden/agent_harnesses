---
created_at: '2026-03-06T14:27:16.737482'
username: benjamin_van_heerden
---
# Work Log - Fix manual merge PR lookup and diff resolution

## Overarching Goals

Fix two bugs in `mem merge manual` that prevented it from working when the spec's PR metadata wasn't pre-populated and when the feature branch only existed as a remote tracking ref.

## What Was Accomplished

### Fixed PR lookup in `_get_pr_for_spec`

The function previously required `pr_url` in the spec's frontmatter, but this field only gets set during `mem spec complete`. When running `mem merge manual` from dev, the spec file on dev doesn't have `pr_url` set, so the command would fail immediately.

Updated the function to first try `pr_url`, and if unavailable, fall back to searching GitHub's open PRs targeting dev for one whose head branch matches the spec's `branch` field. This mirrors how the base `mem merge` command finds PRs.

### Fixed empty diff in `_build_manual_merge_tmp_file`

The function was running `git diff dev...{branch_name}` using the bare branch name (e.g. `dev-marcobooysep-user_dashboard_ui`). When the feature branch only exists as a remote tracking ref (`remotes/origin/dev-marcobooysep-...`) and not as a local branch, git can't resolve the bare ref and the diff returns empty — causing "No changes detected."

Fixed by using `origin/{branch_name}` as the ref in all three `git diff` calls. Since `_fetch_origin()` is already called before this function, the remote tracking refs are up to date.

## Key Files Affected

- `src/commands/merge.py` — `_get_pr_for_spec()`: added branch-based PR lookup fallback; `_build_manual_merge_tmp_file()`: changed diff refs from bare branch name to `origin/{branch_name}`

## What Comes Next

- Commit and push changes to dev
- Test the fixes against the studii project's `user_dashboard_ui` spec to confirm the manual merge flow works end-to-end
