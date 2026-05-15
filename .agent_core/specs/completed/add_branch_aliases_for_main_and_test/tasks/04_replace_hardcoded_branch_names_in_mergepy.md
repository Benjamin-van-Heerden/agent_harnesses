---
title: Replace hardcoded branch names in merge.py
status: completed
created_at: '2026-02-02T16:10:07.555362'
updated_at: '2026-02-02T16:37:46.831368'
completed_at: '2026-02-02T16:37:46.831361'
---
Update src/commands/merge.py to use get_branch_names() from src/config/models. At the top of each function that references branch names, call branches = get_branch_names() and replace: (1) _merge_into_test(): replace all 'test' with branches.test and 'dev' with branches.dev in switch/pull/merge/push calls and output strings. (2) _merge_into_main(): replace 'main' with branches.main, 'test' with branches.test, 'dev' with branches.dev. (3) into(): replace target validation to use branches.test and branches.main, branch check to use branches.dev. The user-facing target argument should still accept 'test' and 'main' as logical names that map to the configured branch names.

## Completion Notes

Added get_branch_names() import. Updated _merge_into_test(), _merge_into_main(), and into() to use branches.dev/test/main for all git operations and echo strings. User-facing target argument still accepts logical 'test'/'main' names. No remaining hardcoded branch refs except intentional logical target comparisons.