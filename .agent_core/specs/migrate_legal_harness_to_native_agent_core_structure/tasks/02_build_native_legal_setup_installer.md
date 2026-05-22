---
title: Build native legal setup installer
status: completed
created_at: '2026-05-21T09:48:52.424308'
updated_at: '2026-05-21T14:40:22.438238'
completed_at: '2026-05-21T14:40:22.438238'
---
Replace the legacy Bash installer path with a stdlib-only legal/setup.py modeled on coding/setup.py. It must install from the legal/ template in this repository, create the legal project directory structure, install or refresh .agent_core/harness, manage the AGENTS.md managed core block, create or refresh CLAUDE.md compatibility, manage the legal .gitignore block, copy managed Typst support files, and preserve lawyer-owned state on update. It must remove the old mem-lite fetch dependency from the supported setup/update path and include focused setup tests for fresh install, update preservation, managed file refresh, and lawyer-owned state preservation.

## Completion Notes

Added a stdlib-only legal/setup.py installer/updater for native Agent Core legal installs. The installer resolves the legal template locally or from the agent_harnesses archive, creates native .agent_core practice/docs/harness directories, initializes local git when available, manages the legal .gitignore block, installs or refreshes .agent_core/harness and .agent_core/README.md, preserves lawyer-owned profile/legal context/templates/clients/custom source, refreshes managed Typst reference docs and baseline src files, installs AGENTS.md and CLAUDE.md compatibility, and migrates durable legacy agent_rules state into native .agent_core locations including practice memories/logs/todos and matter-scoped todos. Added a minimal native legal runtime foundation needed by setup, including main.py, dependency checks, path helpers, local post-command git snapshot support, and a placeholder onboard command. Added focused legal setup tests covering fresh install, managed refresh with preservation, legacy migration, and installed onboard execution. Verified with uv run pytest legal/tests/test_setup.py, uvx ruff check legal/setup.py legal/.agent_core/harness legal/tests/test_setup.py, and uv run ty check legal/setup.py legal/.agent_core/harness legal/tests/test_setup.py.
