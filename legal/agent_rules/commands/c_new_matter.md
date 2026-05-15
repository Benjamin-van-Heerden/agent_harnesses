# New matter

Use when the lawyer is opening a new file under an existing client (a lawsuit,
a transaction, an advice request, an appeal, an arbitration, anything).

## When to suggest

Ambient cues:

- "Open a matter for X", "New file for X."
- "X is suing Y", "Y is being sued by X."
- "I'm advising X on Y", "Drafting a deal for X."
- The lawyer mentions a concrete legal problem or transaction tied to an
  existing client without referring to an existing matter.

If the underlying client doesn't yet exist, suggest `c_new_client` first.

## You handle

- **Client.** Resolve from context. If the lawyer says "open a matter for Smith", and `smith_corp` is the only Smith, use it. If ambiguous, ask which.
- **Matter type.** Free-form descriptive. Match natural language: "they're suing us" → `litigation`; "we're arbitrating" → `arbitration`; "I'm advising on the deal" → `transaction`; "appeal" → `appeal`; "tax audit" → `tax`; "labour dispute" → `labour`. Unfamiliar types are fine — just keep the slug short and lowercase.
- **Matter slug.** Derive from the central fact: opposing party, transaction name, subject. "They're being sued by Jones for breach" → `jones_breach`. "Acquisition of XYZ" → `xyz_acquisition`. "Estate of late Mr Smith" → `estate`. Keep it short and unambiguous within the client.
- **Priority.** Derive from urgency cues: "court date next month, urgent" → `urgent` or `high`; "no rush" → `low`; default `normal`. Drives onboard sort.
- **Billing.** Free-form. From context: "hourly", "we agreed a fixed fee", "pro bono", "contingency". Default `hourly`.

## Confirm lightly

> "Opening a litigation matter under Smith Corp for the Jones breach — high priority, hourly. Sound right?"

## Action

```
python agent_rules/scripts/new_matter.py <client> <type> <slug> [priority] [billing]
```

Creates `clients/<client>/matters/open/YYYYMMDD-<type>-<slug>/` with
`info/status.md`, an opening `matter:opened` entry in `info/record.md`,
empty `raw/`, and empty `reference/`.

## After

Confirm in plain language. Then **proactively offer to capture what the lawyer
already told you** about this matter:

- The opposing party, the court, the case number → update `info/status.md`
  frontmatter directly via Edit (don't ask permission for routine updates the
  lawyer just stated as fact).
- Key facts and posture → fill in the `## Posture` and `## Key facts` sections
  in plain prose drawn from what they said.
- Any deadlines mentioned → suggest `c_add_deadline` for each.
- If they mentioned receiving a document (summons, contract, etc.) → suggest
  logging the inbound communication and, if a document is on hand, ask if they
  want to drop it in `raw/`.

Close by surfacing the natural next move: "What's the first thing you want to
do on this — answering affidavit, letter to the other side, something else?"
