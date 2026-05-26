---
title: Split and expand legal harness tests
status: todo
created_at: '2026-05-26T14:35:16.445376'
updated_at: '2026-05-26T14:35:16.445376'
completed_at: null
---
Refactor legal/tests/test_setup.py into focused modules with shared helpers, using coding/tests as the organization reference. Suggested files: helpers.py, test_setup.py, test_runtime_paths.py, test_onboard.py, test_clients_matters.py, test_chronology_obligations_todos.py, test_workflows.py, test_typst_compile.py, and test_state_helpers.py. Keep behavior coverage from the existing integration file, add coverage for the .praxis installed namespace and repository template layout, and avoid brittle full-prose AGENTS assertions. Tests should make legal harness behavior easier to inspect and should not leave one giant god file.