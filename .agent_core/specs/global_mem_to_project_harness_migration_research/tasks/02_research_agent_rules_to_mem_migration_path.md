---
title: Research agent_rules to mem migration path
status: completed
created_at: '2026-05-19T14:17:44.112182'
updated_at: '2026-05-20T10:11:57.355486'
completed_at: '2026-05-20T10:11:57.355486'
---
Research the existing mem migrate --lite-to-mem path in /Users/benjamin/utils/mem/src/utils/migrate.py, with special attention to how agent_rules specs are parsed back into .mem specs and tasks. Document the current parser behavior, where AI-assisted interpretation may still be needed for ambiguous spec content, what generated .mem state should be reviewed before running the later mem migrate --to-harness step, and what the final research markdown should recommend for the agent_rules to mem to harness route.

## Completion Notes

Documented the agent_rules to .mem to .agent_core migration route, including deterministic parser behavior, review risks, branch detection and source-branch requirements, required mem-side quick fixes, command sequence, and verification checklist.
