# Log communication

Use to record any inbound or outbound contact: letter, email, call, meeting,
court filing, SMS, anything that's a legally meaningful contact event. The
entry goes into the matter's `info/record.md` (the canonical chronology).

## When to suggest

Ambient cues:

- "Tom called this morning."
- "I just sent the demand letter."
- "Got an email from opposing counsel."
- "Met with the client yesterday."
- "Filed the answering affidavit."
- The lawyer pastes an email body (inbound or outbound — figure out which
  from headers/sender/recipient).

Suggest:

> "Want me to log that?"

## You handle

- **Matter.** Resolve from context. The active matter is usually obvious.
- **Date.** ISO `YYYY-MM-DD`. Default to today unless the lawyer says otherwise.
- **Direction.** `in` (we received) or `out` (we sent). Determine from natural language.
- **Medium.** Free-form: `letter`, `email`, `call`, `meeting`, `court_filing`, `sms`, `whatsapp`. Match what the lawyer said.
- **Counterparty.** Who the contact was with: "Jones Inc Attorneys", "the client", "Judge Khumalo's clerk", "opposing counsel".
- **Subject.** One short line.

## Confirm lightly (if needed)

For a clearly stated event, just record it. Briefly confirm: "Logged: outbound
letter to Jones, demand for payment." For ambiguous cases, confirm before
recording.

## Action

```
python agent_rules/scripts/log_communication.py <matter_ref> <date> <direction> <medium> <counterparty> "<subject>"
```

Appends an entry to the matter's `info/record.md` with kind
`comm:<direction>:<medium>` and `_TODO: body_` placeholder for the body.

## Then fill in

- Open `info/record.md`, find the new entry, and replace `_TODO: body_` with
  a concise account: who said what, what was agreed, what action items
  emerged. For pasted emails, you can include the email body in full here —
  this file is the chronological record and stays with the matter.

## After

- If the communication created a deadline (e.g. they gave you 10 days to
  respond), suggest `c_add_deadline`.
- If it surfaced a follow-up, suggest `c_create_todo`.
- If it shifts the matter's posture, update `info/status.md` directly.
