---
title: Streamline task completion feedback loop
status: completed
created_at: '2026-02-11T17:19:43.115317'
updated_at: '2026-02-11T17:54:06.035928'
completed_at: '2026-02-11T17:54:06.035922'
---
Remove the laborious two-step task completion flow. Currently: agent completes -> mem mark complete -> forced summary + ask acceptable -> mem mark complete again -> forced summary again. Instead: remove the pre-completion summary/confirmation block. Keep the --user-gave-explicit-permission flag (it's strong enough to stop agents). After the successful completion message, just add: 'Remember: you must ALWAYS get explicit user permission before passing --user-gave-explicit-permission for ANY task. Never assume permission carries over. Before marking the next task as complete, give a summary of what you have done and ask the user if the task is complete and acceptable.' Also clean up mem.md template and onboard command to make sure instructions are coherent and don't expose things they shouldn't.

## Completion Notes

Removed the two-step pre-completion flow (no-notes block). Made notes required arg. No-flag message now teaches the workflow as a discovery moment on first task, says 'from the next task onward' to avoid stop-start. Post-completion says 'you may continue with the next task'. Updated all hints (mem.md, onboard.py, task.py new/list/show/amend) to use 'detailed notes about what was done'. All consistent.