---
title: Add mem light init and mem light update command
status: claimed
issue_id: 80
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/80
created_at: '2026-02-11T11:04:51.207676'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-02-11T11:08:28.026056'
---
In some projects, e.g. when doing consulting and working on their repos, it is impossible to actually use mem, we can however achieve something like mem with simple markdown file instructions that the agent reads and executes. I have created the system in src/templates/mem_light - the commands should basically copy/overwrite these files int the project directory we are currently (I would also like us to look at the files in this directory in comparison with mem and see if we need to add or remove anything