---
title: Restructure legal template layout
status: completed
created_at: '2026-05-26T14:34:54.461302'
updated_at: '2026-05-26T15:12:10.766485'
completed_at: '2026-05-26T15:12:10.766485'
---
Restructure the legal/ template source tree: delete legal/.DS_Store if still present; rename legal/.agent_core/docs to legal/.agent_core/core_docs; rename legal/.agent_core/practice to legal/.agent_core/local_context; move legal/.agent_core/local_context/templates into legal/.agent_core/harness/templates; move legal/.agent_docs/typst_detailed_reference.typ into legal/.agent_core/docs/typst_detailed_reference.typ. Keep legal/.agent_core as the template source root inside this repository.

## Completion Notes

Restructured the legal template source tree to match the requested layout. Renamed legal/.agent_core/docs to legal/.agent_core/core_docs for legal_context.typ, renamed legal/.agent_core/practice to legal/.agent_core/local_context for lawyer_profile.md, moved harness scaffolding templates into legal/.agent_core/harness/templates, moved typst_detailed_reference.typ from legal/.agent_docs into legal/.agent_core/docs, removed the now-empty legal/.agent_docs directory, and confirmed legal/.DS_Store was not present.
