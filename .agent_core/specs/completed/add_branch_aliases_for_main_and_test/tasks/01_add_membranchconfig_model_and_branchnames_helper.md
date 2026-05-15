---
title: Add MemBranchConfig model and BranchNames helper
status: completed
created_at: '2026-02-02T16:09:46.625639'
updated_at: '2026-02-02T16:26:54.585416'
completed_at: '2026-02-02T16:26:54.585411'
---
Add a new MemBranchConfig Pydantic model to src/config/models.py with 'main' (default: 'main') and 'test' (default: 'test') string fields. Add this as a 'branches' field on MemLocalConfig with default_factory=MemBranchConfig. Then add a BranchNames frozen dataclass and get_branch_names() function that loads from config and returns BranchNames(dev='dev', test=config.branches.test, main=config.branches.main). BranchNames should have a 'protected' property returning [self.dev, self.test, self.main]. Put BranchNames and get_branch_names in src/config/models.py (with lazy imports inside get_branch_names to avoid circular imports).

## Completion Notes

Added MemBranchConfig Pydantic model with main/test fields, added branches field to MemLocalConfig with default_factory, added BranchNames frozen dataclass with protected property, added get_branch_names() with lazy imports and config fallback to defaults