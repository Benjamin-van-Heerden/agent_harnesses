---
title: Build native legal setup installer
status: todo
created_at: '2026-05-21T09:48:52.424308'
updated_at: '2026-05-21T09:48:52.424308'
completed_at: null
---
Replace the legacy Bash installer path with a stdlib-only legal/setup.py modeled on coding/setup.py. It must install from the legal/ template in this repository, create the legal project directory structure, install or refresh .agent_core/harness, manage the AGENTS.md managed core block, create or refresh CLAUDE.md compatibility, manage the legal .gitignore block, copy managed Typst support files, and preserve lawyer-owned state on update. It must remove the old mem-lite fetch dependency from the supported setup/update path and include focused setup tests for fresh install, update preservation, managed file refresh, and lawyer-owned state preservation.