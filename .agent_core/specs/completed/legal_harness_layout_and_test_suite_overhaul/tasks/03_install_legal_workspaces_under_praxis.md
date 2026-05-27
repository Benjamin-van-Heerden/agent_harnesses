---
title: Install legal workspaces under .praxis
status: completed
created_at: '2026-05-26T14:35:01.258758'
updated_at: '2026-05-26T16:56:35.281037'
completed_at: '2026-05-26T16:56:35.281037'
---
Update legal/setup.py so fresh install, update, docs list/add/update, stdout/stderr, config creation, managed README copy, AGENTS/CLAUDE installation, gitignore, Typst src installation, WIP, ZZ_CLIENTS, and optional docs all target .praxis as the installed state root. Source files still come from the legal/.agent_core template. Remove obsolete legal compatibility/migration code for old installed .agent_core or agent_rules layouts unless a tiny helper is clearly simpler than deletion; backwards compatibility is intentionally out of scope.

## Completion Notes

Updated legal/setup.py so fresh installs, updates, docs commands, managed runtime copy, config creation, AGENTS/CLAUDE installation, gitignore handling, Typst source installation, WIP, ZZ_CLIENTS, and optional/default docs target the installed .praxis namespace. Kept template sources under legal/.agent_core, installed legal_context.typ from core_docs, installed typst_detailed_reference.typ under .praxis/docs, moved default docs away from legal_harness_function.md, removed obsolete agent_rules migration and .agent_docs installation, updated README text to describe .praxis, and smoke-tested a fresh install plus docs add in /private/tmp.
