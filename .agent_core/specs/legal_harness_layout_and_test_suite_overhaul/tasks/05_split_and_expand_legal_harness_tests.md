---
title: Split and expand legal harness tests
status: completed
created_at: '2026-05-26T14:35:16.445376'
updated_at: '2026-05-27T09:36:57.705232'
completed_at: '2026-05-27T09:36:57.705232'
---
Refactor legal/tests/test_setup.py into focused modules with shared helpers, using coding/tests as the organization reference. Suggested files: helpers.py, test_setup.py, test_runtime_paths.py, test_onboard.py, test_clients_matters.py, test_chronology_obligations_todos.py, test_workflows.py, test_typst_compile.py, and test_state_helpers.py. Keep behavior coverage from the existing integration file, add coverage for the .praxis installed namespace and repository template layout, and avoid brittle full-prose AGENTS assertions. Tests should make legal harness behavior easier to inspect and should not leave one giant god file.

## Completion Notes

Split the former monolithic legal/tests/test_setup.py into focused behavior modules with shared helpers. Added legal/tests/helpers.py and focused test modules for setup, runtime paths, onboard, client/matter behavior, chronology/obligations/todos, workflows, Typst compile behavior, and state helpers. Updated test expectations for the installed .praxis namespace, core_docs/docs/local_context layout, harness templates, optional legal_harness_function behavior, and removal of legacy agent_rules migration coverage because backwards compatibility is out of scope. Ran collection, formatted legal tests with ruff, and verified uv run pytest legal/tests passes with 20 tests.
