---
created_at: '2026-03-06T11:32:34.617070'
username: benjamin_van_heerden
---
# Work Log - Add manual merge command

## Overarching Goals

Add a `mem merge manual` command that allows selectively drawing in changes from a spec's PR instead of merging the entire PR. This enables a review loop where the agent and user go through changes file by file and decide what to keep.

## What Was Accomplished

### Added `mem merge manual {slug}` review start command

The command validates we're on dev with a clean working directory, looks up the spec and its linked PR, fetches latest from origin, and produces two outputs:

- **Direct output (stdout)**: Descriptive intro explaining the manual merge process and review loop, PR metadata (title, author, branch, URL, issue), diff stats, pointer to the tmp file, and step-by-step agent instructions for how to proceed (including how to finish with `--finish`).
- **Tmp file (`.mem/tmp/mem_manual_merge_{slug}_{timestamp}.md`)**: File-by-file diffs with `## File: path/to/file` markdown headings for easy navigation via outline tools.

### Added `mem merge manual {slug} --finish "message"` finish command

Mirrors the `spec abandon` flow with manual merge context:

1. `git add -A`, commit with the provided message, push to dev
2. Close the PR with "Abandoned via manual merge" comment including the commit hash and message
3. Close the GitHub issue with abandoned label and comment
4. Remove worktree if one exists
5. Delete branches (local + remote), prune refs
6. Move spec to `abandoned/`
7. Commit and push the spec cleanup

### Updated onboard to mention manual merge

Added a hint alongside the existing `mem merge` suggestion when merge-ready specs are listed: `mem merge manual <slug>` for selective review.

### Broadened tmp file cleanup in onboard

Changed the cleanup in `onboard.py` from only cleaning `mem_onboard_*.md` files (1 hour TTL) to cleaning all `.md` files in `.mem/tmp/`. Onboard files keep the 1-hour TTL, everything else (including manual merge files) uses a 1-week TTL.

## Key Files Affected

- `src/commands/merge.py` — Added `_get_pr_for_spec()`, `_build_manual_merge_tmp_file()`, `_manual_merge_review()`, `_manual_merge_finish()`, and `manual` Typer command. Added imports for `re`, `datetime`, `Path`, `Repo`, `specs`, `close_issue_with_comment`, `close_pull_request`, `get_pull_request_by_url`, `sync_status_labels`.
- `src/commands/onboard.py` — Added manual merge hint in merge-ready specs section. Broadened tmp file cleanup to cover all `.md` files with tiered TTLs.

## What Comes Next

- Commit and push changes to dev
- Test the command against a real spec with an open PR to validate the full flow (review start, review loop, finish)
