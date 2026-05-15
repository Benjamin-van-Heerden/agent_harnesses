---
title: Remove the mem onboard nosync command
status: claimed
issue_id: 98
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/98
created_at: '2026-03-12T12:50:05.091151'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-03-13T11:49:55.457513'
---
Agents ignore if after compactification and there seems to be no clear way to hook this in after such an event. In stead we have to update src/templates/AGENTS.md to contain more information about the workings of mem itself, maybe move the function of mem src/templates/mem.md into AGENTS and then not output that in the onboard output since that would be redundant. Just need to think about that a bit, AGENTS.md (CLAUDE.md) survives compactification events, so this is a good place to put things like this unfortunately we will lose memories and other important context, but we have to trust that compactification is done sensibly and that e.g. the guys at anthropic know what they are doing