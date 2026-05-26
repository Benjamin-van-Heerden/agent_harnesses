---
created_at: '2026-05-26T16:56:41.978673'
username: benjamin_van_heerden
spec_slug: legal_harness_layout_and_test_suite_overhaul
---
Work Log - Legal Harness AGENTS, Layout, And .praxis Setup

## Overarching Goals

Continue the `legal_harness_layout_and_test_suite_overhaul` spec by making the legal harness more self-contained and moving installed legal workspaces toward the new `.praxis/` namespace. The session focused on the first three spec tasks: agent-facing guidance, template directory layout, and installer behavior.

## What Was Accomplished

### Legal AGENTS Guidance

Expanded `legal/AGENTS.md` from a short pointer into a self-contained managed block. It now tells agents to run:

```bash
python -B .praxis/harness/main.py onboard
```

and to compile legal Typst documents through:

```bash
python -B .praxis/harness/main.py compile <source.typ>
```

The guidance now includes the legal operating model, command descriptions, the state model, client and matter rules, chronology/obligation/todo/memory distinctions, WIP rules, drafting rules, Typst compile behavior, confidentiality guidance, and stop/ambiguity rules. The direct dependency on `.agent_core/docs/legal_harness_function.md` was removed. The command section was expanded after review to explain when each command group is relevant and roughly what it does.

### Template Layout

Restructured the legal template source tree:

- moved `legal/.agent_core/docs/legal_context.typ` to `legal/.agent_core/core_docs/legal_context.typ`;
- moved `legal/.agent_core/practice/lawyer_profile.md` to `legal/.agent_core/local_context/lawyer_profile.md`;
- moved `legal/.agent_core/practice/templates/*` to `legal/.agent_core/harness/templates/*`;
- moved `legal/.agent_docs/typst_detailed_reference.typ` to `legal/.agent_core/docs/typst_detailed_reference.typ`;
- removed the now-empty `legal/.agent_docs/` directory;
- confirmed `legal/.DS_Store` was not present.

### .praxis Installer Setup

Updated `legal/setup.py` so fresh installs and docs commands target `.praxis/` instead of installed `.agent_core/`. The installer now creates and manages `.praxis/config.toml`, `.praxis/harness/`, `.praxis/README.md`, `.praxis/core_docs/legal_context.typ`, `.praxis/docs/typst_detailed_reference.typ`, `.praxis/local_context/lawyer_profile.md`, `.praxis/todos/open`, and `.praxis/todos/claimed`.

Removed obsolete `agent_rules` migration code and stopped installing `.agent_docs/`. The default installed optional docs no longer include `legal_harness_function.md`; it remains available through `setup.py docs add legal_harness_function`.

Updated `legal/README.md` and `legal/.agent_core/README.md` to describe the new `.praxis/` installed namespace.

### Verification During Session

Smoke-tested a fresh legal install in `/private/tmp`. The installer created `.praxis/`, `src/`, `WIP/`, `ZZ_CLIENTS/`, `AGENTS.md`, `CLAUDE.md`, and `.gitignore`, and printed `python -B .praxis/harness/main.py onboard`. Also verified `docs add legal_harness_function` installs the optional function doc into `.praxis/docs/`.

## Key Files Affected

- `legal/AGENTS.md`: expanded from a short pointer to full self-contained legal harness instructions using `.praxis/harness/main.py`.
- `legal/setup.py`: changed installed state root from `.agent_core` to `.praxis`, updated managed/default copied paths, removed legacy migration helpers, removed `.agent_docs` installation, and updated setup/docs output.
- `legal/README.md`: updated installed runtime and onboard examples from `.agent_core` to `.praxis`; updated Typst reference doc location.
- `legal/.agent_core/README.md`: updated installed runtime/state descriptions from `.agent_core/practice` and `.agent_core/docs` to `.praxis/local_context`, `.praxis/core_docs`, and `.praxis/docs`.
- `legal/.agent_core/core_docs/legal_context.typ`: new template location for core legal context.
- `legal/.agent_core/local_context/lawyer_profile.md`: new template location for local lawyer profile defaults.
- `legal/.agent_core/harness/templates/{log.md,memory.md,profile.md,status.md,todo.md}`: new template location for harness-owned scaffolding templates.
- `legal/.agent_core/docs/typst_detailed_reference.typ`: new template location for the detailed Typst reference.
- `.agent_core/specs/legal_harness_layout_and_test_suite_overhaul/tasks/01_fold_legal_operating_model_into_agentsmd.md`: marked complete.
- `.agent_core/specs/legal_harness_layout_and_test_suite_overhaul/tasks/02_restructure_legal_template_layout.md`: marked complete.
- `.agent_core/specs/legal_harness_layout_and_test_suite_overhaul/tasks/03_install_legal_workspaces_under_praxis.md`: marked complete.

## Errors and Barriers

The first installer smoke test in `/private/tmp` failed during `git init` with `Operation not permitted` under the default sandbox. Rerunning the same installer command with elevated filesystem permissions succeeded. A temporary `legal/__pycache__` directory was created by an initial `python -m py_compile legal/setup.py` check and was removed.

## What Comes Next

Completed spec tasks:

- `fold_legal_operating_model_into_agentsmd`
- `restructure_legal_template_layout`
- `install_legal_workspaces_under_praxis`

Remaining spec work should continue with runtime path resolution and command output updates. The installed runtime code under `legal/.agent_core/harness/` still needs to be brought into alignment with `.praxis`, `core_docs`, `local_context`, harness templates, and the new detailed docs location. Tests also still need to be split and expanded, then focused verification run for the changed legal harness areas.
