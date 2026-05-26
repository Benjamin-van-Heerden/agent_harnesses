---
title: Verify legal layout overhaul
status: todo
created_at: '2026-05-26T14:35:22.613100'
updated_at: '2026-05-26T14:35:22.613100'
completed_at: null
---
Run focused verification for the changed legal harness files. At minimum run the reorganized legal tests relevant to setup/runtime/onboard/commands, focused ruff on edited Python files, focused ty on edited Python files, and git diff --check. Do not run unrelated full suites unless the implementation blast radius makes that necessary and the user approves.