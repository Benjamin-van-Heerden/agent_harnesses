---
title: Strengthen legal harness reusable Typst architecture
status: claimed
issue_id: 24
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/24
created_at: '2026-05-27T16:57:54.527957'
claimed_by: benjamin_van_heerden
claimed_at: '2026-05-28T10:33:47.467646'
---
Review legal/ and update the harness so generated legal work strongly prefers reusable, clean Typst structures. Emphasize aggressive extraction into shared templates, components, constants, and soft-typed domain values instead of one-off document-local helpers. Guard against disorganized generated work by making modularity, reuse, and typed data structures first-class defaults in AGENTS.md, setup scaffolding, examples, and any relevant generator/template code. The PRAXIS_OUT cleanup showed that valuation schedules, leases, settlement agreements, trust deeds, forms, money values, parties, and document shells should be reusable modules rather than repeated local code.