---
title: Typed state records only
created_at: '2026-05-15T12:31:39.429390'
updated_at: '2026-05-15T12:31:39.429390'
---
Across the coding/ codebase, raw dict records are not allowed for domain state. State loaders must parse data into explicit typed objects (either pydantic BaseModels or dataclasses) with known shapes, and command code should work with those typed objects rather than dict[str, Any].
