---
title: Simplify onboard and documentation handling
status: completed
created_at: '2026-05-12T16:25:46.495875'
updated_at: '2026-05-13T09:31:39.140218'
completed_at: '2026-05-13T09:31:39.140212'
---
Migrate onboard to the .agent_core state layout and local harness invocation style. Remove generic template loading from ~/.config/mem. Remove the docs/core distinction. On onboard, read every file under .agent_core/docs/ in full, with deterministic ordering and clear headings. Remove indexed documentation, summaries, vector search, and related warnings from onboard. Ensure generated onboard output and hints use local vanilla Python command examples such as python .agent_core/harness/main.py ... instead of relying on a global CLI.

## Completion Notes

Added a harness-local onboard command that uses .agent_core/config.toml, reads configured important files, reads every file under .agent_core/docs recursively in deterministic order, removes docs/core special handling, avoids indexed docs summaries vector search AI docs tooling and generic templates, includes .agent_core state summaries for specs tasks open todos memories and recent logs, prints small output to stdout, and lazily creates .agent_core/tmp/onboard_*.md only for large output. Verified with focused Ruff, no standalone product-word usage in harness code/setup/support scripts, temp project full nested docs reads, state summary output, no .agent_core/tmp creation for stdout mode, lazy temp creation for large output, and no .mem directory creation.