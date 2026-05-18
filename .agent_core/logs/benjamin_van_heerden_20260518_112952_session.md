---
created_at: '2026-05-18T11:29:52.694181'
username: benjamin_van_heerden
---
# Work Log - Preserve Onboard Context On Sync Failure

## Overarching Goals

Fix the coding harness onboard behavior so git/sync problems, especially a dirty
tracked working tree, are surfaced as prominent warnings without preventing the
agent from receiving full project context.

## What Was Accomplished

- Investigated the current checked-in coding harness and the installed local
  `.agent_core/harness` runtime after `onboard` aborted with
  `Working tree has uncommitted tracked changes.`
- Confirmed both copies still had the regression: `onboard` re-raised
  non-zero `typer.Exit` from `sync_all()` before building context.
- Updated the checked-in coding harness so default sync failures are captured as
  an onboard sync warning and included in the generated context.
- Added an agent instruction section to onboard output that explicitly requires
  reading the full onboard context before proceeding, and asks the agent to
  report sync warnings before any other work.
- Added a regression test proving `onboard --stdout` continues when a tracked
  file is dirty and includes the sync warning reason.
- Verified the targeted onboard tests pass.
- Ran the full coding test suite; onboard tests passed, while unrelated
  migration/remote-flow tests failed due existing issues outside this patch.

## Key Files Affected

- `coding/.agent_core/harness/src/commands/onboard.py`
- `coding/tests/test_onboard.py`
- `.agent_core/logs/benjamin_van_heerden_20260518_112952_session.md`

## What Comes Next

- Commit and push the coding harness fix.
- After the pushed change is available, update the project-local installed
  harness through the normal setup/update loop so `.agent_core/harness` receives
  the fixed onboard behavior.
- Keep the pre-existing `.gitignore` change separate; it was present before this
  session's edits and was not modified.
