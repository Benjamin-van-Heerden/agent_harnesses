---
created_at: '2026-05-21T16:21:04.078623'
username: benjamin_van_heerden
spec_slug: migrate_legal_harness_to_native_agent_core_structure
---
Work Log - Native legal setup, runtime foundation, state layer, and context commands

## Overarching Goals

This session continued the `migrate_legal_harness_to_native_agent_core_structure` spec by moving the legal harness from legacy Praxis installation and script/playbook surfaces toward the native Agent Core shape.

The practical goal was to get the legal harness installable through `legal/setup.py`, give that installer a real native `.agent_core/harness/` runtime to copy, port the reusable legacy helper behavior into typed state modules, and make the first native context commands usable enough for onboard/focus/list/lint workflows.

## What Was Accomplished

### Completed the setup installer task

Added `legal/setup.py`, a stdlib-only installer/updater for native legal Agent Core installs.

The installer now:
- resolves the legal template locally or from the `agent_harnesses` repository archive;
- creates the native `.agent_core/` practice/docs/harness directories;
- initializes local git when available;
- manages the legal `.gitignore` block;
- installs or refreshes `.agent_core/harness` and `.agent_core/README.md`;
- installs/updates `AGENTS.md` and `CLAUDE.md`;
- refreshes managed Typst reference docs and baseline `src/` files;
- preserves lawyer-owned profile, legal context, templates, clients, custom source files, and legacy `functions/`/`templates/`;
- migrates durable legacy `agent_rules` state into native `.agent_core` locations, including memories, logs, practice todos, and matter-scoped todos.

The task was marked complete after user approval.

### Completed the runtime foundation task

Added the native legal runtime under `legal/.agent_core/harness/`.

The runtime now includes:
- `main.py`, `deps.py`, and `requirements.txt`;
- Typer command registration for `onboard`, `client`, `matter`, `deadline`, `obligation`, `record`, `todo`, `memory`, `log`, and `lint`;
- typed config models and TOML loading;
- expanded path helpers for `.agent_core/practice`, `.agent_core/docs`, clients, matter info paths, chronology, obligations, todos, raw/reference files, Typst source roots, and legacy function/template roots;
- shared error handling;
- markdown/frontmatter utilities;
- local post-command git snapshot support without remote pull/rebase/push behavior.

The task was marked complete after user approval.

### Completed the state models and helpers task

Ported reusable legacy helper behavior from `legal/agent_rules/scripts/_lib.py` and related scripts into typed native state modules.

The state layer now includes:
- dataclass records for client profiles, matter statuses, matter refs, deadline entries, chronology entries, todos, memories, and work logs;
- validation helpers for slugs, dates, priorities, todo priorities, and communication direction;
- template rendering from `.agent_core/practice/templates`;
- client creation/listing/resolution helpers;
- matter creation/listing/resolution/closing helpers;
- deadline parsing/addition, `next_deadline` updates, and upcoming deadline listing;
- communication and note record append helpers;
- practice and matter todo creation/claiming/listing;
- memory and work log creation/listing;
- initial obligation record helpers.

The task was marked complete after user approval.

### Completed the legal context commands task

Implemented native context commands over the typed state layer.

The command surface now includes:
- `onboard` with profile/setup warnings, client/open-matter counts, upcoming deadline count, high-priority matter summary, practice todo count, memory/log counts, Typst building block count, and direct agent guidance;
- `client list`;
- `matter list`;
- `matter find`;
- `matter focus`;
- `matter list-unparsed`;
- `deadline upcoming [days]`;
- `todo list [matter_ref]`;
- `lint`.

`matter focus` now reports status/record/deadline presence, open todos, draft/PDF counts, raw/reference counts, unparsed raw files, deadlines, and direct guidance to read relevant matter files before advising or drafting.

The task was marked complete after user approval.

### Verification

Focused verification passed:
- `uv run pytest legal/tests/test_setup.py`
- `uvx ruff check legal/setup.py legal/.agent_core/harness legal/tests/test_setup.py`
- `uv run ty check legal/setup.py legal/.agent_core/harness legal/tests/test_setup.py`

## Key Files Affected

### `legal/setup.py`

Added the native legal setup/update installer, including managed runtime installation, durable state creation, legacy `agent_rules` migration, managed docs/source refresh, `AGENTS.md` block installation, `CLAUDE.md` compatibility, and `.gitignore` management.

### `legal/.agent_core/`

Added the native legal runtime template:
- `harness/main.py`
- `harness/deps.py`
- `harness/requirements.txt`
- command groups under `harness/src/commands/`
- config modules under `harness/src/config/`
- state modules under `harness/src/state/`
- utilities under `harness/src/utils/`
- `.agent_core/README.md`

### `legal/tests/test_setup.py`

Added focused tests covering:
- fresh native legal install;
- update preservation and managed refresh behavior;
- legacy `agent_rules` migration;
- installed onboard execution;
- runtime command registration and config/path commands;
- markdown/frontmatter utility behavior;
- state helper behavior end to end;
- installed context command behavior.

### `.agent_core/specs/migrate_legal_harness_to_native_agent_core_structure/tasks/*.md`

Updated harness task state for completed tasks:
- `build_native_legal_setup_installer`
- `scaffold_legal_harness_runtime_foundation`
- `port_legal_state_models_and_helpers`
- `implement_legal_context_commands`

## What Comes Next

Four spec tasks remain:
- implement client and matter lifecycle commands;
- implement legal record and bookkeeping commands;
- update legal agent instructions and documentation;
- retire the legacy legal command surface.

The next logical implementation step is to expose the already-ported lifecycle helpers through native commands such as `client new`, `matter new`, and `matter resolve`, then add focused tests around command success paths and validation failures.
