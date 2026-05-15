---
title: add adr command
status: claimed
issue_id: 92
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/92
created_at: '2026-02-25T12:30:48.184977'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-03-03T12:26:18.675087'
---
add a command for logging architecture decision records, these are files that live in .mem/adrs - these files are concerned with decisions made which overrule active sow's or agreements when doing contractual work to document discussed changes. adrs should have a fixed format which addresses a section of a sow or agreement and overrules or modifies it on record, dates for when the decision was made should be added as well as correspondence records (these cannot be known to the agent at time of creation so the agent should ask the user for this information - include this in the intructions that are logged when 'mem adr new' is called). Also associate relevant frontmatter so that referential integrity with the orignal document/agreement is maintained.