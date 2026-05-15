---
title: Replace hardcoded branch names in specs.py and spec.py
status: completed
created_at: '2026-02-02T16:10:21.291558'
updated_at: '2026-02-02T16:41:43.341237'
completed_at: '2026-02-02T16:41:43.341232'
---
Update src/utils/specs.py: (1) ensure_on_dev_branch(): replace current in ('main', 'test') with current in (branches.main, branches.test), checkout branches.dev. (2) get_branch_diff_stat(): replace branch_name in ('dev', 'main', 'master', 'test') with branch_name in branches.protected — REMOVE 'master'. (3) get_active_spec(): replace current_branch in ('dev', 'main', 'master', 'test') with current_branch in branches.protected — REMOVE 'master'. (4) get_branch_status(): same pattern — REMOVE 'master', use branches.protected. Update src/commands/spec.py: (1) complete(): the rebase onto 'origin/dev' and create_pull_request(base='dev') should use branches.dev (which is always 'dev' but should go through the helper for consistency).

## Completion Notes

Added get_branch_names() import to both files. specs.py: updated ensure_on_dev_branch() to use branches.main/test/dev, updated get_branch_diff_stat/get_active_spec/get_branch_status to use branches.protected (removing all 'master' references). spec.py: updated complete() to use branches.dev for rebase, error messages, and create_pull_request base param.