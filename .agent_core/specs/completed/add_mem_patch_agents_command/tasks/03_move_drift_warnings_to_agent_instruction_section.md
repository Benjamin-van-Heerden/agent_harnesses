---
title: Move drift warnings to AGENT INSTRUCTION section
status: completed
created_at: '2026-01-22T09:14:53.757034'
updated_at: '2026-01-22T09:22:24.320104'
completed_at: '2026-01-22T09:22:24.320097'
---
Refactor onboard.py to collect all drift warnings (config AND agents) into a list, then display them in the [AGENT INSTRUCTION] section at the end of the onboard file content. Remove the early stderr printing of config drift warning. The warnings should instruct the agent to notify the user to run the appropriate mem patch command.

## Completion Notes

Removed early stderr printing of config drift. Created drift_warnings list to collect both config and AGENTS.md drift warnings. Added drift warnings display in the AGENT INSTRUCTION section with clear formatting.