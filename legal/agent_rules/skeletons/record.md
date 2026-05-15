# Record

Chronological, append-only log of everything that has happened on this matter.
Newest entries at the bottom. Entries are written by structured commands
(`c_log_communication`, `c_add_deadline`, `c_resolve_matter`, etc.) and by
`c_record` for anything that doesn't fit a structured command.

Entry format:

    ## YYYY-MM-DD — <kind> — <one-line summary>

    <body — optional, for free-text detail>

Never edit past entries. Add a new entry to correct or expand on an earlier one.
