# New client

Use when the lawyer mentions someone new they're acting for.

## When to suggest

Ambient cues:

- "I have a new client."
- "Sign up X", "Take on X."
- "I'll be acting for [new name]" — and the name doesn't match any existing
  client.
- The lawyer starts describing a new entity or person without referring to an
  existing matter.

If the trigger is ambiguous (could be a new matter under an existing client),
ask which.

## You handle

- **Display name.** What the lawyer says ("Smith Corp Pty Ltd", "John Doe").
- **Slug.** Derive from the display name: lowercase, alphanumeric, underscore-separated, short. "Smith Corp Pty Ltd" → `smith_corp`. "Robert van der Merwe" → `vd_merwe` or `rob_vd_merwe`. Use judgement: short, recognisable, unambiguous against existing clients.
- **Type.** Free-form descriptive — derive from context. "Pty Ltd" → `company`. "the trust" → `trust`. "the deceased estate" → `estate`. A natural person → `individual`. Unfamiliar SA entity types are fine: `close_corporation`, `voluntary_association`, `body_corporate`. Set what makes sense.

## Confirm lightly

Before running, confirm in one short sentence:

> "I'll set up Smith Corp Pty Ltd as a client (filed as `smith_corp`, type: company). Sound good?"

If the lawyer wants different naming, take their lead.

## Action

```
python agent_rules/scripts/new_client.py <slug> "<display_name>" <type>
```

The script creates `clients/<slug>/profile.md` with frontmatter populated, plus
empty `matters/open/` and `matters/resolved/` directories.

## After

- Confirm in plain language: "Done. Smith Corp Pty Ltd is set up."
- Offer the natural next step: "Want to open a matter for them now?" or, if the
  lawyer mentioned context that fills out the profile (contact details, fee
  arrangement), offer to fill those in: "Want me to capture their contact
  details and fee arrangement?"
- Update the profile body sections only if the lawyer agrees.
