---
created_at: '2026-05-27T11:28:29.423426'
username: benjamin_van_heerden
spec_slug: legal_harness_layout_and_test_suite_overhaul
---
Work Log - Legal Runtime Paths, Test Split, And Verification

## Overarching Goals

Complete the remaining `legal_harness_layout_and_test_suite_overhaul` spec work after the previous session had already expanded legal AGENTS guidance, restructured the template tree, and moved setup installs to `.praxis/`. This session focused on bringing the installed runtime into alignment with `.praxis/`, replacing stale test expectations, splitting the large legal test module into focused files, and verifying the overhaul.

## What Was Accomplished

### Legal Runtime Paths

Updated the installed legal runtime path model so `find_project_root()` identifies workspaces by `.praxis/` instead of `.agent_core/`. `ProjectPaths` now resolves the installed namespace as:

```text
.praxis/
  config.toml
  core_docs/
  docs/
  harness/
    templates/
  local_context/
    logs/
    memories/
    workflows/
  todos/
    open/
    claimed/
```

Runtime paths now point to `.praxis/core_docs/legal_context.typ`, `.praxis/docs/typst_detailed_reference.typ`, and `.praxis/harness/templates/`. Lawyer/practice-local records now resolve under `.praxis/local_context/`.

Updated the `paths` command so it reports state, harness, core docs, docs, local context, clients, WIP, and Typst source roots using `.praxis/`.

Updated onboard required-doc handling so it no longer depends on or prints `legal_harness_function.md`. Routine onboard now reads only the core legal context from `.praxis/core_docs/legal_context.typ`.

Refreshed `legal/optional_docs/legal_harness_function.md` so the optional reference doc also uses `.praxis/harness/main.py`, `.praxis/todos`, `.praxis/client_matter_index.toml`, `.praxis/local_context/workflows`, and `.praxis/docs`.

### Legal Test Suite Split

Split the former single large `legal/tests/test_setup.py` into focused modules:

- `legal/tests/helpers.py`
- `legal/tests/test_setup.py`
- `legal/tests/test_runtime_paths.py`
- `legal/tests/test_onboard.py`
- `legal/tests/test_clients_matters.py`
- `legal/tests/test_chronology_obligations_todos.py`
- `legal/tests/test_workflows.py`
- `legal/tests/test_typst_compile.py`
- `legal/tests/test_state_helpers.py`

Updated all test expectations for the installed `.praxis/` namespace. The tests now assert fresh installs do not create installed `.agent_core/` or `.agent_docs/`, that legal core docs live under `.praxis/core_docs/`, detailed and optional docs live under `.praxis/docs/`, lawyer-owned context lives under `.praxis/local_context/`, and harness templates live under `.praxis/harness/templates/`.

Removed legacy `agent_rules` migration test coverage because backwards compatibility is intentionally out of scope for this legal harness overhaul.

Added template layout coverage for `legal/.agent_core/core_docs`, `legal/.agent_core/docs`, `legal/.agent_core/local_context`, and `legal/.agent_core/harness/templates`.

Added optional-doc coverage confirming `legal_harness_function.md` is listed and can be installed on request, but is not part of default installed onboard context.

### Verification

Ran focused verification for the changed legal harness areas:

```bash
uv run pytest --collect-only legal/tests
uvx ruff format legal/tests
uv run pytest legal/tests
uvx ruff check legal/.agent_core/harness legal/tests
uv run ty check legal/.agent_core/harness legal/tests
git diff --check
```

Final verification state:

- `uv run pytest legal/tests`: 20 passed.
- `uvx ruff check legal/.agent_core/harness legal/tests`: passed.
- `uv run ty check legal/.agent_core/harness legal/tests`: passed.
- `git diff --check`: passed.

Marked the remaining spec tasks complete:

- `update_legal_runtime_paths_and_command_output`
- `split_and_expand_legal_harness_tests`
- `verify_legal_layout_overhaul`

## Key Files Affected

- `legal/.agent_core/harness/src/config/paths.py`: changed installed root detection and all legal runtime state paths from `.agent_core`, `.agent_docs`, and `practice` to `.praxis`, `core_docs`, `docs`, `local_context`, and harness `templates`.
- `legal/.agent_core/harness/main.py`: updated `paths` command output to show the new core docs and local context roots.
- `legal/.agent_core/harness/src/commands/onboard/main.py`: removed `legal_harness_function.md` from routine required docs.
- `legal/optional_docs/legal_harness_function.md`: updated optional reference examples to match `.praxis/`.
- `legal/tests/helpers.py`: new shared command runner, setup runner, TOML reader, ASCII assertion, and installed harness command helper.
- `legal/tests/test_setup.py`: narrowed to setup/dependency/layout/docs behavior and updated default install/update assertions for `.praxis/`.
- `legal/tests/test_runtime_paths.py`: new focused runtime command/path/config coverage.
- `legal/tests/test_onboard.py`: new focused onboard/session-log/git-snapshot coverage.
- `legal/tests/test_clients_matters.py`: new focused client, matter, lookup, ambiguity, touch tracking, and context command coverage.
- `legal/tests/test_chronology_obligations_todos.py`: new focused bookkeeping command coverage.
- `legal/tests/test_workflows.py`: new focused workflow command and matter focus integration coverage.
- `legal/tests/test_typst_compile.py`: new focused compile and PDF classification coverage.
- `legal/tests/test_state_helpers.py`: new focused frontmatter and state helper coverage.
- `.agent_core/specs/legal_harness_layout_and_test_suite_overhaul/tasks/04_update_legal_runtime_paths_and_command_output.md`: marked complete.
- `.agent_core/specs/legal_harness_layout_and_test_suite_overhaul/tasks/05_split_and_expand_legal_harness_tests.md`: marked complete.
- `.agent_core/specs/legal_harness_layout_and_test_suite_overhaul/tasks/06_verify_legal_layout_overhaul.md`: marked complete.

## Errors and Barriers

The first smoke install in `/private/tmp/legal-harness-runtime-smoke-20260527` failed under the default sandbox when `git init` attempted to create `.git`. Rerunning the setup command with elevated filesystem permissions succeeded.

The first pytest collection after splitting tests failed because the new modules imported helpers as `legal.tests.helpers`, while pytest selected `legal/` as `rootdir`. Switching imports to `from helpers import ...` fixed collection.

An initial `uvx ty check legal/.agent_core/harness legal/tests` failed because `uvx` ran ty in an isolated environment without legal harness dependencies such as `typer`, `pydantic`, and `yaml`. Running `uv run ty check legal/.agent_core/harness legal/tests` in the project environment passed.

## What Comes Next

All implementation and verification tasks for the `legal_harness_layout_and_test_suite_overhaul` spec are complete. The remaining step is spec completion and PR creation.
