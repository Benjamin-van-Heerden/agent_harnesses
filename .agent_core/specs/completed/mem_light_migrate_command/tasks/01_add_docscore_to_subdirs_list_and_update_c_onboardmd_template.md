---
title: Add docs/core to subdirs list and update c_onboard.md template
status: completed
created_at: '2026-02-11T14:59:07.196889'
updated_at: '2026-02-11T16:58:17.889043'
completed_at: '2026-02-11T16:58:17.889036'
---
Two small changes that benefit init/update/migrate: (1) Add 'docs/core' to the subdirs list in _copy_agent_rules() in src/commands/light.py so the directory is created automatically. (2) Add a 'Read Core Docs' section to src/templates/mem_light/agent_rules/commands/c_onboard.md between 'Read Memories' and 'Read Work Logs' that lists and reads all files in agent_rules/docs/core/.

## Completion Notes

Added docs/core to subdirs list in _copy_agent_rules() and added Read Core Docs section to c_onboard.md template between Read Memories and Read Work Logs