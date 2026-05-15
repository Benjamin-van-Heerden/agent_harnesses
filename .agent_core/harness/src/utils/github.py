import os
import re

from github import Auth, Github, GithubException

from src.utils.errors import GitHubError
from src.utils.git import run_git


SPEC_LABEL = "spec"
TODO_LABEL = "todo"

STATUS_LABELS = {
    "todo": "status:todo",
    "merge_ready": "status:merge-ready",
    "completed": "status:completed",
    "abandoned": "status:abandoned",
    "open": "status:todo",
    "claimed": "status:completed",
}


def get_token() -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubError(
            "GITHUB_TOKEN is not set.\n"
            "Create a GitHub token with repo and read:user scopes, then run:\n"
            "  export GITHUB_TOKEN='your_token_here'"
        )
    return token


def get_client() -> Github:
    try:
        client = Github(auth=Auth.Token(get_token()))
        client.get_user().login
        return client
    except GithubException as error:
        raise GitHubError(f"GitHub authentication failed: {error}") from error


def authenticated_username() -> str:
    try:
        return get_client().get_user().login
    except GithubException as error:
        raise GitHubError(f"Could not read GitHub user: {error}") from error


def parse_repo_url(url: str) -> tuple[str, str] | None:
    patterns = [
        r"https://(?:[^@]+@)?github\.com/([^/]+)/([^/.]+)(?:\.git)?",
        r"git@github\.com:([^/]+)/([^/.]+)(?:\.git)?",
    ]
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            return match.group(1), match.group(2)
    return None


def repo_name() -> str:
    result = run_git(["remote", "get-url", "origin"], check=False)
    url = result.stdout.strip()
    parsed = parse_repo_url(url)
    if parsed is None:
        raise GitHubError(f"Origin remote is not a GitHub repository: {url}")
    return f"{parsed[0]}/{parsed[1]}"


def repository():
    try:
        return get_client().get_repo(repo_name())
    except GithubException as error:
        raise GitHubError(f"Could not open GitHub repository: {error}") from error


def ensure_label(repo, name: str, color: str, description: str) -> None:
    try:
        repo.get_label(name)
    except GithubException as error:
        if error.status != 404:
            raise GitHubError(f"Could not read label '{name}': {error}") from error
        try:
            repo.create_label(name, color, description)
        except GithubException as create_error:
            raise GitHubError(f"Could not create label '{name}': {create_error}") from create_error


def ensure_labels(repo) -> None:
    ensure_label(repo, SPEC_LABEL, "8B5CF6", "Specification")
    ensure_label(repo, TODO_LABEL, "22C55E", "Standalone todo")
    ensure_label(repo, STATUS_LABELS["todo"], "6B7280", "Not completed")
    ensure_label(repo, STATUS_LABELS["merge_ready"], "8B5CF6", "Ready to merge")
    ensure_label(repo, STATUS_LABELS["completed"], "3B82F6", "Completed")
    ensure_label(repo, STATUS_LABELS["abandoned"], "DC2626", "Abandoned")


def status_label(status: str) -> str | None:
    return STATUS_LABELS.get(status)


def status_from_labels(labels: list[str], kind: str) -> str | None:
    allowed = ["todo", "merge_ready", "completed", "abandoned"]
    if kind == "todo":
        allowed = ["open", "claimed"]
    reverse = {STATUS_LABELS[key]: key for key in allowed}
    for label in labels:
        status = reverse.get(label)
        if status is not None:
            return status
    return None


def issue_labels(kind: str, status: str) -> list[str]:
    base = SPEC_LABEL if kind == "spec" else TODO_LABEL
    labels = [base]
    label = status_label(status)
    if label is not None:
        labels.append(label)
    return labels


def list_issues(repo, label: str | None = None, state: str = "open") -> list:
    try:
        issues = repo.get_issues(state=state, labels=[label] if label else None)
        return [issue for issue in issues if issue.pull_request is None]
    except GithubException as error:
        raise GitHubError(f"Could not list issues: {error}") from error


def create_issue(repo, title: str, body: str, labels: list[str], assignees: list[str] | None = None):
    try:
        return repo.create_issue(
            title=title,
            body=body,
            labels=labels,
            assignees=assignees or [],
        )
    except GithubException as error:
        raise GitHubError(f"Could not create issue: {error}") from error


def update_issue(repo, issue_id: int, **kwargs):
    try:
        issue = repo.get_issue(issue_id)
        issue.edit(**kwargs)
        return issue
    except GithubException as error:
        raise GitHubError(f"Could not update issue #{issue_id}: {error}") from error


def create_pull_request(repo, title: str, body: str, head: str, base: str):
    try:
        return repo.create_pull(title=title, body=body, head=head, base=base)
    except GithubException as error:
        raise GitHubError(f"Could not create pull request: {error}") from error


def merge_pull_request(repo, number: int, commit_message: str):
    try:
        pull_request = repo.get_pull(number)
        return pull_request.merge(commit_message=commit_message, merge_method="squash")
    except GithubException as error:
        raise GitHubError(f"Could not merge pull request #{number}: {error}") from error


def delete_remote_branch(repo, branch: str) -> None:
    try:
        ref = repo.get_git_ref(f"heads/{branch}")
        ref.delete()
    except GithubException as error:
        if error.status != 404:
            raise GitHubError(f"Could not delete remote branch '{branch}': {error}") from error


def parse_pull_number(url: str) -> int | None:
    match = re.search(r"/pull/(\d+)", url or "")
    if match is None:
        return None
    return int(match.group(1))
