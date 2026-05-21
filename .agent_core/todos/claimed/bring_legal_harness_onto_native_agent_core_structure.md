---
title: Bring legal harness onto native Agent Core structure
status: claimed
issue_id: 9
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/9
created_at: '2026-05-20T17:06:19.277828'
claimed_by: benjamin_van_heerden
claimed_at: '2026-05-21T09:24:28.467175'
---
Research and plan the migration of the legal/ harness from the legacy agent_rules shape to the native Agent Core harness structure. Current observed problems: no template-level setup.py, no .agent_core/harness/main.py runtime, no src/commands command tree, command behavior is still defined by markdown playbooks under agent_rules/commands, and scripts live outside the standard command/state/utils composition model. Plan should map existing legal concepts and scripts into the expected template shape: legal/AGENTS.md for agent workflow, legal/setup.py for install/update, legal/.agent_core/harness/main.py as the CLI composition root, legal/.agent_core/harness/src/commands/<area>/main.py for command groups, and one Python file per command verb. Preserve the core legal workflow and lawyer-facing behavior, but replace markdown-command dispatch with typed, testable Python command modules whose stdout tells the agent exactly how to proceed.