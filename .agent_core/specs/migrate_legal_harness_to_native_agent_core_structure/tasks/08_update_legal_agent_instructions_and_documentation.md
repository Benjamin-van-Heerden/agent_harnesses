---
title: Update legal agent instructions and documentation
status: completed
created_at: '2026-05-21T09:49:42.806625'
updated_at: '2026-05-22T11:25:45.567509'
completed_at: '2026-05-22T11:25:45.567509'
---
Rewrite legal/AGENTS.md around the native Agent Core command path while preserving the lawyer-facing UX contract: the lawyer speaks naturally, the agent runs harness commands invisibly, confirms in plain language, and never exposes slugs or filesystem detail unless asked. Add a human-facing legal/README.md if useful. Remove references that make markdown playbooks or agent_rules/scripts the command source of truth. Document managed vs lawyer-owned files, setup/update usage, first-run setup, daily onboard, matter focus, drafting conventions, Typst source conventions, and confidentiality boundaries.

## Completion Notes

Rewrote legal/AGENTS.md around the native Agent Core command path and the lawyer-facing UX contract. Documented the legal primitives now exposed by the native runtime: onboard, clients, matters, matter focus, deadlines, records, todos, memories, work logs, and Typst source. Removed legacy command playbook/script guidance as the command source of truth. Added legal/README.md with install/update and managed-vs-lawyer-owned state guidance. Implemented onboard-created session work logs with cleanup for untouched empty log skeletons, and added focused tests covering installed AGENTS content plus onboard work-log creation and cleanup. Verified focused pytest selection plus Ruff and ty checks on touched files.
