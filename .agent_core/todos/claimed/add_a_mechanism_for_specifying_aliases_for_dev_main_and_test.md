---
title: Add a mechanism for specifying aliases for dev main and test
status: claimed
issue_id: 71
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/71
created_at: '2026-02-02T15:41:16.784468'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-02-02T16:10:40.208967'
---
Some projects have different conventions for which branches constitute the main and test branches, e.g. 'development' 'stage' and 'prod' for 'dev' 'test' and 'main' respectively. Add a configuration flag in config.toml with which we can govern this. This will affect much of the git functionality so we should plan this out carefully. Also add something to init command where this can be set upon initialization 'You are currently on {branch}, is this the main branch for this project' and 'Which of these branches are the 'dev' and 'test' branches or would you like to create new ones' - with some kind of selector or the default option (use typer primitives for this)