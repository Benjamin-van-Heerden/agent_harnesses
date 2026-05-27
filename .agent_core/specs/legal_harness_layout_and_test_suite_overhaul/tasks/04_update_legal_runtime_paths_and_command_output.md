---
title: Update legal runtime paths and command output
status: completed
created_at: '2026-05-26T14:35:08.085848'
updated_at: '2026-05-27T09:25:22.919184'
completed_at: '2026-05-27T09:25:22.919184'
---
Update legal/.agent_core/harness runtime path resolution and all call sites for the new installed layout: state root .praxis, core docs .praxis/core_docs, detailed/optional docs .praxis/docs, local context .praxis/local_context, harness templates .praxis/harness/templates, legal context .praxis/core_docs/legal_context.typ, detailed Typst reference .praxis/docs/typst_detailed_reference.typ. Update onboard required-doc handling so it no longer depends on legal_harness_function.md for core workflow guidance. Update paths/config/onboard/auto-update/user-facing output to use .praxis terminology and paths.

## Completion Notes

Updated legal runtime path resolution to identify installed workspaces by .praxis and resolve state, harness, config, core docs, optional docs, local context, todos, logs, memories, workflows, and harness templates under the new installed namespace. Updated the paths command to show core docs and local context roots, removed onboard's dependency on legal_harness_function.md as a required doc, and refreshed the optional legal_harness_function reference doc so its command and state examples use .praxis. Smoke-installed the legal harness in /private/tmp and verified .praxis paths/config plus onboard required-doc output.
