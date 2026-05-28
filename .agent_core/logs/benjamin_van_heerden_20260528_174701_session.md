---
created_at: '2026-05-28T17:47:01.629207'
username: benjamin_van_heerden
---
Work Log - Legal onboard config migration patch

## Overarching Goals

Ensure existing installed legal workspaces receive the new onboard configuration shape, not only fresh installs. The immediate issue was that updating an existing PRAXIS workspace preserved its old `.praxis/config.toml`, so the newly added default `[[tree_dirs]]` entry for `src/` did not appear locally.

## What Was Accomplished

### Added an update patch for existing configs

Added a source-side legal patch, `20260528_add_onboard_config_file_and_tree_sections`, and registered it in `legal/patches/patches.toml`.

The patch targets existing `.praxis/config.toml` files and inserts the onboard configuration block when absent:

```toml
# Files to include in onboard output
# [[files]]
# path = "README.md"
# description = "Practice overview and setup instructions"

# Directories whose tree structure is included in onboard output
[[tree_dirs]]
path = "src"
description = "Reusable Typst source"
```

The patch is idempotent. It does not run if `[[files]]` or active file config already exists and a `tree_dirs` entry for `src` is already present.

### Added regression coverage

Updated the legal setup update test to rewrite the installed test config into the old PRAXIS-style shape, run `setup.py --update`, and assert that the new patch runs and inserts both the commented `[[files]]` scaffold and the active `[[tree_dirs]]` `src` entry.

Verification completed:

```bash
uv run pytest legal/tests/test_setup.py
uvx ruff check legal/setup.py legal/patches legal/tests/test_setup.py
uv run ty check legal/setup.py legal/patches legal/tests/test_setup.py
git diff --check
```

## Key Files Affected

- `legal/patches/patches.toml`: registered the new config migration patch.
- `legal/patches/20260528_add_onboard_config_file_and_tree_sections.py`: adds the update-time migration for existing `.praxis/config.toml` files.
- `legal/tests/test_setup.py`: covers the old config shape and confirms update patches it.

## What Comes Next

After this is merged and pulled by the remote setup flow, existing legal workspaces should receive the config scaffold automatically during update.
