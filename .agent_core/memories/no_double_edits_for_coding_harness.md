---
title: No double edits for coding harness
created_at: '2026-05-19T14:50:02.649281'
updated_at: '2026-05-19T14:50:02.649281'
---
When working on the coding harness, make source changes only under coding/. Do not manually duplicate the same edits into the installed .agent_core/harness runtime unless the user explicitly instructs it. The normal propagation loop is: edit coding/ -> run python -B coding/setup.py --update for local uncommitted template updates, or after the change is pushed use the remote bootstrap update command: python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/Benjamin-van-Heerden/agent_harnesses/main/coding/setup.py').read())" -- --update. Treat .agent_core/harness as generated installed runtime, not the source of truth. This only ever applies when working on the coding/ harness.
