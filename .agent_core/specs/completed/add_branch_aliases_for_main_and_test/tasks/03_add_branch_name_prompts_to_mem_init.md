---
title: Add branch name prompts to mem init
status: completed
created_at: '2026-02-02T16:10:00.057255'
updated_at: '2026-02-02T16:34:44.054233'
completed_at: '2026-02-02T16:34:44.054224'
---
Update the init() function in src/commands/init.py: (1) After step 4 (git config discovery), add prompts: main_branch = typer.prompt('Main/production branch name', default='main') and test_branch = typer.prompt('Staging/test branch name', default='test'). (2) Pass main_branch and test_branch to generate_default_config_toml() in the create_config_with_discovery call. (3) Change ensure_branches_exist() call from ['main', 'test', 'dev'] to [main_branch, test_branch, 'dev']. (4) Change switch_to_branch() to still switch to 'dev'. (5) Update create_pre_merge_commit_hook() to accept main_branch and test_branch params and substitute them into the shell script instead of hardcoded 'test' and 'main' in the case statement. The create_config_with_discovery function will also need to accept and pass through the branch params.

## Completion Notes

Added branch name prompts after step 4 in init(). Updated create_config_with_discovery() to accept and pass main_branch/test_branch to generate_default_config_toml(). Changed ensure_branches_exist() from hardcoded list to [main_branch, test_branch, 'dev']. Updated create_pre_merge_commit_hook() to accept branch params and substitute them into the shell script template. All call sites updated.