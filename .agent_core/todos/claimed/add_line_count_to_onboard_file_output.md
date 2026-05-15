---
title: Add line count to onboard file output
status: claimed
issue_id: 90
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/90
created_at: '2026-02-24T18:14:59.821519'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-02-24T18:16:09.144871'
---
in the 'mem onboard' command output, let's add the line count for the temp file that is generated. Some agents and tools have hard limits on the file sizes they can read at a time (so they need to break it up into multiple reads), a hint on how many lines the generated file is may help