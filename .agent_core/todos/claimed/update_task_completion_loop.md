---
title: Update task completion loop
status: claimed
issue_id: 69
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/69
created_at: '2026-01-28T12:46:09.107886'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-01-28T12:49:26.470348'
---
currently we have mem task complete 'task_name' 'description' - but this will never actually complete the task, this is by design so that there is a clear feedback loop between what agents are doing and what I want/decide. Agents quickly realize that the command will 'never succeed' and go off on their own passing --accept without my consent I just want a clear stopping point before we mark tasks as complete. My thinking is that we split the command into two steps: mem task complete 'task_name' (this is the 'precompletion' step and works basically identically to the current mem task complete 'task_name' 'description' command) then I think we should remove the --accept flag and replace it with a --user-gave-explicit-permission flag i.e. mem task complete 'task_name' 'description' should give the same effectively as just mem task complete 'task_name' (this will make it *very* clear that the agent needs to ask for permission and solidify the feedback loop. Then very important we need to methodically go through the codebase and obscure the functionality for mem task complete 'title' 'description' so that e.g. in onboard command and when working with tasks the agent only sees mem task complete 'task_name' as an available command - only when they call this command is the whole --user-gave-explicit-permission option revealed