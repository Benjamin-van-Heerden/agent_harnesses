---
created_at: '2026-03-26T11:33:07.382656'
username: benjamin_van_heerden
---
# Work Log - Unified migrate command with bidirectional mem/lite conversion

## Overarching Goals

Consolidate the migration functionality between mem (`.mem/`) and mem lite (`agent_rules/`) into a single unified `mem migrate` command with `--mem-to-lite` and `--lite-to-mem` flags. The old `mem migrate` was a hidden legacy command that used AI parsers for an outdated agent_rules format. The `mem lite migrate` subcommand only went one direction. Both needed to be replaced with a clean, deterministic, bidirectional solution.

## What Was Accomplished

### Rewrote `src/utils/migrate.py` with deterministic parsers

Replaced the old AI-parser-based migration utility entirely. The new module includes:

- Deterministic parsers for all mem lite file formats: specs (with `%% Status %%` inline markers and `###` task sections), todos (with `**Status:**` metadata), logs (with `# Work Log -` title pattern), and memories
- `convert_lite_specs()` — parses lite spec files including inline tasks, maps lite statuses (`Active`/`Merge Ready`/`Completed`/`Abandoned`) to mem statuses (`todo`/`merge_ready`/`completed`/`abandoned`), creates proper `.mem/specs/` directory structure with separate task files
- `convert_lite_logs()`, `convert_lite_todos()`, `convert_lite_memories()`, `convert_lite_docs()` — handle all other entity types
- `run_lite_to_mem()` — full orchestrator with dry-run support, branch detection from AGENTS.md, config.toml generation
- `run_mem_to_lite()` — delegates to existing helpers in `lite.py`, also with dry-run support

### Rewrote `src/commands/migrate.py` as unified command

New command with mutually exclusive `--mem-to-lite` / `--lite-to-mem` flags and `--dry-run` support. Replaces the old hidden legacy command.

### Fixed STATUS_MAP bug in `lite.py`

`merge_ready` was incorrectly mapped to `"Completed"` instead of `"Merge Ready"` in the mem-to-lite direction.

### Removed `migrate` subcommand from `lite.py`

The `mem lite migrate` command was removed since this functionality now lives under the unified `mem migrate --mem-to-lite`.

### Unhid `migrate` in `main.py`

Changed from `hidden=True` to a visible command with proper help text.

## Key Files Affected

- `src/utils/migrate.py` — Complete rewrite: deterministic parsers for mem lite format, bidirectional migration orchestrators
- `src/commands/migrate.py` — Complete rewrite: unified command with `--mem-to-lite` / `--lite-to-mem` flags
- `src/commands/lite.py` — Fixed `STATUS_MAP` (`merge_ready` → `"Merge Ready"`), removed `migrate` subcommand
- `main.py` — Unhid `migrate` command

## What Comes Next

- Commit and push these changes to dev
- Consider end-to-end testing on a real mem lite project to validate the full round-trip (mem → lite → mem)
- The old `src/utils/ai/spec_parser.py` and `src/utils/ai/log_parser.py` are no longer used by migrate — could be cleaned up if not used elsewhere
