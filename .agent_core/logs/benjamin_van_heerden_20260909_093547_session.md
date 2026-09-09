---
created_at: '2026-09-09T09:35:47.431745'
username: benjamin_van_heerden
---
Work Log - GitHub SSH remote parsing and auto-update away from raw.githubusercontent.com

## Overarching Goals

Fix two user-reported coding harness failures: GitHub-touching commands rejecting SSH host aliases as "not a GitHub repository", and onboard dying on HTTP 503 from `raw.githubusercontent.com` during auto-update. Deploy the fixes through `dev` → `test` → `main` and confirm update works in this repository.

## What Was Accomplished

### GitHub origin URL parsing

`parse_repo_url` and setup's `parse_github_repo` now take `owner/repo` from:

- `git@<any-host>:owner/repo.git` (SSH config aliases such as `git@github-tendanimukhithi:Zero-Carbon-Charge/charge_mobile_app.git`)
- `ssh://git@<host>/owner/repo.git` and `ssh://git@<host>:22/owner/repo.git`
- existing `https://github.com/owner/repo.git`

Failed parses now say the URL could not be parsed and list accepted forms, instead of "Origin remote is not a GitHub repository".

### Auto-update no longer uses raw.githubusercontent.com

Diagnosed the 503 from this machine: Fastly Johannesburg POP (`cache-jnb-faor7300xx-JNB`), Varnish error 54113 `Backend.max_conn reached`, `X-Cache: MISS`, ~30ms. Not GitHub API quota (4960/5000 remaining) and not payload size (`coding/setup.py` is ~60KB; the tracked repo zip is ~1.08MB and downloaded successfully from `github.com` in ~0.5s).

Auto-update now downloads the template zip from `github.com` with a `codeload.github.com` fallback, extracts it, and runs `coding/setup.py --update` from that tree so setup does not fetch a second copy. One attempt per URL, 8s timeout, no sleep retries. Onboard continues with the installed harness if the download still fails; explicit `update.py --force` still fails hard.

### Deploy and verification in this repo

Committed the template changes, pushed `dev`, and full-deployed `dev` → `test` → `main` without PRs. Then:

- `python -B coding/setup.py --update` installed the new runtime from the local template
- `python -B .agent_core/harness/update.py --force` downloaded the zip from `github.com` and completed in ~5s

`dev`, `test`, and `main` were left aligned at `dd904d7` (`harness updated 20260909`).

## Key Files Affected

- `coding/.agent_core/harness/src/utils/github.py`: SSH alias and `ssh://` origin parsing; clearer parse error
- `coding/setup.py`: matching `parse_github_repo`; zip download with 8s timeout and `codeload` fallback; download failures exit 2
- `coding/.agent_core/harness/src/utils/auto_update.py`: zip-based updater instead of `raw.githubusercontent.com`; fail-open on download errors during onboard
- `coding/.agent_core/harness/src/commands/onboard/main.py`: auto-update hard-fail message no longer tells the agent to set `AGENT_CORE_SKIP_AUTO_UPDATE`
- `coding/tests/test_github_repo_url.py`: URL parse cases including the reported SSH alias
- `coding/tests/test_auto_update.py` and `coding/tests/test_setup_download.py`: zip fallback, fail-fast 503, onboard continues
- `.agent_core/harness/src/utils/auto_update.py`, `.agent_core/harness/src/utils/github.py`, `.agent_core/harness/src/commands/onboard/main.py`, `.agent_core/config.toml`: installed runtime in this repo after the verified update

## Errors and Barriers

A first harden used 3 attempts with a 20s timeout against `raw.githubusercontent.com`. That was rejected: onboard would stall, and it did not explain the 503. Direct probes showed raw failing immediately at the JNB Fastly POP while the GitHub API and the github.com zip succeeded from the same network.

Old installed coding harnesses still fetch `coding/setup.py` from `raw.githubusercontent.com`. They cannot pick up this zip-based updater until raw recovers for one onboard, or until someone runs a one-time zip-based `coding/setup.py --update` in that clone. `AGENT_CORE_SKIP_AUTO_UPDATE` is not an acceptable recovery path.

## What Comes Next

Do not pre-touch every old clone. If raw recovers, the next onboard installs the new updater and they never hit raw again. If JNB is still 503 when someone onboards an old clone, they need a one-shot zip update (the same path verified here), not a skip flag. A follow-up session can write that one-shot command if an old repo actually hits it.

The legal harness auto-update still uses `raw.githubusercontent.com` for `legal/setup.py`; that was not changed.
