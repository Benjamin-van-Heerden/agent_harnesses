HEADING_WIDTH = 80
SUBSECTION_WIDTH = 70
FILE_WIDTH = 50


def heading(title: str) -> list[str]:
    return ["=" * HEADING_WIDTH, title, "=" * HEADING_WIDTH, ""]


def subsection(title: str) -> list[str]:
    return ["-" * SUBSECTION_WIDTH, title, "-" * SUBSECTION_WIDTH, ""]


def file(title: str) -> list[str]:
    return ["#" * FILE_WIDTH, f"# {title}", "#" * FILE_WIDTH, ""]
