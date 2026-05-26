---
title: Update legal runtime paths and command output
status: todo
created_at: '2026-05-26T14:35:08.085848'
updated_at: '2026-05-26T14:35:08.085848'
completed_at: null
---
Update legal/.agent_core/harness runtime path resolution and all call sites for the new installed layout: state root .praxis, core docs .praxis/core_docs, detailed/optional docs .praxis/docs, local context .praxis/local_context, harness templates .praxis/harness/templates, legal context .praxis/core_docs/legal_context.typ, detailed Typst reference .praxis/docs/typst_detailed_reference.typ. Update onboard required-doc handling so it no longer depends on legal_harness_function.md for core workflow guidance. Update paths/config/onboard/auto-update/user-facing output to use .praxis terminology and paths.