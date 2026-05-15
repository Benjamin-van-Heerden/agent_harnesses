# Add deadline

Use to record any date with a consequence: court filing, prescription window,
diary date, follow-up.

## When to suggest

Ambient cues:

- "Plea is due 20 court days from now."
- "Court date is 15 May."
- "Prescription runs out in three years."
- "I need to follow up by Friday."
- "We need to respond within 14 days."
- "Filing is due X", "Diary the date", "Note the date for X."

Suggest:

> "Want me to diary that?"

## You handle

- **Matter.** Resolve from context.
- **Date.** ISO `YYYY-MM-DD`. Convert from natural language ("next Friday", "in
  10 court days") to a concrete date — see *Court days* below.
- **Type.** Short tag: `court_filing`, `prescription`, `client_meeting`,
  `discovery_response`, `appeal_window`, `follow_up`, etc. Free-form.
- **Description.** One short line: what is due.

## Court days vs calendar days (SA)

In SA practice, "court days" exclude Saturdays, Sundays, and public holidays.
Common rule-based deadlines:

- **Notice of intention to defend:** 10 court days from service of summons.
- **Plea:** 20 court days from notice of intention to defend (or other date set by rule).
- **Replication:** 15 court days from plea.
- **Discovery:** 20 court days after close of pleadings.

When the lawyer states a deadline in court days, calculate calendar-equivalent
carefully. If you're unsure of the SA public holiday list for the year, ask
the lawyer or note your assumption: "Counting from today (29 April 2026), 10
court days lands on 14 May 2026 — assuming no public holidays in that window.
Confirm?"

## Action

```
python agent_rules/scripts/add_deadline.py <matter_ref> <date> <type> "<description>"
```

The script appends an `[open]` entry to `info/deadlines.md`, updates
`next_deadline` in `info/status.md` to the earliest open deadline, and
appends a `deadline:added` entry to `info/record.md` so the chronology stays
complete.

## After

- Confirm in plain language: "Added. Next deadline now 15 May 2026 — answering
  affidavit."
- If the deadline is within 14 days, mention urgency.
- For high-stakes deadlines (court filing, prescription), suggest a
  preparation todo so the work starts well before the date:
  > "Want me to add a todo to start drafting the answering affidavit by 8
  > May?"

## Closing a deadline later

When a deadline is met or passes, edit `info/deadlines.md` directly: change `[open]`
to `[done]`, `[missed]`, or `[waived]`. Then re-run `add_deadline.py` against
any other open deadline (or edit `next_deadline` in `info/status.md`) to re-sync.
