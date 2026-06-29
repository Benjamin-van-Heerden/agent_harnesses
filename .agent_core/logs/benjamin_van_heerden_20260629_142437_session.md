---
created_at: '2026-06-29T14:24:37.971616'
username: benjamin_van_heerden
---
Work Log - Coding harness source-side patch runner

## Overarching Goals

Make coding harness update migrations easier to reason about by replacing scattered setup/update repair behavior with a first-class source-side patch system.

The desired model was:

- patch implementations live only in the harness source under `coding/patches/`;
- patch order and metadata are declared in a source manifest;
- installed projects track applied patch IDs in `.agent_core/patches.toml`;
- setup/update runs unapplied patches idempotently and records successful application.

## What Was Accomplished

### Added source-side patch manifest and patch files

Added `coding/patches/patches.toml` with ordered patch entries and four initial numbered patch files:

- `0001_agent_core_state_gitignore.py`: ensures durable `.agent_core/` state stays trackable while `.agent_core/tmp/` and `.cache/pycache/` are ignored.
- `0002_optional_onboard_config_scaffolds.py`: adds missing commented `[[files]]`, `[[tree_dirs]]`, and `[[runnables]]` onboarding scaffolds to existing configs, including the commented runnable `name` field.
- `0003_worktree_symlink_comment.py`: refreshes the worktree symlink config comment without changing configured values.
- `0004_remove_retired_default_docs.py`: removes retired default coding docs from installed `.agent_core/docs/`.

### Added installed patch tracking

Added setup-side patch record support at `.agent_core/patches.toml`. The record stores applied patch entries with:

```toml
[[applied]]
id = "0001_agent_core_state_gitignore"
applied_at = "..."
description = "..."
```

Setup writes this file when patches are first applied and skips any patch ID already recorded.

### Wired patches into setup/update

Updated `coding/setup.py` to:

- parse `coding/patches/patches.toml`;
- validate patch IDs, duplicate IDs, filenames, and referenced patch files;
- dynamically load source patch modules;
- require each patch to expose `run(project_root: Path) -> bool`;
- stop setup/update on invalid manifests, missing patch files, missing runners, or non-boolean return values;
- run source patches during setup/update after config/state creation and worktree symlink ignore handling;
- record successful patch IDs whether or not the patch made file changes.

Removed the old scattered direct migration calls from setup for the moved behaviors. Normal fresh defaults and required config/key creation remain in setup; existing-project migrations now live in source patches.

### Added regression coverage

Updated setup tests to verify:

- fresh installs create `.agent_core/patches.toml`;
- all initial patch IDs are recorded;
- the Agent Core `.gitignore` state patch is recorded;
- source patches update legacy worktree comments without resetting configured values;
- recorded patch IDs are skipped on later updates even if a user manually reverts the patch effects.

Verification completed:

```bash
uv run pytest coding/tests/test_setup.py
uv run pytest coding/tests/test_setup.py coding/tests/test_onboard.py::test_template_onboard_reads_docs_without_indexing coding/tests/test_onboard.py::test_template_onboard_reports_agent_core_tmp_mutations coding/tests/test_introspect.py
uvx ruff check coding/setup.py coding/patches coding/tests/test_setup.py coding/tests/test_onboard.py coding/tests/test_introspect.py
uv run ty check coding/setup.py coding/patches coding/tests/test_setup.py coding/tests/test_onboard.py coding/tests/test_introspect.py
git diff --check
```

## Key Files Affected

- `coding/setup.py`: added source patch models, manifest parsing, installed patch record rendering/loading/writing, patch module loading, patch execution, and patch recording; removed old direct migration helper calls for the moved behaviors.
- `coding/patches/patches.toml`: new source manifest listing ordered patches.
- `coding/patches/0001_agent_core_state_gitignore.py`: new `.gitignore` state/cache patch.
- `coding/patches/0002_optional_onboard_config_scaffolds.py`: new optional onboard config scaffold patch.
- `coding/patches/0003_worktree_symlink_comment.py`: new worktree symlink comment patch.
- `coding/patches/0004_remove_retired_default_docs.py`: new retired default docs cleanup patch.
- `coding/tests/test_setup.py`: updated and added focused coverage for source patch execution and installed patch records.

## What Comes Next

After this reaches `main`, running the installed harness update flow should create/update `.agent_core/patches.toml` locally and apply the `.gitignore` patch through the source patch runner rather than relying on scattered setup side effects.
