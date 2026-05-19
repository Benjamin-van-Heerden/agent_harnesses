---
title: Research agent_rules to mem migration path
status: todo
created_at: '2026-05-19T14:17:44.112182'
updated_at: '2026-05-19T14:17:44.112182'
completed_at: null
---
Research the existing mem migrate --lite-to-mem path in /Users/benjamin/utils/mem/src/utils/migrate.py, with special attention to how agent_rules specs are parsed back into .mem specs and tasks. Document the current parser behavior, where AI-assisted interpretation may still be needed for ambiguous spec content, what generated .mem state should be reviewed before running the later mem migrate --to-harness step, and what the final research markdown should recommend for the agent_rules to mem to harness route.