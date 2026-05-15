---
title: Implement branch name selection with validation
status: completed
created_at: '2026-02-11T14:59:13.999013'
updated_at: '2026-02-11T16:59:45.682602'
completed_at: '2026-02-11T16:59:45.682597'
---
Add a helper function (e.g. _select_branches_interactive()) that: (1) Fetches remote branches with 'git branch -r --format=%(refname:short)' and strips 'origin/' prefix. (2) If fewer than 3 remote branches, prints warning that project needs at least main/dev/test branches and exits with error. (3) Lists all remote branches. (4) Prompts for dev, prod, and test branch names using typer.prompt(). (5) Validates each input against the remote branch list — if invalid, shows error and re-prompts. Returns (dev_branch, prod_branch, test_branch) tuple. This will be called at the start of the migrate command.

## Completion Notes

Added _get_remote_branches() and _select_branches_interactive() to light.py. Fetches remote branches, validates minimum 3 exist, lists them, prompts for dev/prod/test with re-prompt on invalid input.