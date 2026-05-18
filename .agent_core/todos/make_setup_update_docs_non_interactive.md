---
title: Make setup update docs non-interactive
status: open
issue_id: 1
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/1
created_at: '2026-05-18T15:57:04.761611'
claimed_by: null
claimed_at: null
---
The command `bash <(curl -sL https://raw.githubusercontent.com/Benjamin-van-Heerden/agent_harnesses/main/coding/setup.sh) --update` should not ask about optional docs. Optional docs should be controlled only through explicit docs commands: listing available docs, updating docs already present, or adding requested docs.
