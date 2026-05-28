---
created_at: '2026-05-28T12:08:24.011851'
username: benjamin_van_heerden
---
Work Log - Legal unbound matters, global logs, repair, onboard files, chronology, and patches

## Overarching Goals

Implement the claimed legal harness todos other than onboard performance by aligning `legal/` with the already-in-use `PRAXIS_OUT` workspace shape, adding first-class unbound matter handling, simplifying session work logs, improving legal onboard output, adding lightweight repair guidance, correcting chronology storage, and adding source-controlled update patches for old workspace state.

## What Was Accomplished

### Claimed the legal todos

Claimed the five legal todos and pushed the claims to `dev`, closing their linked GitHub issues:

- `improve_legal_onboard_output_and_work_log_hygiene`
- `remove_legal_src_functions_layout_and_standardize_componentsassets_structure`
- `add_legal_repair_command_for_post_repair_refactor_audits`
- `strengthen_legal_harness_reusable_typst_architecture`
- `add_unbound_support_to_legal_harness`

### Updated legal scaffold layout

Changed `legal/setup.py` so fresh legal installs create the PRAXIS-compatible top-level layout:

```text
UNBOUND/open/
UNBOUND/closed/
assets/
src/components/
src/constants/
src/templates/
src/types/
```

Setup no longer creates `src/functions/`, `src/templates/components/`, or nested component assets for new installs. Existing user-owned folders are not removed during update, preserving backwards compatibility for already-used workspaces such as `PRAXIS_OUT`.

### Added unbound matter support

Added first-class unbound matter support under the existing `matter` command group. `matter new --unbound "<path>"` creates an open unbound matter under `UNBOUND/open/`, treating `/` and `\` as harness-level nesting separators and using the final segment as the matter name. Created unbound matters use the normal matter internals: `info/status.md`, `info/chronology.toml`, obligations, todos, raw, and reference folders.

Added `matter list --unbound`, `matter list --unbound --closed`, and unbound matter lookup/focus support. Runtime lookup also surfaces legacy unbound folders under `UNBOUND/` that are not yet in the new `open/closed` structure as untracked bundles so already-used workspace content does not disappear from onboard.

Added `matter bind <unbound_ref> <client_slug> <matter_type> <matter_slug>` to move an open unbound matter into `ZZ_CLIENTS/<CLIENT>/matters/open/...`, update matter frontmatter, preserve the previous unbound path in `bound_from`, preserve source material/drafts/todos/obligations/chronology, and touch the resulting client matter.

### Simplified work logs and improved onboard

Retired matter-specific work logs. `log new <matter>` now fails with direct guidance that matter-specific context belongs in chronology, obligations, todos, status, raw/reference material, and drafts. Work logs are now global session continuity records only.

Updated legal onboard so it prunes untouched empty logs before surfacing recent global work logs, creates a new global session work log at session start, clearly identifies that current session log, and instructs the agent to read it and update it as work happens. Onboard also surfaces open unbound matters and untracked legacy unbound bundles.

### Added repair workflow

Added repair support with:

- `repair` to inspect relevant git changes since the last repair checkpoint, surface recent global work logs, and print modularization/organization instructions.
- `repair checkpoint` to record the current git HEAD in `.praxis/local_context/repair.toml` for future delta-based audits.

The repair command intentionally audits and instructs rather than blindly rewriting legal content.

### Corrected chronology storage

The user objected to the earlier `info/chronology/<kind>/<timestamp>.toml` layout. Chronology is now a single matter-level TOML file at `info/chronology.toml`; chronology commands append `[[events]]` entries to that file. New matters and unbound matters create the single chronology file immediately. Matter open/resolve/bind lifecycle operations no longer create synthetic chronology events; factual matter history should only be added when the lawyer or source material establishes a real chronology event.

`list_chronology` remains backwards compatible by reading both the new single file and any legacy `info/chronology/<kind>/*.toml` files until a workspace is migrated.

### Added source-side update patches

Added a source-controlled patch mechanism under `legal/patches/` and wired `legal/setup.py --update` to run needed, unapplied patches before refreshing the managed runtime. Patch scripts are not installed into the local `.praxis/harness`; only the workspace-local `.praxis/patches.toml` record is written after a patch runs.

The first patch, `20260528_collapse_chronology_into_single_file`, detects legacy chronology directories under `ZZ_CLIENTS/` and `UNBOUND/`, appends their TOML files to `info/chronology.toml` with `source_path` metadata, preserves extra scalar/list fields as `legacy_*`, and moves the old directory to `info/legacy_chronology` after a successful write.

The setup patch runner makes best-effort git snapshots around patches when git identity is configured:

- `pre-patch snapshot before <patch_id>`
- `patch <patch_id>: <description>`

If git identity is not configured, setup prints that the snapshot was skipped and still runs the patch.

### Updated guidance, docs, lint, and tests

Updated `legal/AGENTS.md`, `legal/README.md`, `.praxis` README template, and Typst house rules to describe unbound matters, root assets, `src/components`, global-only logs, and avoiding `src/functions` for document UI.

Expanded legal lint to report deprecated `src/functions/` and nested `src/templates/components/assets` layouts. Removed `legal/.DS_Store` after the user explicitly approved removing the pre-existing repository noise file.

### Changed legal onboard to write context files

After the initial legal harness changes were committed and pushed, the user requested that legal onboard follow the coding harness pattern: write the full onboard briefing to a temp file instead of streaming the full context to stdout.

Updated legal onboard so it writes the full generated briefing to:

```text
.praxis/tmp/onboard_YYYYMMDD_HHMMSS.md
```

Stdout now prints only the generated file path, line count, and an authoritative instruction that the agent must read the file in full before proceeding. The full context still includes setup warnings, required docs, practice summary, global work logs, unbound matters, obligations, high-priority matters, todos, and agent instructions.

Setup now creates `.praxis/tmp/` and refreshes the managed legal `.gitignore` block so `.praxis/tmp/` is ignored on existing installs as well as fresh installs. The implementation prunes `onboard_*.md` temp files older than one hour.

Verification completed:

```bash
uv run pytest legal/tests/test_setup.py legal/tests/test_clients_matters.py legal/tests/test_onboard.py legal/tests/test_runtime_paths.py legal/tests/test_typst_compile.py legal/tests/test_state_helpers.py legal/tests/test_chronology_obligations_todos.py
uv run pytest legal/tests/test_clients_matters.py legal/tests/test_onboard.py legal/tests/test_runtime_paths.py
uv run pytest legal/tests/test_workflows.py
uv run pytest legal/tests/test_setup.py legal/tests/test_onboard.py legal/tests/test_clients_matters.py legal/tests/test_runtime_paths.py
uvx ruff check legal/.agent_core/harness legal/tests
uv run ty check legal/.agent_core/harness legal/tests
uv run pytest legal/tests/test_setup.py::test_setup_update_runs_needed_source_patches_without_installing_patch_scripts
uv run pytest legal/tests/test_setup.py legal/tests/test_clients_matters.py legal/tests/test_chronology_obligations_todos.py legal/tests/test_state_helpers.py legal/tests/test_runtime_paths.py
uvx ruff check legal/setup.py legal/.agent_core/harness legal/tests legal/patches
uv run ty check legal/setup.py legal/.agent_core/harness legal/tests legal/patches
git diff --check
```

## Key Files Affected

- `legal/setup.py`: creates `UNBOUND/open`, `UNBOUND/closed`, root `assets`, `src/components`, and `.praxis/tmp`; stops creating new `src/functions` and nested component asset directories; refreshes the managed `.gitignore` block so `.praxis/tmp/` is ignored.
- `legal/.agent_core/harness/src/config/paths.py`: adds `unbound_root`, `unbound_open_root`, `unbound_closed_root`, `assets_root`, `src_components_root`, and `tmp_root`.
- `legal/.agent_core/harness/src/state/chronology.py`: writes chronology to `info/chronology.toml` as appended `[[events]]` while still reading legacy per-kind chronology files.
- `legal/.agent_core/harness/src/state/matters.py`: adds unbound matter creation, listing, legacy-bundle detection, open/closed handling, lookup/focus compatibility, close behavior for unbound matters, binding into client matters, and single-file chronology initialization.
- `legal/.agent_core/harness/src/commands/matter/main.py`: adds `matter new --unbound`, `matter list --unbound`, `matter list --unbound --closed`, and `matter bind`.
- `legal/.agent_core/harness/src/commands/onboard/main.py`: surfaces recent global work logs, creates and identifies the current session work log, surfaces open unbound matters, reports untracked legacy unbound bundles, writes full onboard context to `.praxis/tmp/onboard_*.md`, and prints the required read instruction to stdout.
- `legal/.agent_core/harness/src/state/logs.py`: makes work logs global-only and adds recent-global-log listing.
- `legal/.agent_core/harness/src/commands/repair/main.py`: new bare `repair` output and `repair checkpoint` command.
- `legal/.agent_core/harness/src/state/lint.py`: adds deprecated layout checks for `src/functions` and nested component assets.
- `legal/.agent_core/harness/src/state/todos.py` and `legal/.agent_core/harness/src/state/obligations.py`: includes unbound matter todos and obligations in global listing/upcoming obligation flows.
- `legal/.agent_core/harness/src/models/frontmatter.py` and `legal/.agent_core/harness/src/state/models.py`: adds workspace/unbound/binding metadata fields.
- `legal/AGENTS.md`, `legal/README.md`, `legal/.agent_core/README.md`, and `legal/optional_docs/legal_harness_typst_soft_typesystem_and_house_rules.typ`: updated legal harness guidance for the new workspace model.
- `legal/patches/`: source-side update patch manifest and first chronology-collapse patch.
- `legal/tests/*`: updated focused coverage for setup layout, unbound matter creation/listing/onboard/binding, global-only logs, repair command surfacing, paths output, Typst imports, state helper behavior, onboard temp-file output, single-file chronology, and source-side setup patches.

## Errors and Barriers

Initial focused verification failed because a pre-existing `legal/.DS_Store` file violated the repository layout test. Work stopped and the user explicitly approved removing that file. After removal, the focused test set passed.

Ruff found two small style issues after implementation: a multiline `E402` import suppression in `legal/.agent_core/harness/main.py` and an unused `Path` import in the new repair command. Both were corrected, and ruff then passed.

During the onboard temp-file follow-up, `legal/.DS_Store` reappeared and caused the same repository layout assertion to fail. It was removed again under the user's standing approval, and the focused tests passed.

During the chronology/patch follow-up, `.DS_Store` files reappeared under `legal/`, `legal/tests/`, `legal/.agent_core/`, and `legal/.pytest_cache/`. They were removed again under the same standing approval.

## What Comes Next

After this follow-up is committed, pushed, and merged, existing practice workspaces such as `PRAXIS_OUT` should receive the single-file chronology model and migration behavior only through the installed harness update flow, not by direct manual edits.
