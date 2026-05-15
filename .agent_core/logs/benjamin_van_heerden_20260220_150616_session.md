---
created_at: '2026-02-20T15:06:16.593816'
username: benjamin_van_heerden
---
# Work Log - Add tree_dirs config option

## Overarching Goals

Implement a new `[[tree_dirs]]` config option in `.mem/config.toml` that prints recursive directory tree listings in the onboard output. This addresses the "Add tree dirs config" todo (GitHub issue #88).

## What Was Accomplished

### Added MemTreeDir model and config field

Added `MemTreeDir` Pydantic model to `src/config/models.py` (mirrors `MemImportantFile` with `path` + optional `description`) and a `tree_dirs: list[MemTreeDir]` field on `MemLocalConfig`.

### Added tree rendering to onboard

Added `build_directory_tree()` function in `src/commands/onboard.py` — a recursive tree renderer that produces `tree`-command-style output. Filters out common noise directories (`__pycache__`, `node_modules`, `.venv`, `.git`, etc.). Directories are listed first (sorted alphabetically), then files.

The onboard output renders a "DIRECTORY TREES" section right after "Important Files" and before "Core Documentation", wrapping each tree in a code block.

### Updated config generation and patch preservation

- `generate_default_config_toml()` in `src/config/main_config.py` now accepts a `tree_dirs` parameter and generates `[[tree_dirs]]` TOML entries.
- `_extract_known_values()` in `src/commands/patch.py` now extracts `tree_dirs` from raw config so entries are preserved during patching.
- `_filter_valid_files()` is reused for validating `tree_dirs` entries (same `path`/`description` structure).

### Drift detection

No changes needed — `find_unknown_key_paths` works generically against the model schema. Verified that unknown keys within `[[tree_dirs]]` entries are correctly detected and removed by patch.

### Claimed todo

Claimed and closed "Add tree dirs config" (GitHub issue #88).

## Key Files Affected

- `src/config/models.py` — Added `MemTreeDir` model and `tree_dirs` field on `MemLocalConfig`
- `src/commands/onboard.py` — Added `build_directory_tree()` function and directory trees section in onboard output
- `src/config/main_config.py` — Added `tree_dirs` parameter to `generate_default_config_toml()`
- `src/commands/patch.py` — Added `tree_dirs` extraction in `_extract_known_values()` and pass-through to config generation

## What Comes Next

- Changes need to be committed and pushed to `dev`.
- Could consider adding a `max_depth` option to `MemTreeDir` for very deep directory structures, but not needed unless it becomes a problem.
