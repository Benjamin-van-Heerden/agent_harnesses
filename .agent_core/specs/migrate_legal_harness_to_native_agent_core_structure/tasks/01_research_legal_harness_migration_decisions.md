---
title: Research legal harness migration decisions
status: completed
created_at: '2026-05-21T09:44:37.917475'
updated_at: '2026-05-21T13:27:28.333914'
completed_at: '2026-05-21T13:27:28.333914'
---
Survey the current legal harness behavior and write a durable migration map before implementation. Capture the current legacy surfaces under legal/AGENTS.md, legal/bash_setup.sh, legal/agent_rules/commands, legal/agent_rules/scripts, legal/agent_rules/skeletons, legal/agent_rules/docs, legal/src, and the client/matter state tree. Decide which files are managed template/runtime files, which are lawyer-owned durable state, which legacy files need temporary compatibility, and which can be removed or deprecated by the final implementation. The output should be a concise markdown research/design note in the spec directory that future implementation tasks can follow without re-discovering the whole tree.

## Completion Notes

Researched the legacy legal harness surfaces and created .agent_core/specs/migrate_legal_harness_to_native_agent_core_structure/legal_migration_research.md as the detailed migration map. Captured decisions on native .agent_core/practice state, legacy agent_rules migration, obligations as the primary primitive, matter-local todos, typed chronology and obligation records, local-only git snapshots, managed-but-evolving Typst source, and deferring firm/global sync to a later rewrite.
