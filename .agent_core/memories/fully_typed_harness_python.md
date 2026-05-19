---
title: Fully typed harness Python
created_at: '2026-05-19T13:01:38.309045'
updated_at: '2026-05-19T13:01:38.309045'
---
All harness-based Python code must have explicit type annotations for every function argument and every return value. This applies to harness templates, installed harness runtime code, setup/update support scripts, command modules, utilities, state modules, and harness tests; do not leave helper functions, CLI callbacks, or test functions with untyped parameters or missing return annotations.