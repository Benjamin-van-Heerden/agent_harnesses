# Record a note on a matter

Use to append a free-text entry to a matter's `info/record.md` for anything
that doesn't fit a structured command. Strategic decisions, observations,
internal notes, "client confirmed instructions telephonically",
"considered but rejected approach X" — anything worth a line in the timeline.

The structured commands (`c_log_communication`, `c_add_deadline`,
`c_resolve_matter`) already write to `record.md` for you. `c_record` is the
catch-all.

## When to suggest

Ambient cues:

- "Just to note that..." / "For the record..."
- A decision the lawyer just talked through.
- An observation about how the matter is going.
- A client conversation that wasn't really a comm event ("she popped in,
  we chatted").

Suggest:

> "Want me to add that to the record?"

## You handle

- **Matter.** Resolve from context.
- **Date.** ISO `YYYY-MM-DD`. Default to today.
- **Text.** What the lawyer wants on record. Keep the first line as a useful
  summary (it appears in the entry heading); use further lines for detail if
  needed.

## Action

```
python agent_rules/scripts/record.py <matter_ref> <date> "<text>"
```

The script appends a `note` entry to `info/record.md`. The first line of
`<text>` becomes the summary; the rest becomes the body.

## After

- Confirm in plain language: "Noted — added to the record."
- If the note hints at a follow-up (a thing to do, a date), suggest the
  matching command: `c_create_todo`, `c_add_deadline`.
