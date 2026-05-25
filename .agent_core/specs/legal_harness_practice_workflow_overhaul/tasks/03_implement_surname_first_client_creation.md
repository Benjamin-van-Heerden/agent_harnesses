---
title: Implement surname-first client creation
status: todo
created_at: '2026-05-25T15:15:40.251685'
updated_at: '2026-05-25T15:15:40.251685'
completed_at: null
---
Rework legal client creation so natural person clients can be created surname-first with deterministic slug generation, e.g. Van Heerden, Benjamin -> van_heerden_benjamin. Support explicit entity/non-person clients. Add explicit suffix handling for generated slug collisions; do not guess suffixes. Collision errors must instruct the agent to ask the lawyer for a distinguishing suffix such as location, ID hint, company, or role. Update typed client state, command interface, docs, and tests.