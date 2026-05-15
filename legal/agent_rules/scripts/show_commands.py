"""Usage: show_commands.py

Dumps every command playbook in agent_rules/commands/ to stdout, with clear
separators between files. Used at onboard time so the agent loads all command
triggers and execution detail in a single read.

Excludes:
  - c_onboard.md         (the agent is in this flow already)
  - c_initial_setup.md   (one-shot first-run flow; dispatched explicitly from
                          c_onboard, not needed in routine session context)
"""

from __future__ import annotations

import sys

from _lib import die, praxis_root

EXCLUDED = {"c_onboard.md", "c_initial_setup.md"}
SEPARATOR = "=" * 72


def main(argv: list[str]) -> None:
    if argv:
        die("usage: show_commands.py")

    root = praxis_root()
    commands_dir = root / "agent_rules" / "commands"
    if not commands_dir.is_dir():
        die(f"commands directory not found: {commands_dir}")

    files = sorted(p for p in commands_dir.glob("c_*.md") if p.name not in EXCLUDED)
    if not files:
        die("no command playbooks found")

    print(f"# Praxis command playbooks ({len(files)} files)")
    print()
    print("Each section below is a complete command playbook. The 'When to use'")
    print("/ 'When to suggest' headings tell you when to dispatch to that")
    print("command; the 'Action' heading shows the script invocation.")
    print()

    for f in files:
        print(SEPARATOR)
        print(f"FILE: agent_rules/commands/{f.name}")
        print(SEPARATOR)
        print()
        print(f.read_text().rstrip())
        print()


if __name__ == "__main__":
    main(sys.argv[1:])
