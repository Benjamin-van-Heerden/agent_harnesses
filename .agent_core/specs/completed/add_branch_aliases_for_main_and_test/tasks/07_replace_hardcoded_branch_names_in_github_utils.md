---
title: Replace hardcoded branch names in github utils
status: completed
created_at: '2026-02-02T16:10:28.319892'
updated_at: '2026-02-02T16:42:59.804840'
completed_at: '2026-02-02T16:42:59.804833'
---
Update src/utils/github/git_ops.py: (1) ensure_branches_exist(): change default from ['main', 'test', 'dev'] to None and use get_branch_names().protected when None. (2) switch_to_branch(): keep default='dev' since dev is fixed. (3) smart_switch(): keep default base_branch='dev' since dev is fixed. Update src/utils/github/api.py: (1) create_pull_request(): keep default base='dev' since dev is fixed. (2) list_merge_ready_prs(): keep default base_branch='dev' since dev is fixed. These defaults are all 'dev' which remains fixed, so the changes here are minimal — just update ensure_branches_exist() to use config-driven values.

## Completion Notes

Updated ensure_branches_exist() default from hardcoded ['main', 'test', 'dev'] to get_branch_names().protected with lazy import. No changes to api.py or other git_ops functions since they all default to 'dev' which is fixed by design.