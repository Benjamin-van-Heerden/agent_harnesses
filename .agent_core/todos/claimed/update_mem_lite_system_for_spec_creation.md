---
title: Update mem lite system for spec creation
status: claimed
issue_id: 99
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/99
created_at: '2026-03-12T14:33:22.090385'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-03-12T14:44:29.692283'
---
When creating a spec on mem lite, currently the agent asks you if you want to create a spec branch, if yes, then we need to do a couple more things, first *tie spec to branch* meaning, add something to expicitly say that this spec is on this branch in the spec file, then git add commit push so that dev branch stays clean and tracked everywhere. Also, in onboard, let's just do a git fetch && git status as well and have the agent warn if we are behind