---
created_at: '2026-06-29T13:33:40.692492'
username: benjamin_van_heerden
---
Work Log - Coding harness introspection and gitignore state tracking

## Overarching Goals

Add two coding harness improvements:

- make installed projects reliably track durable `.agent_core/` state even when broad `.gitignore` rules would otherwise hide nested files such as `.agent_core/config.toml`;
- add an `introspect` command that scaffolds durable project reference documents for agents to complete.

During verification, the user's intentional `PYTHONPYCACHEPREFIX=.cache/pycache` setup surfaced as a setup preflight issue, so the `.gitignore` patch was expanded to also ignore `.cache/pycache/`.

## What Was Accomplished

### Added managed Agent Core `.gitignore` state rules

Updated the coding harness setup and runtime `.gitignore` helpers to maintain a named managed block:

```gitignore
# Agent Core state
!.agent_core/
!.agent_core/**
.agent_core/tmp/
.agent_core/tmp/**
.cache/pycache/
.cache/pycache/**
```

This keeps durable `.agent_core/` state trackable even when a project has broad ignore patterns such as `.agent_core/`, `config/`, or `*.toml`, while continuing to ignore generated onboard/report temp files under `.agent_core/tmp/`.

The setup output now reports the change as an applied `.gitignore` patch, and onboard reports the same patch when it has to repair `.gitignore` during a session.

Setup was also adjusted so the managed state block is kept after configured worktree symlink ignore entries. That makes the `.agent_core/` negation rules effective against earlier broad ignore rules.

### Handled `.cache/pycache/` as an environment artifact

The user's environment intentionally sets `PYTHONPYCACHEPREFIX=.cache/pycache`, which can create an untracked `.cache/` tree before setup has written `.gitignore`.

Setup now treats an untracked `.cache/pycache/` tree as an allowed Python cache-prefix artifact during initial dirty-tree checks, without allowing arbitrary `.cache/` content. Setup/uninstall staging was tightened to stage only harness-managed paths so cache-prefix artifacts do not get committed or block uninstall commits after the managed `.gitignore` block is removed.

### Added `introspect` command group

Added `python -B .agent_core/harness/main.py introspect` with:

- `introspect structure`: scaffolds `.agent_core/docs/core/codebase_and_structure.md`;
- `introspect what`: scaffolds `.agent_core/docs/core/what.md`;
- `--force` overwrite support;
- filtered file tree output capped at 300 lines;
- agent-facing instructions for completing the generated documents.

The structure document was refined to be a factual repository map: what exists, where things live, how modules connect, entry points, commands/workflows, external interfaces, tests, and conventions confirmed from code. It explicitly avoids goals, motivation, target users, and future direction.

The what document keeps the goals/purpose/user-interview framing and instructs the agent to interview the user before completing it.

### Added focused regression coverage

Added and updated tests for:

- setup writing the Agent Core state `.gitignore` block after broad ignore rules;
- `.agent_core/config.toml` remaining unignored while `.agent_core/tmp/*` and `.cache/pycache/*` are ignored;
- setup tolerating an existing `.cache/pycache/` artifact before `.gitignore` is patched;
- uninstall removing managed `.gitignore` entries cleanly;
- onboard applying the runtime `.gitignore` patch;
- introspect structure and what scaffolding;
- introspect refusing to overwrite existing docs without `--force`.

Verification completed:

```bash
uv run pytest coding/tests/test_setup.py coding/tests/test_onboard.py::test_template_onboard_reads_docs_without_indexing coding/tests/test_onboard.py::test_template_onboard_reports_agent_core_tmp_mutations coding/tests/test_introspect.py
uv run pytest coding/tests/test_introspect.py
uvx ruff check coding/.agent_core/harness/main.py coding/.agent_core/harness/src/commands/introspect/main.py coding/.agent_core/harness/src/commands/onboard/main.py coding/.agent_core/harness/src/commands/report/main.py coding/.agent_core/harness/src/utils/gitignore.py coding/setup.py coding/tests/test_setup.py coding/tests/test_onboard.py coding/tests/test_introspect.py
uv run ty check coding/.agent_core/harness/main.py coding/.agent_core/harness/src/commands/introspect/main.py coding/.agent_core/harness/src/commands/onboard/main.py coding/.agent_core/harness/src/commands/report/main.py coding/.agent_core/harness/src/utils/gitignore.py coding/setup.py coding/tests/test_setup.py coding/tests/test_onboard.py coding/tests/test_introspect.py
git diff --check
```

## Key Files Affected

- `coding/setup.py`: added the managed Agent Core state `.gitignore` block, `.cache/pycache/` ignore entries, cache-prefix dirty-tree allowance, scoped setup staging, uninstall cleanup for managed ignore entries, and updated setup/onboard-facing patch messages.
- `coding/.agent_core/harness/src/utils/gitignore.py`: updated runtime `.gitignore` repair logic to maintain the full Agent Core state/cache block.
- `coding/.agent_core/harness/src/commands/onboard/main.py`: updated onboard mutation output to describe the broader `.gitignore` patch.
- `coding/.agent_core/harness/src/commands/report/main.py`: updated report warning text for the broader `.gitignore` state rules.
- `coding/.agent_core/harness/main.py`: registered the new `introspect` command group.
- `coding/.agent_core/harness/src/commands/introspect/main.py`: added the new introspection command implementation, templates, filtered tree rendering, and instructions.
- `coding/tests/test_setup.py`: added `.gitignore` patch and `.cache/pycache/` regression coverage.
- `coding/tests/test_onboard.py`: added runtime `.gitignore` patch assertions.
- `coding/tests/test_introspect.py`: added focused coverage for `introspect structure`, `introspect what`, and overwrite behavior.

## Errors and Barriers

The first broad focused test run failed because `PYTHONPYCACHEPREFIX=.cache/pycache` caused plain Python subprocesses in setup tests to create `.cache/` in fresh git repositories before setup ran. Initially the tests were rerun with `PYTHONDONTWRITEBYTECODE=1`, but the user clarified that the cache prefix is intentional. The implementation was then updated so `.cache/pycache/` is part of the managed ignore patch and setup tolerates that exact cache-prefix tree during preflight.

After adding `.cache/pycache/`, uninstall initially failed because removing the managed `.gitignore` block caused the existing cache-prefix tree to reappear in status before the uninstall commit. Setup staging was corrected to stage only harness-managed paths, while still allowing `.cache/pycache/` in the status audit.

A broad `coding/tests/test_onboard.py` run also exposed an unrelated existing expectation around recent work-log selection on a non-dev branch. That behavior was not changed for this session; verification was kept focused on the onboarding paths affected by the `.gitignore` patch.

## What Comes Next

If the user wants the installed local harness in this repository to pick up these uncommitted coding template changes before they are merged/pushed through the normal remote update loop, run the local template update path after commit: `python -B coding/setup.py --update`. Otherwise, the normal propagation model remains: source changes under `coding/`, push, then installed projects update from the coding setup flow.
