---
created_at: '2026-03-16T11:18:11.853870'
username: benjamin_van_heerden
---
# Work Log - Update mem lite complete spec with PR workflow

## Overarching Goals

Address todo #100: update the mem lite system so that spec completion uses actual GitHub PRs instead of local merges, and add supporting commands for merging and branch cleanup.

## What Was Accomplished

### Updated `c_complete_spec.md` for PR workflow

- On feature branch: status now goes to `Merge Ready` (not `Completed`), rebases onto dev, pushes, creates PR via `gh pr create`. Stops after PR creation.
- Not on feature branch: unchanged — status → `Completed`, move to `completed/`, commit.
- Added `which gh` check before PR creation with install/auth guidance.

### Created `c_merge.md`

New command that:
- Finds specs with `Merge Ready` status
- Checks `gh` is installed (hard requirement)
- Finds the open PR for the spec's branch
- Squash-merges via `gh pr merge --squash --delete-branch`
- Syncs local: `git switch $dev_branch && git pull origin $dev_branch`
- Moves spec to `completed/`, commits
- Calls `c_clean_git` for branch cleanup

### Created `c_clean_git.md`

New command that:
- Fetches and prunes remote refs
- Finds branches merged into `$dev_branch`
- Excludes protected branches (`$dev_branch`, `$prod_branch`, `$test_branch`)
- Deletes local and remote merged branches

### Updated `c_onboard.md`

- Added "Check for Open PRs" section after branch/sync check
- Uses `which gh` with soft warning if not installed (non-blocking)

### Updated `c_abandon_spec.md`

- Added "Close PR if Exists" section after moving spec to abandoned
- Checks for `Branch:` line in spec, closes any open PR via `gh pr close`
- Soft `gh` check — warns if not installed, doesn't block abandonment

### Updated `AGENTS.md`

- Added `c_merge` and `c_clean_git` to directory listing and command table
- Updated `c_complete_spec` and `c_abandon_spec` descriptions

### Claimed todo #100

Closed GitHub issue #100.

## Key Files Affected

- `src/templates/mem_lite/agent_rules/commands/c_complete_spec.md` — Reworked for PR workflow with `Merge Ready` status
- `src/templates/mem_lite/agent_rules/commands/c_merge.md` — New file: squash-merge PR, sync local, finalize spec
- `src/templates/mem_lite/agent_rules/commands/c_clean_git.md` — New file: delete merged branches
- `src/templates/mem_lite/agent_rules/commands/c_onboard.md` — Added open PR check
- `src/templates/mem_lite/agent_rules/commands/c_abandon_spec.md` — Added PR close on abandon
- `src/templates/mem_lite/AGENTS.md` — Updated command table and directory listing

## What Comes Next

- Commit and push changes to dev
- Consider testing the workflow end-to-end in a mem lite project
