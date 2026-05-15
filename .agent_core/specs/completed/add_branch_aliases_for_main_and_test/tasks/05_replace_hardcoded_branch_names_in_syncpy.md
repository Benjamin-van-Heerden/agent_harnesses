---
title: Replace hardcoded branch names in sync.py
status: completed
created_at: '2026-02-02T16:10:14.271238'
updated_at: '2026-02-02T16:39:31.751530'
completed_at: '2026-02-02T16:39:31.751523'
---
Update src/commands/sync.py to use get_branch_names(): (1) sync_protected_branches(): replace branches_to_sync = ['dev', 'test', 'main'] with branches.protected. Replace all 'dev' fallback checkouts with branches.dev. (2) sync_mem_itself(): replace current_branch != 'main' with branches.main, and git pull origin 'main' with branches.main. (3) git_fetch_and_pull(): the rebase onto 'origin/dev' uses the dev branch which stays as-is since dev is fixed. (4) All error-recovery git checkout fallbacks that use 'dev' should use branches.dev.

## Completion Notes

Added get_branch_names() import. Updated sync_protected_branches() to use branches.protected for branch list and branches.dev for all 6 error-recovery fallback checkouts and the final return-to-dev checkout. Updated sync_mem_itself() to use branches.main for current branch check, remote changes check, and git pull. Left git_fetch_and_pull() as-is since it only uses origin/dev which is fixed.