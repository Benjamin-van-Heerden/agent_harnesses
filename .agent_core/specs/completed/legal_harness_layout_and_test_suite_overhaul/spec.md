---
title: Legal harness layout and test suite overhaul
status: completed
assigned_to: Benjamin-van-Heerden
issue_id: 21
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/21
branch: dev-benjamin_van_heerden-legal_harness_layout_and_test_suite_overhaul
pr_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/pull/22
created_at: '2026-05-26T14:32:58.030242'
updated_at: '2026-05-27T12:11:11.165290'
completed_at: '2026-05-27T12:11:11.165290'
last_synced_at: null
local_content_hash: null
remote_content_hash: null
---
## Overview

Rework the legal harness template, installed workspace namespace, agent-facing guidance, and tests so the legal harness is easier to reason about before wider use.

The legal harness is not yet broadly distributed. Do not spend implementation effort on migration, compatibility shims, or preserving existing installed `.agent_core/` legal workspaces. The one current guinea-pig workspace can be manually restructured outside this change if necessary.

This spec combines the two claimed todos:

- Expand the legal harness test suite into clear, behavior-focused files instead of one large catch-all test module.
- Surface the legal command and operating model guidance directly in `legal/AGENTS.md` instead of depending on onboard output or optional docs for core workflow rules.

It also changes the legal installed namespace from `.agent_core/` to `.praxis/`, while keeping `legal/.agent_core/` as the template source directory inside this repository for consistency with the other harness templates.

## Goals

- Make `legal/AGENTS.md` self-contained for routine agent operation by folding in the practical content currently held in `legal/optional_docs/legal_harness_function.md`.
- Keep the source repository layout consistent with other harness templates while making legal-specific directories clearer:
  - keep `legal/.agent_core/` as the template/runtime source root;
  - rename template core docs from `legal/.agent_core/docs/` to `legal/.agent_core/core_docs/`;
  - rename template practice defaults from `legal/.agent_core/practice/` to `legal/.agent_core/local_context/`;
  - move harness scaffolding templates from `legal/.agent_core/practice/templates/` to `legal/.agent_core/harness/templates/`;
  - move `legal/.agent_docs/` into `legal/.agent_core/docs/`;
  - delete `legal/.DS_Store`.
- Install legal workspaces with `.praxis/` as the managed state/runtime namespace, not `.agent_core/`.
- Preserve the installed top-level legal workspace shape:
  - `.praxis/`
  - `src/`
  - `WIP/`
  - `ZZ_CLIENTS/`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `.gitignore`
- Update runtime path resolution, setup output, onboard output, command guidance, auto-update, docs commands, and README text to use the new legal namespace and directory names.
- Split and expand `legal/tests/test_setup.py` into focused files that make the legal harness behavior easier to inspect and maintain.

## Technical Approach

### Agent Guidance

Move the substance of `legal/optional_docs/legal_harness_function.md` into the managed block in `legal/AGENTS.md`. The installed AGENTS guidance should use the legal installed entrypoint:

```bash
python -B .praxis/harness/main.py onboard
python -B .praxis/harness/main.py compile <source.typ>
```

The AGENTS content should retain the lawyer-facing contract, command shape, state model, action triggers, chronology/obligation/todo/memory distinctions, drafting rules, WIP rules, Typst compile rule, and confidentiality guidance. It should no longer tell agents that core legal workflow guidance lives in `.agent_core/docs/legal_harness_function.md`.

The optional doc file may remain in `legal/optional_docs/` as a reference artifact if useful, but the installed harness must not depend on it for core instructions.

### Repository Template Layout

Restructure the `legal/` template directory to this shape:

```text
legal/
  .agent_core/
    README.md
    core_docs/
      legal_context.typ
    docs/
      typst_detailed_reference.typ
    harness/
      deps.py
      main.py
      requirements.txt
      templates/
        log.md
        memory.md
        profile.md
        status.md
        todo.md
      src/
      update.py
    local_context/
      lawyer_profile.md
  AGENTS.md
  README.md
  optional_docs/
  setup.py
  src/
  tests/
```

Keep `legal/.agent_core/` named as-is in this repository. Only installed legal workspaces use `.praxis/`.

### Installed Workspace Layout

Fresh install should create and update legal workspaces using `.praxis/`:

```text
.praxis/
  README.md
  config.toml
  core_docs/
    legal_context.typ
  docs/
    typst_detailed_reference.typ
    legal_harness_typst_basic_reference.typ
    legal_harness_typst_soft_typesystem_and_house_rules.typ
  harness/
  local_context/
    lawyer_profile.md
    memories/
    logs/
    workflows/
  todos/
    open/
    claimed/
  client_matter_index.toml
src/
WIP/
ZZ_CLIENTS/
AGENTS.md
CLAUDE.md
.gitignore
```

The runtime should treat `.praxis/` as the state root. `find_project_root()` should identify installed legal workspaces by `.praxis/`, not `.agent_core/`.

Harness-owned templates should be loaded from `.praxis/harness/templates/`. Lawyer/practice-local context should live under `.praxis/local_context/`. Core always-on legal context should live under `.praxis/core_docs/`. Detailed/optional reference docs should live under `.praxis/docs/`.

Remove old legal install compatibility logic unless keeping a small helper is genuinely simpler than deleting it. In particular, do not build migrations from installed `.agent_core/` legal workspaces or old `agent_rules/` workspaces unless needed by a test that is intentionally retained. The project owner explicitly does not care about backwards compatibility for this harness yet.

### Setup And Runtime Updates

Update `legal/setup.py` so all install/update/docs commands use `.praxis/` display paths and real paths. Setup should still source files from `legal/.agent_core/` in this repository or from the downloaded legal template archive.

Update runtime path models and all call sites to use the renamed paths:

- `state_root`: `.praxis`
- `core_docs_root`: `.praxis/core_docs`
- `docs_root`: `.praxis/docs`
- `local_context_root`: `.praxis/local_context`
- `templates_root`: `.praxis/harness/templates`
- `typst_detailed_reference`: `.praxis/docs/typst_detailed_reference.typ`
- `legal_context`: `.praxis/core_docs/legal_context.typ`

Also update user-facing stdout/stderr, README text, docs command help, onboard required-doc handling, auto-update config lookup, `paths` command output, and tests so no installed legal command tells agents to run `.agent_core/harness/main.py`.

### Tests

Use `coding/tests/` as the organization reference: shared helpers plus focused behavior files. Avoid a single god file.

The existing `legal/tests/test_setup.py` behaviors should be split into files along these lines:

- `legal/tests/helpers.py`: shared command runners, setup helpers, TOML loading, ASCII assertion, fixture builders.
- `legal/tests/test_setup.py`: dependency guidance, fresh install shape, update behavior, managed block behavior, docs commands.
- `legal/tests/test_runtime_paths.py`: installed `.praxis/` path resolution, `paths`, `config show`, runtime dependency guidance.
- `legal/tests/test_onboard.py`: onboard runs, session log creation/cleanup, client matter index refresh, git checkpoint behavior.
- `legal/tests/test_clients_matters.py`: client creation, slug/suffix behavior, matter creation/list/find/focus/resolve, lookup metadata, ambiguity.
- `legal/tests/test_chronology_obligations_todos.py`: chronology entries, obligations, global and matter todos, todo claiming.
- `legal/tests/test_workflows.py`: workflow create/list/show/link and matter focus integration.
- `legal/tests/test_typst_compile.py`: harness compile command, `.p.pdf` output, focus classification of Typst sources/generated PDFs/other PDFs.
- `legal/tests/test_state_helpers.py`: frontmatter utilities, typed state helpers, lint where appropriate.

Keep tests behavior-focused. Do not add brittle exact prose assertions for large AGENTS sections. For AGENTS, assert stable contract markers such as `.praxis/harness/main.py onboard`, key command groups, the Typst compile rule, confidentiality rule, and absence of stale `.agent_core/docs/legal_harness_function.md` dependency language.

## Success Criteria

- `legal/AGENTS.md` contains the legal operating model and command guidance directly, and installed AGENTS guidance points to `.praxis/harness/main.py`.
- Fresh legal setup installs `.praxis/` rather than `.agent_core/`, with `src/`, `WIP/`, `ZZ_CLIENTS/`, `AGENTS.md`, `CLAUDE.md`, and `.gitignore` at the workspace root.
- The repository template layout matches the requested structure: `core_docs`, `local_context`, harness `templates`, and `.agent_core/docs` for detailed reference docs.
- Runtime commands work from an installed `.praxis/` workspace and report `.praxis/` paths where state paths are shown.
- Onboard no longer depends on `legal_harness_function.md` as a required installed doc for the core workflow contract.
- The legal test suite is split into focused modules with shared helpers and no single catch-all god file.
- Focused legal tests pass for the changed areas.
- Focused `ruff`, `ty`, and `git diff --check` verification passes for edited legal files.

## Notes

- The coding harness remains unchanged except as a reference for test organization.
- The containing repository should keep `legal/.agent_core/` as the legal template source root for consistency with `coding/`.
- Backwards compatibility is intentionally out of scope. Prefer deleting obsolete legal migration code and stale tests over preserving old installed layouts.
