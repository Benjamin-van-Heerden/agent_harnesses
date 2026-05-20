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

## `agent_rules` to `.mem` to `.agent_core`

### Scope Reviewed

This section reviews the current working-tree implementation of:

- `/Users/benjamin/utils/mem/src/commands/migrate.py`
- `/Users/benjamin/utils/mem/src/utils/migrate.py`
- `/Users/benjamin/utils/mem/src/commands/lite.py`
- `/Users/benjamin/utils/mem/src/templates/mem_lite/AGENTS.md`
- `/Users/benjamin/utils/mem/src/templates/mem_lite/agent_rules/commands/`

As with the `.mem -> .agent_core` route, the dirty global `mem` repository is treated as the effective implementation. The migration command is expected to be a final-use bridge, not a long-lived code path.

### Current Command Surface

For this route, the command sequence is:

```bash
mem migrate --lite-to-mem [--dry-run]
mem migrate --to-harness [--dry-run]
```

`--lite-to-mem` calls `run_lite_to_mem(target_dir, dry_run)`. The target directory defaults to the current directory.

### Current `agent_rules -> .mem` Behavior

The route is conservative about top-level state, but less complete than the later `.mem -> .agent_core` route:

- It refuses to run if `agent_rules/` does not exist.
- It refuses to run if `.mem/` already exists.
- It does not check for `agent_rules.bak/` before renaming `agent_rules/` to `agent_rules.bak/`, so an existing backup can fail late.
- It does not check git cleanliness, current branch, remote sync, or GitHub authentication.
- It does not create or relabel GitHub issues. Generated `.mem` specs and todos have no issue IDs unless a later manual process adds them.

Dry-run mode detects branch names, counts specs, logs, todos, and memories, then exits without writing files or renaming `agent_rules/`.

In non-dry-run mode, it creates `.mem/` directories, converts records, writes `.mem/config.toml`, creates an empty `.mem/user_mappings.toml`, and renames `agent_rules/` to `agent_rules.bak/`.

### Parser Behavior

The parser is deterministic and expects mem-lite's generated markdown shape. It is not an AI-assisted semantic parser.

Specs:

- It reads spec files matching `agent_rules/spec/s_*__*.md`, plus `agent_rules/spec/completed/s_*__*.md` and `agent_rules/spec/abandoned/s_*__*.md`.
- `parse_lite_spec_filename()` expects `s_YYYYMMDD_username__slug.md`; if the filename does not match, created time falls back to now and assigned user may be missing.
- The spec title is the first `# ` heading, falling back to a titleized file slug.
- Status is read from an inline marker exactly like `` `%% Status: Active %%` `` and mapped through `LITE_TO_MEM_STATUS`.
- Branch is read from an inline marker exactly like `` `%% Branch: branch-name %%` `` and copied into `.mem` spec frontmatter.
- The spec body is the exact `## Description` section, with a `## Completion Report` section appended only when it is present and not the placeholder text.
- Tasks are parsed only from the `## Tasks` section and only when each task is a `###` heading.
- A task is marked completed if any line in its task body contains a checked markdown checkbox, regardless of which checkbox is checked.
- Task body content is reconstructed from `#### Description`, `#### Implementation Details`, and `#### Key Files`. Placeholder text starting with `*(migrated` is skipped.
- Task file order follows the sorted order of parsed `###` task section titles because `_split_sections()` returns a dict keyed by heading title. If duplicate task headings exist, later content overwrites earlier content.

Logs:

- It reads flat `agent_rules/log/*.md` files.
- Filenames must match `YYYYMMDDHHmm_username.md` or `YYYYMMDDHHMMSS_username.md`; non-matching logs are skipped.
- If the first line matches `# Work Log - ...`, that title is parsed but not used in the generated filename.
- A spec reference is detected from `## Spec: `path`` and only converted to `spec_slug` if the path resembles `s_<date>_<user>__<slug>.md`.
- The original log content is kept as the generated `.mem` log body.

Todos:

- It reads open todos from `agent_rules/todos/t_*.md` and claimed todos from `agent_rules/todos/claimed/t_*.md`.
- The title is the first `# ` heading, falling back to a titleized slug.
- `**Created:**` and `**Claimed:**` values are treated as dates and converted by appending `T00:00:00`.
- Generated todos always have `issue_id = null` and `issue_url = null`.
- Generated claimed todos have `claimed_by = null`, even when the source file has a claimed date.

Memories:

- It reads `agent_rules/memories/m_*.md`.
- The first `# ` heading becomes the memory title; the body is everything after that heading.
- Created and updated timestamps are the migration time, not the original authoring time.

Docs and config:

- It copies `agent_rules/docs/core/*.md` into `.mem/docs/core/`.
- It copies only top-level `agent_rules/docs/*.md` into `.mem/docs/`.
- Nested non-core docs are not copied.
- `agent_rules/project_description.md` becomes the `.mem` project description unless it starts with `TODO:`.
- `.mem/user_mappings.toml` is created empty.

### Where Manual or AI-Assisted Review Is Needed

The existing parser is sufficient when the project was produced by the mem-lite templates and not heavily hand-edited. It is risky for looser `agent_rules` projects because the structured conversion depends on exact filenames and headings.

Manual review is required for:

- specs whose filenames do not match `s_YYYYMMDD_username__slug.md`;
- specs without `## Description`, `## Tasks`, or `###` task headings;
- tasks represented only as checklists under one heading instead of one `###` heading per task;
- duplicate task headings;
- branch markers that are missing, stale, or point to deleted feature branches;
- completed specs whose status marker disagrees with their directory;
- logs with non-standard filenames or spec references;
- claimed todos where the claimer matters;
- nested docs under `agent_rules/docs/` outside `core/`;
- any source content that used prose structure instead of the mem-lite template.

AI-assisted interpretation may be useful before running `--lite-to-mem` when a spec's task structure is ambiguous. The safer approach is to normalize the `agent_rules` files first into the expected template shape, then run the deterministic migration and review the generated `.mem` output.

### Branch Mapping Findings

This route has two branch-handling gaps.

First, `run_lite_to_mem()` detects branch names from root `AGENTS.md` by importing `_detect_branches()` from `src.commands.lite`. That helper scans for branch bullets in the mem-lite branching model:

- a line containing `the main working branch` becomes `dev_branch`;
- a line containing `production branch` becomes `prod_branch`;
- a line containing `test/staging branch` becomes `test_branch`;
- missing values default to `dev`, `main`, and `test`.

This is reasonable for mem-lite projects created from the bundled template, but it is fragile for hand-edited `AGENTS.md` files. The operator should verify the detected branch names during dry-run output.

Second, `create_mem_config(mem_dir, project_name, project_description, dev_branch, prod_branch, test_branch)` accepts `dev_branch` but does not persist it. It calls `generate_default_config_toml(..., main_branch=prod_branch, test_branch=test_branch)`, and the legacy `.mem` config generator writes only:

```toml
[branches]
main = "..."
test = "..."
```

That was acceptable for legacy `mem`, which hardcoded or derived `dev` elsewhere, but it compounds the later `.mem -> .agent_core` blocker: without a fix, the final harness config still cannot reliably know the intended development branch.

### Allowed Source Branch

The complete `agent_rules -> .mem -> .agent_core` migration should run from the configured mem-lite development branch, not from `main`, `test`, a detached HEAD, or an old spec branch.

Recommended rule for the first command:

- Run `mem migrate --lite-to-mem --dry-run` from the target project root.
- Confirm dry-run detected the intended `dev`, `prod`, and `test` branch names.
- Require `git branch --show-current` to equal the detected mem-lite development branch before non-dry-run `--lite-to-mem`.
- Require a clean working tree before non-dry-run `--lite-to-mem`.
- Fetch origin and require local development branch to be in sync with `origin/<dev>`.
- Require `agent_rules.bak/` not to exist before non-dry-run migration.

Recommended rule for the second command:

- Review and fix generated `.mem` state on the same development branch.
- Commit the `.mem` migration result if the operator wants an audit point before the final harness conversion.
- Run `mem migrate --to-harness --dry-run` from that same development branch.
- Run non-dry-run `mem migrate --to-harness` only after the `.mem -> .agent_core` quick fixes from the previous section are present.

Running both commands from the development branch matters because the first command renames `agent_rules/`, writes `.mem/`, and rewrites local state, while the second command installs the project-local harness, relabels GitHub issues, removes old instructions, and renames `.mem/`. Those are development-branch migration commits, not production or staging mutations.

### Required Quick Fixes Before First Real `agent_rules -> .mem -> .agent_core` Migration

No current `agent_harnesses/coding` harness change appears necessary for this route. The final-use fixes belong in the `mem` migration path or the operator procedure.

Recommended quick-and-dirty changes to `mem` before the real run:

1. Persist the detected development branch somewhere that survives into the final harness migration.
   - Best option: teach `create_mem_config()` and `generate_default_config_toml()` to write `[branches].dev`.
   - Acceptable one-time option: manually add `dev = "<detected-dev>"` to `.mem/config.toml` after `--lite-to-mem` and before `--to-harness`, then ensure `--to-harness` preserves it into `.agent_core/config.toml`.

2. Gate non-dry-run `--lite-to-mem` on branch and git state.
   - Block detached HEAD.
   - Block current branch != detected development branch.
   - Block dirty working tree.
   - Fetch and block when local development branch differs from `origin/<dev>`.
   - Block when `agent_rules.bak/` already exists.

3. Improve review guidance after `--lite-to-mem`.
   - Tell the operator to inspect `.mem/specs/**/spec.md`, `.mem/specs/**/tasks/*.md`, `.mem/todos/`, `.mem/logs/`, `.mem/memories/`, `.mem/docs/`, `.mem/config.toml`, and `.mem/user_mappings.toml`.
   - Make clear that linked GitHub issues are not preserved or relabeled until the later harness migration, and generated lite-to-mem records usually have no issue IDs.

4. Apply the `.mem -> .agent_core` fixes from the previous section before running the second command.
   - Generate current-compatible `[branches].dev`.
   - Run only from the resolved development branch.
   - Install the current `coding` harness instead of stale `mem/harnesses/mem`.
   - Use `python -B` in final stdout guidance.

### Recommended Command Sequence

For a mem-lite `agent_rules` project:

```bash
git status --short
git branch --show-current
git fetch origin
git status -sb
mem migrate --lite-to-mem --dry-run
mem migrate --lite-to-mem
git diff -- .mem
```

Then review the generated `.mem` state. Fix parser misses before proceeding. At minimum, verify branch config before the second command:

```bash
cat .mem/config.toml
mem migrate --to-harness --dry-run
GITHUB_TOKEN=<token> mem migrate --to-harness
python -B .agent_core/harness/main.py onboard
```

Both non-dry-run migration commands should be executed only from the resolved development branch. If the project uses custom branch names, do not proceed until the intended development branch is visible in the intermediate `.mem/config.toml` and final `.agent_core/config.toml`.

### Manual Verification Checklist

After `--lite-to-mem`:

- Confirm `agent_rules/` is gone and `agent_rules.bak/` exists.
- Confirm `.mem/specs/` contains active specs, `.mem/specs/completed/` contains completed specs, and `.mem/specs/abandoned/` contains abandoned specs.
- Confirm spec titles, status, assigned user, branch, created/completed timestamps, and bodies are sensible.
- Confirm each spec's `tasks/` directory has the expected task count, order, titles, statuses, and body content.
- Confirm duplicate or prose-only task sections were not lost.
- Confirm `.mem/logs/` contains all expected logs and spec references resolve where possible.
- Confirm `.mem/todos/` and `.mem/todos/claimed/` preserve open vs claimed status.
- Confirm `.mem/memories/` content is complete, accepting that timestamps are migration-time values.
- Confirm `.mem/docs/core/` and `.mem/docs/` contain the expected docs.
- Confirm no important nested non-core docs were skipped.
- Confirm `.mem/config.toml` has the intended project name, description, main branch, test branch, and either a persisted development branch or a documented manual correction before continuing.
- Confirm `.mem/user_mappings.toml` is intentionally empty or manually populate it before harness migration.

After the later `--to-harness`, use the `.mem -> .agent_core` verification checklist above.
