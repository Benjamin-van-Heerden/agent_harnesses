# Global Mem Migration Research

## `.mem` to `.agent_core`

### Scope Reviewed

This section reviews the current working-tree implementation of:

- `/Users/benjamin/utils/mem/src/commands/migrate.py`
- `/Users/benjamin/utils/mem/src/utils/migrate.py`
- `/Users/benjamin/utils/mem/harnesses/mem/setup.sh`
- the bundled `/Users/benjamin/utils/mem/harnesses/mem/.agent_core/harness/`
- the current `coding/` harness in this repository

The global `mem` repository has uncommitted migration-related changes. For this research, those working-tree files are treated as the effective implementation because the intended use is a final migration run before shelving `mem`.

### Current Command Surface

`mem migrate` is a Typer command that requires exactly one mode:

```bash
mem migrate --mem-to-lite [--dry-run]
mem migrate --lite-to-mem [--dry-run]
mem migrate --to-harness [--dry-run]
```

For this route, `--to-harness` calls `run_mem_to_harness(target_dir, dry_run)`. The target directory defaults to the current directory.

### Current `.mem -> .agent_core` Behavior

The route is intentionally conservative about existing local state:

- It refuses to run if `.mem/` does not exist.
- If `agent_rules/` exists but `.mem/` does not, it tells the user to run `migrate --lite-to-mem` first, review the generated `.mem` state, then run `migrate --to-harness`.
- It refuses to run if `.agent_core/` already contains any of the durable state paths it knows about: `config.toml`, `user_mappings.toml`, `specs/`, `todos/`, `memories/`, `logs/`, or `docs/`.
- It refuses to run if `.mem.bak/` already exists.
- It refuses to run if the bundled harness setup script is missing at `/Users/benjamin/utils/mem/harnesses/mem/setup.sh`.

In dry-run mode, it does not touch the filesystem or GitHub. It prints source and destination paths, counts legacy specs, tasks, logs, todos, memories, and docs, reports how many linked GitHub issues would be relabeled, and says it would install the harness and rename `.mem/` to `.mem.bak/`.

In non-dry-run mode, it opens the GitHub repository before writing state. This requires `GITHUB_TOKEN`, a GitHub `origin` remote, and token access to that repository. It ensures the new project-local labels exist, then relabels linked issues found in legacy spec and todo frontmatter:

- Specs get labels `spec` and `status:<mapped-status>`.
- Todos get labels `todo` and `status:<mapped-status>`.
- Claimed todos are also closed.

After GitHub relabeling succeeds, the command runs the bundled `setup.sh`, then migrates state:

- `.mem/specs/` -> `.agent_core/specs/`
- `.mem/todos/` -> `.agent_core/todos/`
- `.mem/memories/` -> `.agent_core/memories/`
- `.mem/logs/` -> `.agent_core/logs/`
- `.mem/docs/core/*` -> `.agent_core/docs/*`
- `.mem/docs/*`, except `core/` and `data/`, -> project-root `docs/`
- `.mem/docs/data/` is intentionally skipped
- `.mem/user_mappings.toml` -> `.agent_core/user_mappings.toml`, if present

It converts `.mem/config.toml` into `.agent_core/config.toml`, removes a legacy `<MEMCONTENT>...</MEMCONTENT>` block from root `AGENTS.md`, removes `.github/ISSUE_TEMPLATE/mem-spec.md` if present, and finally renames `.mem/` to `.mem.bak/`.

The final user guidance currently says to run:

```bash
python .agent_core/harness/main.py onboard
```

For this repository's current convention, the verification command should be:

```bash
python -B .agent_core/harness/main.py onboard
```

### Branch Mapping Findings

This is the main migration risk.

Legacy `mem` only modeled `[branches].main`, `[branches].test`, and `[branches].noswitch_branches` as supported config. The current `coding/` harness requires all three protected branch names in `.agent_core/config.toml`:

```toml
[branches]
dev = "dev"
main = "main"
test = "test"
```

The current `run_mem_to_harness` config conversion preserves legacy `main`, `test`, and `noswitch_branches`, but it does not write `dev`. That output is not compatible with the current `coding/` harness because `src.config.branches.get_branch_names()` requires a valid config and `BranchConfig.dev` is required.

The bundled harness that `mem migrate --to-harness` installs is also stale relative to `coding/`:

- It is installed from `/Users/benjamin/utils/mem/harnesses/mem/setup.sh`, not from the current `coding/setup.py`.
- Its config model does not require `[branches].dev`.
- Its branch helper hardcodes `dev="dev"`.
- Its AGENTS instructions and runtime shape lag current `coding/` conventions, including the `python -B` command convention and the newer onboard package split.

This means the current route can produce something that passes the old bundled harness but is not the actual current project-local coding harness shape. For the final real migrations, the migration should install the current `coding/` harness and write a current-compatible config.

### Allowed Source Branch

The migration should only be allowed from the legacy development branch, not from `main`, `test`, a detached HEAD, or a feature/spec branch.

Recommended rule:

- Read the legacy dev branch as `legacy_config["branches"]["dev"]` when present and a non-empty string.
- Otherwise default to `dev`, matching the historical hardcoded mem behavior.
- Require `git branch --show-current` to equal that legacy dev branch before non-dry-run migration.
- Require a clean working tree before non-dry-run migration.
- Fetch origin and require the local legacy dev branch to be in sync with `origin/<legacy-dev>` before non-dry-run migration.
- Require local and remote protected branches for the final mapping, or intentionally let current `coding/setup.py` create missing `test`/`dev` branches only after the converted config is in place.

This branch gate matters because the migration renames the durable state directory, rewrites `AGENTS.md`, writes `.agent_core/config.toml`, removes the legacy issue template, and changes GitHub issue labels. Those changes should land as the development-branch migration commit, not as an accidental main/test/spec-branch mutation.

### Required Quick Fixes Before First Real `.mem -> .agent_core` Migration

No current `agent_harnesses/coding` harness change appears necessary for this route. The required changes are in the final-use `mem migrate --to-harness` path or in the exact operator procedure around it.

Recommended quick-and-dirty changes to `mem` before the real run:

1. Generate `[branches].dev` in `.agent_core/config.toml`.
   - Use legacy `branches.dev` if it exists in raw TOML.
   - Otherwise default to `"dev"`.
   - Keep preserving `main`, `test`, and `noswitch_branches`.

2. Run only from the configured legacy dev branch.
   - Block non-dry-run migration on detached HEAD.
   - Block if current branch is not the resolved legacy dev branch.
   - Block if the working tree is dirty.
   - Fetch and block if local dev and `origin/<dev>` are not synchronized.

3. Install the current `coding` harness, not the stale bundled `harnesses/mem` runtime.
   - The safest sequencing is to write or stage the converted `.agent_core/config.toml` before invoking current `coding/setup.py`, because current setup validates and may create protected branches based on the config.
   - If using the remote bootstrap, run the current coding setup installer from the target project after the converted branch mapping exists.

4. Update final stdout guidance to use `python -B`.

The existing behavior around GitHub relabeling, state refusal, backups, docs placement, AGENTS cleanup, issue-template cleanup, and `.mem.bak/` backup is broadly suitable for a one-time migration once the harness install and branch config gaps are fixed.

### Recommended Command Sequence

For a legacy `.mem` project:

```bash
git status --short
git branch --show-current
git fetch origin
git status -sb
mem migrate --to-harness --dry-run
GITHUB_TOKEN=<token> mem migrate --to-harness
python -B .agent_core/harness/main.py onboard
```

The non-dry-run command should be executed only from the resolved legacy dev branch. If the project uses custom branch names, confirm the final `.agent_core/config.toml` contains the intended `dev`, `main`, and `test` values before running project-local onboarding.

### Manual Verification Checklist

After migration:

- Confirm `.mem/` is gone and `.mem.bak/` exists.
- Confirm `.agent_core/harness/` is the current `coding` harness runtime, not the stale bundled `mem/harnesses/mem` runtime.
- Confirm `.agent_core/config.toml` has `[branches].dev`, `[branches].main`, and `[branches].test` with the expected remapped names.
- Confirm `.agent_core/specs/` contains active, completed, and abandoned specs in the expected directories.
- Confirm task files remain under each spec's `tasks/` directory.
- Confirm `.agent_core/todos/` and `.agent_core/todos/claimed/` preserve todo status and issue IDs.
- Confirm `.agent_core/memories/`, `.agent_core/logs/`, and `.agent_core/user_mappings.toml` were copied.
- Confirm core docs moved to `.agent_core/docs/`.
- Confirm non-core docs moved to root `docs/`.
- Confirm legacy vector/cache docs under `.mem/docs/data/` were not copied.
- Confirm root `AGENTS.md` contains the current `<AGENT_CORE>` block, preserves user notes, and no longer contains `<MEMCONTENT>`.
- Confirm `.github/ISSUE_TEMPLATE/mem-spec.md` was removed if it existed.
- Confirm linked GitHub spec and todo issues have the new `spec`/`todo` and `status:*` labels.
- Confirm claimed todo issues are closed.
- Run `python -B .agent_core/harness/main.py onboard` with network access and read the generated context in full.

