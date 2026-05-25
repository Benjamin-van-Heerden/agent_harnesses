---
title: Move Git checkpointing to onboard
status: todo
created_at: '2026-05-25T15:16:22.194077'
updated_at: '2026-05-25T15:16:22.194077'
completed_at: null
---
Change legal harness local Git snapshot behavior so onboard creates a local Git checkpoint after it creates or cleans session logs and refreshes generated state such as .agent_core/client_matter_index.toml. Automatic snapshotting after every harness command is not required and should be removed unless a specific retained behavior is documented. Setup must require Git, so onboard can assume local git is available after install. Add focused tests that onboard creates a checkpoint when it mutates session/generated state and that ordinary non-onboard commands do not snapshot just because main.py exits.