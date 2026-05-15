---
title: Run harness Python commands with python -B
created_at: '2026-05-15T13:35:24.106682'
updated_at: '2026-05-15T13:35:24.106682'
---
All harness-related Python commands, especially commands shown in instructions such as AGENTS.md, should be written and run with python -B so Python does not create __pycache__ files throughout installed projects.