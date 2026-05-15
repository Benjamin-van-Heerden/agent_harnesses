import importlib.util
import shutil
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonPackage:
    import_name: str
    package_name: str


REQUIRED_PACKAGES = [
    PythonPackage(import_name="typer", package_name="typer"),
    PythonPackage(import_name="pydantic", package_name="pydantic"),
    PythonPackage(import_name="yaml", package_name="PyYAML"),
    PythonPackage(import_name="git", package_name="GitPython"),
    PythonPackage(import_name="github", package_name="PyGithub"),
    PythonPackage(import_name="dotenv", package_name="python-dotenv"),
]

REQUIRED_COMMANDS = ["git"]


def missing_python_packages() -> list[PythonPackage]:
    return [
        package
        for package in REQUIRED_PACKAGES
        if importlib.util.find_spec(package.import_name) is None
    ]


def missing_external_commands() -> list[str]:
    return [command for command in REQUIRED_COMMANDS if shutil.which(command) is None]


def require_dependencies() -> None:
    missing_packages = missing_python_packages()
    missing_commands = missing_external_commands()

    if not missing_packages and not missing_commands:
        return

    print("Missing required dependencies.", file=sys.stderr)

    if missing_packages:
        packages = " ".join(package.package_name for package in missing_packages)
        print("", file=sys.stderr)
        print("Install Python packages with:", file=sys.stderr)
        print(f"  python -m pip install {packages}", file=sys.stderr)

    if missing_commands:
        print("", file=sys.stderr)
        print("Install external commands:", file=sys.stderr)
        for command in missing_commands:
            print(f"  - {command}", file=sys.stderr)

    raise SystemExit(1)
