---
title: Add local harness setup and dependency preflight
status: completed
created_at: '2026-05-12T16:25:38.730117'
updated_at: '2026-05-13T09:25:27.152017'
completed_at: '2026-05-13T09:25:27.152012'
---
Create the local harness distribution shape and setup/update flow. setup.sh should install .agent_core/harness, create project-owned state directories, create AGENTS.md and CLAUDE.md using the Praxis managed-core-block pattern, and support --update by overwriting .agent_core/harness wholesale. config.toml update behavior must upsert defaults while preserving user values. user_mappings.toml must preserve existing mappings. Do not create .agent_core/tmp during setup. Add harness/deps.py and wire it before the Typer app so vanilla Python invocation reports missing dependencies with clear pip-based guidance.

## Completion Notes

Added project-local harness setup/update behavior under harnesses/mem/. setup.sh now installs from the template into a target project, overwrites .agent_core/harness/ wholesale on update, preserves project-owned state, preserves user mappings, creates or upserts .agent_core/config.toml defaults while preserving user values, refreshes only the managed AGENTS block while preserving user content, creates CLAUDE.md as a symlink where supported, and avoids creating .agent_core/tmp. Added dependency-free setup support for config upsert and verified setup can run before harness dependencies are installed. Added and verified deps.py preflight so direct vanilla Python invocation reports missing packages with python -m pip install guidance before Typer imports. Verified with focused Ruff, temp install/update smoke tests, stale harness overwrite checks, state/config/mapping preservation checks, no .agent_core/tmp creation, and no standalone product-word usage in harness setup or code.