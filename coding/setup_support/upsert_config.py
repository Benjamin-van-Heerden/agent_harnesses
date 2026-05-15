import argparse
import re
from pathlib import Path


def default_config(project_name: str) -> str:
    return f'''[project]
name = "{project_name}"
description = """
Add your project description here.
"""

[[files]]
path = "README.md"
description = "Project overview and setup instructions"

[worktree]
symlink_paths = [".agent_core/docs/data", ".claude"]

[branches]
dev = "dev"
main = "main"
test = "test"
# [branches.noswitch_branches]
# company_xyz = "main"
'''


def section_exists(content: str, section: str) -> bool:
    return re.search(rf"^\[{re.escape(section)}\]\s*$", content, re.MULTILINE) is not None


def array_section_exists(content: str, section: str) -> bool:
    return re.search(rf"^\[\[{re.escape(section)}\]\]\s*$", content, re.MULTILINE) is not None


def key_exists(content: str, section: str, key: str) -> bool:
    lines = content.splitlines()
    in_section = False
    section_header = f"[{section}]"

    for line in lines:
        stripped = line.strip()
        if stripped == section_header:
            in_section = True
            continue
        if in_section and stripped.startswith("["):
            return False
        if in_section and re.match(rf"^{re.escape(key)}\s*=", stripped):
            return True

    return False


def append_if_missing(content: str, chunk: str) -> str:
    if content and not content.endswith("\n"):
        content += "\n"
    if content.strip():
        content += "\n"
    return content + chunk.rstrip() + "\n"


def uncomment_files_placeholder(content: str) -> str | None:
    updated = re.sub(
        r'''(?m)^# \[\[files\]\]\n# path = "README\.md"\n# description = "Project overview and setup instructions"''',
        '[[files]]\npath = "README.md"\ndescription = "Project overview and setup instructions"',
        content,
        count=1,
    )
    if updated == content:
        return None
    return updated


def insert_after_section(content: str, section: str, chunk: str) -> str:
    lines = content.splitlines()
    section_header = f"[{section}]"

    for index, current in enumerate(lines):
        if current.strip() != section_header:
            continue

        insert_at = index + 1
        while insert_at < len(lines) and not lines[insert_at].strip().startswith("["):
            insert_at += 1
        while insert_at > index + 1 and lines[insert_at - 1].strip() == "":
            insert_at -= 1
        if insert_at < len(lines) and lines[insert_at].strip() != "":
            chunk = chunk.rstrip() + "\n"
        lines[insert_at:insert_at] = ["", *chunk.rstrip().splitlines()]
        return "\n".join(lines).rstrip() + "\n"

    return append_if_missing(content, chunk)


def insert_key(content: str, section: str, line: str) -> str:
    lines = content.splitlines()
    section_header = f"[{section}]"

    for index, current in enumerate(lines):
        if current.strip() != section_header:
            continue

        insert_at = index + 1
        while insert_at < len(lines) and not lines[insert_at].strip().startswith("["):
            insert_at += 1
        lines.insert(insert_at, line)
        return "\n".join(lines) + "\n"

    return append_if_missing(content, f"{section_header}\n{line}")


def upsert_config(path: Path, project_name: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(default_config(project_name))
        return

    content = path.read_text()

    if not section_exists(content, "project"):
        content = append_if_missing(
            content,
            f'''[project]
name = "{project_name}"
description = """
Add your project description here.
"""''',
        )
    else:
        if not key_exists(content, "project", "name"):
            content = insert_key(content, "project", f'name = "{project_name}"')
        if not key_exists(content, "project", "description"):
            content = insert_key(
                content,
                "project",
                'description = """\nAdd your project description here.\n"""',
            )

    if not array_section_exists(content, "files"):
        uncommented = uncomment_files_placeholder(content)
        content = uncommented or insert_after_section(
            content,
            "project",
            '''[[files]]
path = "README.md"
description = "Project overview and setup instructions"''',
        )

    if not section_exists(content, "worktree"):
        content = append_if_missing(
            content,
            '''[worktree]
symlink_paths = [".agent_core/docs/data", ".claude"]''',
        )
    elif not key_exists(content, "worktree", "symlink_paths"):
        content = insert_key(
            content,
            "worktree",
            'symlink_paths = [".agent_core/docs/data", ".claude"]',
        )

    if not section_exists(content, "branches"):
        content = append_if_missing(
            content,
            '''[branches]
dev = "dev"
main = "main"
test = "test"
# [branches.noswitch_branches]
# company_xyz = "main"''',
        )
    else:
        if not key_exists(content, "branches", "dev"):
            content = insert_key(content, "branches", 'dev = "dev"')
        if not key_exists(content, "branches", "main"):
            content = insert_key(content, "branches", 'main = "main"')
        if not key_exists(content, "branches", "test"):
            content = insert_key(content, "branches", 'test = "test"')

    path.write_text(content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("project_name")
    args = parser.parse_args()
    upsert_config(Path(args.path), args.project_name)


if __name__ == "__main__":
    main()
