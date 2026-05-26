---
title: Restructure legal template layout
status: todo
created_at: '2026-05-26T14:34:54.461302'
updated_at: '2026-05-26T14:34:54.461302'
completed_at: null
---
Restructure the legal/ template source tree: delete legal/.DS_Store if still present; rename legal/.agent_core/docs to legal/.agent_core/core_docs; rename legal/.agent_core/practice to legal/.agent_core/local_context; move legal/.agent_core/local_context/templates into legal/.agent_core/harness/templates; move legal/.agent_docs/typst_detailed_reference.typ into legal/.agent_core/docs/typst_detailed_reference.typ. Keep legal/.agent_core as the template source root inside this repository.