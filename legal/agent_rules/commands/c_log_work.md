# Log work

Create a session work log. Run towards the end of every session — these logs
are read on the next onboard and are the main way continuity is preserved.

## When to suggest

- The lawyer says "let's call it", "logging off", "end of day", "we're done".
- A natural pause that marks the end of a substantive working block.
- After completing a major piece of work even if the session continues.

Suggest:

> "Want me to log work?"

Do **not** run unprompted.

## You handle

- **Matter ref** (optional). If most of the session was on one matter, pass
  the matter slug. If the session covered multiple matters, omit.

## Action

```
python agent_rules/scripts/new_log.py [matter_ref]
```

Creates `agent_rules/log/<timestamp>_log.md` with frontmatter populated and
TODO sections.

## Then fill in

Open the file and fill the three sections **drawn from the actual session**,
not from imagination:

- **What was done.** Concrete actions: documents drafted (with file paths),
  communications logged, deadlines added, decisions made. Be specific.
- **What's next.** The most important pending items. What does the next
  session need to know? What's the agenda when the lawyer returns?
- **Notes.** Anything else: blockers, things flagged for follow-up, things the
  lawyer mentioned in passing that matter.

Keep it factual. Logs are read at the start of every next session.

## After

- Confirm briefly: "Logged. Next session will pick up from there."

## Notes

- **Never** create a work log without explicit prompting.
- **Never** edit a previous work log unless the lawyer asks.
