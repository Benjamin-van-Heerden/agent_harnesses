# Ingest raw materials

Use when files have appeared in a matter's `raw/` directory and need to be
parsed into agent-readable markdown in `reference/`.

## When to suggest

- The lawyer mentions dropping a file into a matter ("I put the contract in
  Smith's raw folder").
- You notice unparsed files when focusing on a matter (compare `raw/` and
  `reference/`).
- The lawyer asks a question about an inbound document and you don't have a
  parsed version yet.

Suggest:

> "Want me to parse [file] into reference so I can work with it?"

## You handle

- **Matter ref.** Resolve from context.
- List unparsed files: `python agent_rules/scripts/list_unparsed.py <matter_ref>`.

## Confirm

If multiple files are unparsed, ask which to parse (or "all").

## For each file

1. **Read** the raw file. For PDFs, use the Read tool.
2. **Long PDFs** (more than ~20 pages or large file size) — warn the lawyer.
   Offer:
   - parse the whole thing in chunks
   - parse specific page ranges only
   - skip until a chunked-parse helper exists
3. **Write** a faithful markdown rendering to `reference/<basename>.md`.
   Preserve:
   - Headings and structure
   - Tables (as markdown tables)
   - Numbered clauses and paragraph numbering
   - Page boundaries (as `<!-- page N -->` markers)
4. **Do not summarise.** This is a faithful parse, not a précis. Future
   sessions need the full text.
5. If the file is a scanned image without OCR, flag this — the current
   pipeline doesn't handle OCR.

## After

- Confirm what was parsed.
- Re-run `list_unparsed.py` to show what's still unparsed.
- If the parse uncovered facts that affect the matter's posture, update
  `info/status.md`.
