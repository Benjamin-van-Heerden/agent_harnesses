---
title: Add branch aliases for main and test
status: completed
assigned_to: Benjamin-van-Heerden
issue_id: 72
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/72
branch: dev-benjamin_van_heerden-add_branch_aliases_for_main_and_test
pr_url: https://github.com/Benjamin-van-Heerden/mem/pull/73
created_at: '2026-02-02T16:08:44.833055'
updated_at: '2026-02-02T16:53:40.236969'
completed_at: '2026-02-02T16:53:40.235154'
last_synced_at: '2026-02-02T16:12:14.260751'
local_content_hash: 8bb31cdd6f2871514914b41f8b6f8a474cc7db18adb580e09311db6ce6e0b26b
remote_content_hash: 8bb31cdd6f2871514914b41f8b6f8a474cc7db18adb580e09311db6ce6e0b26b
---
## Overview

Add configurable branch aliases so projects that don't use `main` and `test` as their production and staging branch names can specify alternatives (e.g., `prod`, `stage`, `master`, `development`, etc.). The `dev` branch is NOT aliased — it always remains `dev` because the worktree/feature-branch naming convention (`dev-{user}-{slug}`) and feature-branch detection (`startswith("dev-")`) are deeply coupled to it.

This addresses GitHub issue #71.

## Goals

- Allow projects to configure custom names for the `main` and `test` branches via `config.toml`
- Add interactive branch name prompts to `mem init`
- Replace all hardcoded `"main"` and `"test"` branch references in source code with config-driven values
- Remove legacy `"master"` branch references (users can alias `main = "master"` if needed)

## Technical Approach

### 1. Config Model (`src/config/models.py`)

Add a new `MemBranchConfig` model and add it to `MemLocalConfig`:

```python
class MemBranchConfig(BaseModel):
    """Branch name aliases for projects with non-standard branch naming."""

    model_config = ConfigDict(extra="ignore")

    main: str = Field(
        default="main",
        description="Name of the production/main branch",
    )

    test: str = Field(
        default="test",
        description="Name of the staging/test branch",
    )
```

Add to `MemLocalConfig`:
```python
branches: MemBranchConfig = Field(
    default_factory=MemBranchConfig,
    description="Branch name aliases",
)
```

The resulting TOML section:
```toml
[branches]
# Name of the production/main branch
main = "main"
# Name of the staging/test branch
test = "test"
```

### 2. Branch Resolution Helper (`src/config/models.py`)

Add a helper dataclass and function to resolve branch names from config. This is the single point of access for branch names throughout the codebase:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class BranchNames:
    dev: str  # always "dev"
    test: str
    main: str

    @property
    def protected(self) -> list[str]:
        """Return all protected branch names."""
        return [self.dev, self.test, self.main]

def get_branch_names() -> BranchNames:
    """Load branch names from config, falling back to defaults."""
    from src.config.main_config import load_and_validate_local_config
    from env_settings import ENV_SETTINGS
    
    result = load_and_validate_local_config(ENV_SETTINGS.config_file)
    if result.config is not None:
        return BranchNames(
            dev="dev",
            test=result.config.branches.test,
            main=result.config.branches.main,
        )
    return BranchNames(dev="dev", test="test", main="main")
```

### 3. Config Generation (`src/config/main_config.py`)

Update `generate_default_config_toml()` to accept `main_branch` and `test_branch` params and render the `[branches]` section:

```toml
[branches]
# Name of the production/main branch
main = "main"
# Name of the staging/test branch
test = "test"
```

### 4. Init Command (`src/commands/init.py`)

**Interactive prompts** — After discovering the repo (step 3), before creating the config (step 6), add prompts:

```python
main_branch = typer.prompt("Main/production branch name", default="main")
test_branch = typer.prompt("Staging/test branch name", default="test")
```

Pass these to `generate_default_config_toml()` and `ensure_branches_exist()`.

**Pre-merge-commit hook** — `create_pre_merge_commit_hook()` must accept the branch aliases and substitute them into the shell script template instead of hardcoded `dev`/`test`/`main`.

**`ensure_branches_exist()`** call changes from:
```python
ensure_branches_exist(ENV_SETTINGS.caller_dir, ["main", "test", "dev"])
```
to:
```python
ensure_branches_exist(ENV_SETTINGS.caller_dir, [main_branch, test_branch, "dev"])
```

### 5. Files That Need Branch Name Updates

Each of these files currently has hardcoded `"main"` and/or `"test"` branch references that must be replaced with values from `get_branch_names()`:

**`src/commands/merge.py`:**
- `_merge_into_test()`: All references to `"test"` and `"dev"` branch names in switch/pull/merge/push
- `_merge_into_main()`: All references to `"main"` and `"test"` and `"dev"` branch names
- `into()`: Target validation `if target not in ("test", "main")` and branch check `if current != "dev"`
- Dry-run output strings referencing branch names

**`src/commands/sync.py`:**
- `sync_protected_branches()`: The `branches_to_sync = ["dev", "test", "main"]` list and the final `git checkout "dev"` fallback
- `sync_mem_itself()`: The `current_branch != "main"` check and `git pull origin "main"`
- Various error-recovery `git checkout dev` fallbacks

**`src/commands/spec.py`:**
- `complete()`: The `git rebase("origin/dev")` and `create_pull_request(base="dev")` calls

**`src/utils/specs.py`:**
- `ensure_on_dev_branch()`: The `current in ("main", "test")` check and `repo.git.checkout("dev")`
- `get_branch_diff_stat()`: The `branch_name in ("dev", "main", "master", "test")` check — remove `"master"`, use config values
- `get_active_spec()`: The `current_branch in ("dev", "main", "master", "test")` check — remove `"master"`, use config values
- `get_branch_status()`: Same pattern — remove `"master"`, use config values

**`src/utils/github/api.py`:**
- `create_pull_request()`: Default `base="dev"` parameter
- `list_merge_ready_prs()`: Default `base_branch="dev"` parameter

**`src/utils/github/git_ops.py`:**
- `ensure_branches_exist()`: Default `branches = ["main", "test", "dev"]`
- `switch_to_branch()`: Default `branch_name="dev"`
- `smart_switch()`: Default `base_branch="dev"`

### 6. Remove `"master"` References

In `src/utils/specs.py`, there are several places that check for `"master"`:
- `get_branch_diff_stat()` line ~315
- `get_active_spec()` line ~355
- `get_branch_status()` line ~391

Remove all `"master"` from these checks. Users who have a branch named `master` can alias it via `branches.main = "master"`.

## Success Criteria

- A project with `[branches] main = "prod"` and `test = "stage"` in config.toml works correctly with all mem commands (init, sync, merge, spec complete, etc.)
- `mem init` prompts for branch names and stores them in config
- Default behavior (no `[branches]` section or default values) is unchanged — existing projects work without modification
- No remaining hardcoded `"master"` references in source code
- The pre-merge-commit hook uses configured branch names
- `get_branch_names()` is the single source of truth for branch names throughout the codebase

## Notes

- `dev` is intentionally NOT aliased. The `dev-{user}-{slug}` branch naming convention and `startswith("dev-")` feature branch detection would break if `dev` were aliased. This is a deliberate design constraint.
- The `get_branch_names()` helper loads config on each call. This is fine for a CLI tool (short-lived process). No caching needed.
- Tests should be left as-is since they test against default branch names which remain `"main"` and `"test"`.
