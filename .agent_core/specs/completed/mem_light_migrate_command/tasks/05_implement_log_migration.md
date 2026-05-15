---
title: Implement log migration
status: completed
created_at: '2026-02-11T14:59:35.951448'
updated_at: '2026-02-11T17:23:30.552342'
completed_at: '2026-02-11T17:23:30.552335'
---
Add a function _migrate_logs(mem_dir: Path, agent_rules_dir: Path) that migrates all logs from .mem/logs/ to agent_rules/log/. For each log file: (1) Parse frontmatter (created_at, username, spec_slug). (2) Strip frontmatter, keep markdown body. (3) Derive new filename: {YYYYMMDDHHmm}_{username}.md from created_at. (4) Group logs by spec_slug. For each spec_slug group, sort by created_at — the LAST (most recent) log goes to agent_rules/log/ as a naked log (spec-completion summary), all other logs go to agent_rules/log/{spec_slug}/. (5) Logs with no spec_slug go directly to agent_rules/log/ (naked). Ensure log/{spec_slug}/ directories are created as needed.

## Completion Notes

Added _migrate_logs() to light.py. Handles both old (date) and new (created_at) frontmatter formats. Groups logs by spec_slug — most recent per spec goes naked to log/, older ones to log/{spec_slug}/. Logs without spec_slug go naked. Strips frontmatter, keeps body only.