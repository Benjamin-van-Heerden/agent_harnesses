---
title: Remove legal src functions layout and standardize components/assets structure
status: open
issue_id: 26
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/26
created_at: '2026-05-27T17:04:45.366425'
claimed_by: null
claimed_at: null
---
Update legal/ so the generated legal harness no longer creates or refers to src/functions/. That layer is unnecessary and misleading for the current Typst architecture: reusable UI/document rendering should live under scoped templates/components, while domain values should live under types and constants. Align legal/setup.py, AGENTS.md wording, scaffold examples, and any generated imports with the PRAXIS_OUT layout where assets live at the root and src/ is reserved for reusable Typst modules such as components, templates, constants, and soft-typed domain structures. Ensure future generated work respects this structure by default and does not reintroduce functions/ unless there is a genuinely non-UI, non-template reusable computation that warrants it.