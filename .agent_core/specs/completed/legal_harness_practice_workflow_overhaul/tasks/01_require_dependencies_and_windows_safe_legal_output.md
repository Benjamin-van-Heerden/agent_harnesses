---
title: Require dependencies and Windows-safe legal output
status: completed
created_at: '2026-05-25T15:15:25.380246'
updated_at: '2026-05-25T15:41:14.965063'
completed_at: '2026-05-25T15:41:14.965063'
---
Update the legal harness setup/runtime/docs so Git and Typst are required dependencies with clear Windows/macOS/Linux installation guidance. Setup must check git --version and typst --version and fail before install when missing. Include Windows Typst guidance using winget install --id Typst.Typst. Remove emojis and box-drawing characters from legal harness stdout/stderr and installed legal docs that are part of command guidance. Prefer ASCII headings, separators, and tables that render correctly in PowerShell. Add focused tests for missing dependency guidance and ASCII-safe onboard/core output.

## Completion Notes

Implemented required Git and Typst checks for legal setup using --version before installation, with clear Windows/macOS/Linux install guidance including winget install --id Typst.Typst. Updated runtime dependency checks to require both git and typst with actionable guidance. Removed emoji and box-drawing characters from legal onboard/core harness-owned output and installed placeholder guidance, and replaced harness-owned Unicode separators in command output with ASCII. Added focused setup/runtime dependency guidance tests and ASCII safety assertions for onboard and core command output. Verified with uv run pytest legal/tests/test_setup.py -q, uv run ty check on edited Python files, and uvx ruff check on edited files.
