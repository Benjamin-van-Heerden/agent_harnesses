---
title: Add TOML workflow commands and focus integration
status: completed
created_at: '2026-05-25T15:16:07.212513'
updated_at: '2026-05-25T16:07:34.445315'
completed_at: '2026-05-25T16:07:34.445315'
---
Add a workflow command group for the legal harness. At minimum implement workflow new <name>, workflow list, and workflow show <workflow>. Workflows live as plain TOML files under .agent_core/practice/workflows/<slug>.toml. workflow new should create a useful template with example step structure and print guidance for the agent. Design typed validation for workflow steps supporting sequence/graph concepts such as id, title, kind, requires, blocks, and per-kind todo/obligation data. Matter frontmatter links to a workflow by slug; matter-local progress should be machine-readable, likely info/workflow.toml. matter focus must load linked workflow state and surface workflow name, completed/current/blocked steps, missing prerequisites, workflow-generated open todos/obligations where applicable, and next recommended action. Do not build a custom DSL or .pworkflow extension in this spec.

## Completion Notes

Added plain TOML workflow state under .agent_core/practice/workflows with typed parsing and validation for [[steps]] entries containing id, title, kind, requires, blocks, and optional todo/obligation guidance. Added workflow command group with new, list, show, and link commands. workflow new writes a useful editable template; workflow show validates and summarizes steps; workflow link records the matter workflow slug and creates matter-local info/workflow.toml progress state. Integrated matter focus with linked workflow state so it surfaces workflow name, completed/current/blocked steps, missing prerequisites, workflow todo/obligation guidance, and next recommended action. Missing or invalid linked workflows are reported in focus output instead of causing tracebacks. Setup now creates .agent_core/practice/workflows. Updated docs and focused tests. Verified with uv run pytest legal/tests/test_setup.py -q, uv run ty check on edited workflow files and tests, and uvx ruff check on edited files.
