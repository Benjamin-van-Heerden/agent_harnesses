# Lint

Validate frontmatter across all clients and matters. Use to catch schema drift
after manual edits.

## When to use

- Suspect frontmatter has been broken by a manual edit.
- Things look weird — onboard surfaces nothing for a matter you know exists,
  or a deadline isn't appearing in upcoming.
- Periodically, as a sanity check.

You don't need to suggest this to the lawyer routinely — it's a maintenance
tool. Run it when needed.

## Action

```
python agent_rules/scripts/lint.py
```

Reports missing required keys and out-of-set values for `status` and
`priority`. Exits non-zero if any issue.

## After

- For each issue, open the offending file, show the lawyer the problem in
  plain language, propose a fix.
- Common fixes: typos in `status` or `priority`, accidentally cleared
  required keys after a manual edit.
