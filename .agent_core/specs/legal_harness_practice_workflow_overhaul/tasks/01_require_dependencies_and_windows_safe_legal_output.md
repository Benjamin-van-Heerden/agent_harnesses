---
title: Require dependencies and Windows-safe legal output
status: todo
created_at: '2026-05-25T15:15:25.380246'
updated_at: '2026-05-25T15:15:25.380246'
completed_at: null
---
Update the legal harness setup/runtime/docs so Git and Typst are required dependencies with clear Windows/macOS/Linux installation guidance. Setup must check git --version and typst --version and fail before install when missing. Include Windows Typst guidance using winget install --id Typst.Typst. Remove emojis and box-drawing characters from legal harness stdout/stderr and installed legal docs that are part of command guidance. Prefer ASCII headings, separators, and tables that render correctly in PowerShell. Add focused tests for missing dependency guidance and ASCII-safe onboard/core output.