---
created_at: '2026-05-21T12:29:41.521014'
username: benjamin_van_heerden
---
Work Log - Release Harness Fixes And Verify Urbion Update

## Overarching Goals

Resolve why the Urbion-AI project still reported `Issue sync complete. Actions: 2` after the idempotent issue-sync fix, clarify whether auto-update was respecting its interval, and verify the installed project-local harness no longer mutates tracked `.agent_core` state on normal onboard.

## What Was Accomplished

### Identified the release branch mismatch

Confirmed the Urbion-AI installed harness still had the old issue-sync implementation without `_issue_needs_update()`. The reason was that harness auto-update downloads `coding/setup.py` and the harness archive from the `main` branch, while the earlier fixes had only been pushed to `dev`.

Promoted the harness repository changes through the protected branch flow:

- `python -B .agent_core/harness/main.py merge into test dev`
- `python -B .agent_core/harness/main.py merge into main test --force`

After promotion, `origin/main`, `origin/test`, and `origin/dev` all pointed at `e1b6872`, which includes the idempotent issue-sync fix and spec artifact preservation fix.

### Verified auto-update timing

Checked Urbion-AI's harness config and updater state. With:

```toml
[harness]
update_interval_days = 3
last_updated_at = "2026-05-21T10:21:12Z"
```

the installed updater reported `_update_due() == False` at `2026-05-21T10:26Z`. That means the interval logic was working after the timestamp was present. The earlier update ran because the project had not yet received a current `last_updated_at` from the updated setup path.

### Force-updated and verified Urbion-AI

Ran a one-time forced harness update in `/Users/benjamin/Documents/Urbtec/Urbion-AI` after `main` contained the fixes:

```bash
python -B .agent_core/harness/update.py --force
```

This created Urbion-AI commit `9c4b81c harness updated 20260521`. The installed `sync/main.py` now contains the `_issue_needs_update()` guard.

Ran normal Urbion-AI onboard afterward and verified:

- `Issue sync complete. Actions: 0`
- `.agent_core` had no tracked git changes after onboard
- updater due check remained false with `last_updated_at = "2026-05-21T10:28:49Z"`

## Key Files Affected

- Harness repo protected branches: promoted `dev` to `test` and `main` so remote auto-update serves the fixed harness.
- `/Users/benjamin/Documents/Urbtec/Urbion-AI/.agent_core/harness/...` - refreshed by the forced harness update from corrected `main`.
- `/Users/benjamin/Documents/Urbtec/Urbion-AI/.agent_core/config.toml` - `last_updated_at` refreshed by setup/update.
- `.agent_core/logs/benjamin_van_heerden_20260521_122941_session.md` - this work log.

## What Comes Next

Consider tightening the harness update UX so setup reports that `.agent_core/harness` is a managed runtime replacement and so no-op updates are less visually alarming in editors that show transient delete/copy operations.
