---
created_at: '2026-02-02T16:51:06.049275'
username: benjamin_van_heerden
spec_slug: add_branch_aliases_for_main_and_test
---
# Work Log - Add configurable branch aliases for main and test

## Overarching Goals

Allow projects to configure custom names for the `main` and `test` branches via `config.toml`, so projects using branch names like `prod`, `stage`, `master`, etc. can work with mem. The `dev` branch remains fixed since the worktree/feature-branch naming convention is coupled to it.

## What Was Accomplished

### Config Model and Helper

Added `MemBranchConfig` Pydantic model with `main` (default `"main"`) and `test` (default `"test"`) fields to `src/config/models.py`. Added it as a `branches` field on `MemLocalConfig` with `default_factory`. Created a `BranchNames` frozen dataclass with a `protected` property returning `[dev, test, main]`, and a `get_branch_names()` function that loads from config with lazy imports to avoid circular dependencies.

### Config Generation

Updated `generate_default_config_toml()` to accept `main_branch` and `test_branch` params and render a `[branches]` section with comments from field descriptions.

### Init Command

Added interactive `typer.prompt()` calls for branch names after step 4 in `init()`. Updated `create_config_with_discovery()`, `ensure_branches_exist()`, and `create_pre_merge_commit_hook()` to accept and use the configured branch names. The hook shell script is now an f-string with branch names substituted.

### Branch Name Replacement Across Codebase

Replaced all hardcoded `"main"`, `"test"`, and `"dev"` branch references with `get_branch_names()` in:
- `src/commands/merge.py` - `_merge_into_test()`, `_merge_into_main()`, `into()`
- `src/commands/sync.py` - `sync_protected_branches()`, `sync_mem_itself()`
- `src/utils/specs.py` - `ensure_on_dev_branch()`, `get_branch_diff_stat()`, `get_active_spec()`, `get_branch_status()`
- `src/commands/spec.py` - `complete()` rebase and PR creation
- `src/utils/github/git_ops.py` - `ensure_branches_exist()` default

### Removed `"master"` References

All `"master"` references in `src/utils/specs.py` were removed from branch checks. Users who need `master` can alias it via `branches.main = "master"`.

### Patch Config Fix

Updated `src/commands/patch.py` to detect missing `[branches]` section, extract existing branch values, and pass them through when regenerating config. Without this fix, `mem patch config` would not add the new section to existing configs.

## Key Files Affected

- `src/config/models.py` - Added `MemBranchConfig`, `BranchNames`, `get_branch_names()`
- `src/config/main_config.py` - Added `main_branch`/`test_branch` params to `generate_default_config_toml()`
- `src/commands/init.py` - Branch prompts, updated `create_config_with_discovery()`, `create_pre_merge_commit_hook()`, `ensure_branches_exist()` call
- `src/commands/merge.py` - All three merge functions use `get_branch_names()`
- `src/commands/sync.py` - `sync_protected_branches()` and `sync_mem_itself()` use config-driven values
- `src/utils/specs.py` - Four functions updated, `"master"` removed
- `src/commands/spec.py` - `complete()` uses `get_branch_names()` for rebase and PR
- `src/utils/github/git_ops.py` - `ensure_branches_exist()` default uses config
- `src/commands/patch.py` - Detects/preserves/passes branch config values

## What Comes Next

All 7 spec tasks are complete plus the patch config fix. The spec is ready for completion via `mem spec complete`.
