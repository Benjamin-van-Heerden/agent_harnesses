---
created_at: '2026-05-25T15:41:43.735224'
username: benjamin_van_heerden
---
Work Log - Coding harness user mappings and setup docs prompt

## Overarching Goals

Investigate and fix two coding harness usability issues observed in another installed project: `user_mappings.toml` was not being maintained during onboard, and fresh setup did not ask about optional docs. Also clarify why `.agent_core/docs/data` can appear in `.gitignore`, then propagate the template changes into this repository's installed harness runtime.

## What Was Accomplished

### User mappings maintenance

Updated the coding harness user-mapping state helper so it now has an explicit `ensure_user_mappings_file()` operation. The helper creates a missing `.agent_core/user_mappings.toml` and migrates legacy flat TOML entries such as:

```toml
octo = "Octo User"
```

into the current table format:

```toml
[octo]
name = "Octo User"
```

The loader still accepts both shapes, so existing projects are not forced through a single migration point before commands can read mappings.

Wired that ensure/migration step into onboard after config validation. Onboard now reports when it creates or normalizes the file, which makes the mutation visible in the same way as other onboard-managed `.agent_core` or `.gitignore` updates.

Updated `coding/setup.py` so setup/update performs the same legacy mapping normalization. This keeps fresh installs, manual updates, and onboard behavior aligned.

### Optional docs setup prompt

Changed fresh interactive `coding/setup.py` installs to prompt for optional docs. The prompt lists available optional docs, marks the defaults, accepts space- or comma-separated slugs, treats a blank response as the default docs, and accepts `none`, `no`, or `skip` to install no optional docs.

Non-interactive setup behavior remains unchanged: default docs are installed so existing automated install flows and tests keep the same behavior.

### `.gitignore` investigation

Confirmed that `.agent_core/docs/data` is not hard-coded in the current coding setup template. Setup and onboard add `.gitignore` entries from `[worktree].symlink_paths`, so that path appears when a project's `.agent_core/config.toml` includes it as a configured worktree symlink path. The current default remains `[".claude"]`.

### Installed harness update

Ran `python -B coding/setup.py --update` from the project root to propagate the coding template changes into the installed `.agent_core/harness` runtime. This updated the installed onboard command and user-mapping state helper, refreshed installed optional docs that already existed, and updated `.agent_core/config.toml`'s harness `last_updated_at` timestamp.

Verification completed:

- `uvx ruff check coding/setup.py coding/.agent_core/harness/src/state/user_mappings.py coding/.agent_core/harness/src/commands/onboard/main.py`
- `uv run ty check coding/setup.py coding/.agent_core/harness/src/state/user_mappings.py coding/.agent_core/harness/src/commands/onboard/main.py`
- `git diff --check`

## Key Files Affected

- `coding/setup.py` - added legacy user mapping normalization, fresh interactive optional-doc selection, and selected-doc installation while preserving non-interactive defaults.
- `coding/.agent_core/harness/src/state/user_mappings.py` - added create/migrate support for `user_mappings.toml` and backward-compatible loading of legacy flat mappings.
- `coding/.agent_core/harness/src/commands/onboard/main.py` - runs user mapping ensure/migration during onboard and reports the mutation.
- `.agent_core/harness/src/state/user_mappings.py` - refreshed installed runtime copy from the coding template.
- `.agent_core/harness/src/commands/onboard/main.py` - refreshed installed runtime copy from the coding template.
- `.agent_core/config.toml` - updated by setup with the latest harness `last_updated_at` timestamp.

## Errors and Barriers

The first type-check run failed because `tomllib` table values in `coding/setup.py` needed an explicit cast before calling `.get`. Added the cast and reran the focused checks successfully.
