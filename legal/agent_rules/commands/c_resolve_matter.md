# Resolve matter

Use when a matter is concluded — settled, dismissed, transaction completed,
advice given, estate wound up.

## When to suggest

Ambient cues:

- "Settled", "Closed", "Done with this matter."
- "We've signed off", "Transaction completed", "Estate wound up."
- "Dismissed with costs", "Withdrew the action", "Out of court settlement."
- The lawyer signals the work on a specific matter is finished and there's
  nothing further to do.

Suggest:

> "Want me to mark that resolved?"

## Before running

Confirm with the lawyer that the matter is genuinely concluded. Surface anything
that suggests it isn't:

- Are all deadlines either done, missed, or waived? If any are still `[open]`
  in `info/deadlines.md`, mention them and ask whether to mark them done/waived
  first.
- Is there a final document still to be sent or filed?
- Has the closing communication to the client been logged?

If any of those are unresolved, ask the lawyer how to handle them before
resolving.

## You handle

- **Matter ref.** Resolve from context.

## Confirm lightly

> "Resolving the Smith / Jones arbitration. Sound right?"

## Action

```
python agent_rules/scripts/resolve_matter.py <matter_ref>
```

Sets `status: resolved` in the frontmatter, appends a `matter:resolved` entry
to `info/record.md`, and moves the matter directory from `matters/open/` to
`matters/resolved/`.

## After

- Confirm in plain language.
- Suggest a final work log if the resolution is substantive: "Want me to log
  the outcome?"
- If the lawyer mentioned a closing reason ("settled for R200k", "dismissed
  with costs", "transaction completed"), capture it in the matter's
  `info/status.md` Posture before or after the resolve.
