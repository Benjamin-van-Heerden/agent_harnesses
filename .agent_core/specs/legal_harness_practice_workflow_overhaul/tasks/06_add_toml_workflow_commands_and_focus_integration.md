---
title: Add TOML workflow commands and focus integration
status: todo
created_at: '2026-05-25T15:16:07.212513'
updated_at: '2026-05-25T15:16:07.212513'
completed_at: null
---
Add a workflow command group for the legal harness. At minimum implement workflow new <name>, workflow list, and workflow show <workflow>. Workflows live as plain TOML files under .agent_core/practice/workflows/<slug>.toml. workflow new should create a useful template with example step structure and print guidance for the agent. Design typed validation for workflow steps supporting sequence/graph concepts such as id, title, kind, requires, blocks, and per-kind todo/obligation data. Matter frontmatter links to a workflow by slug; matter-local progress should be machine-readable, likely info/workflow.toml. matter focus must load linked workflow state and surface workflow name, completed/current/blocked steps, missing prerequisites, workflow-generated open todos/obligations where applicable, and next recommended action. Do not build a custom DSL or .pworkflow extension in this spec.