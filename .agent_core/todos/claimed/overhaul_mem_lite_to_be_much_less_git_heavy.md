---
title: Overhaul mem lite to be much less git heavy
status: claimed
issue_id: 95
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/95
created_at: '2026-03-10T10:32:49.801206'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-03-10T10:42:35.693553'
---
At the moment pretty much all of the onboarding is git commands which are not necessary - the current onboard command is assuming 'too large of a team' - practically, so long as it checks we are in dev/development branch and warns if not it's fine. On spec creation we also need to look at the flow, most of the time it is really fine if we just create the spec in the development branch itself - the agent should ask the user if they want to do the whole 'separate branch + pr' approach or 'just work in dev' - same thing with the merge commands. Just critically evaluate and think 'is this really necessary for a small team?' and 'what would work best for a small team?' or even a single developer that works on a repo. The assumption should be that it is a small team and that git will be handled manually. Mem lite is just that - *lite*, it shouldn't strive to do everything that actual 'mem' does. Structural review of src/templates/mem_lite - which commands are necessary, which can be dropped, how should the mem lite AGENTS.md be modified, how should the command itself be modified (src/commands/lite.py)?