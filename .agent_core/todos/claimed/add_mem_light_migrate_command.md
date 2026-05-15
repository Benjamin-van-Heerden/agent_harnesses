---
title: Add mem light migrate command
status: claimed
issue_id: 81
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/81
created_at: '2026-02-11T12:12:49.366199'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-02-11T13:55:22.718767'
---
This command transitions from the .mem based workflow to the mem light based workflow, this is useful in cases where e.g. we want to do handoff of a project where the project owners don't have mem, but we still want to keep a useful system in its place. Good understanding of mem_light will be required since I want to move all work logs, specs, existing memories and docs into the agent_rules directory, obviously we won't have fancy things like doc indexing and doc summaries so they may be skipped, but all of the core components need to be moved and placed in the correct corresponding directories under agent_rules/ - we can also remove all of the 'mem tags' from github since they won't really be necessary anymore