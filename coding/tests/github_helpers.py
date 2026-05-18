import os
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv
from github import Auth, Github, GithubException
from github.AuthenticatedUser import AuthenticatedUser
from github.Repository import Repository

from constants import TEST_REPOSITORY_NAME
from helpers import configure_git, install_harness, run_command


def token_or_skip() -> str:
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token
    warning = (
        "WARNING: GITHUB_TOKEN is not set. Skipping harness GitHub integration "
        f"tests for disposable repository '{TEST_REPOSITORY_NAME}'."
    )
    print(f"\n{warning}\n")
    pytest.skip(warning)


def client_for_token(token: str) -> Github:
    client = Github(auth=Auth.Token(token))
    client.get_user().login
    return client


def clear_repository(client: Github) -> Repository:
    user = client.get_user()
    full_name = f"{user.login}/{TEST_REPOSITORY_NAME}"
    try:
        client.get_repo(full_name).delete()
        time.sleep(3)
    except GithubException as error:
        if error.status != 404:
            raise

    assert isinstance(user, AuthenticatedUser)
    repo = user.create_repo(
        TEST_REPOSITORY_NAME,
        description="Disposable repository for harness integration tests",
        private=False,
        auto_init=False,
    )
    time.sleep(3)
    return repo


def authenticated_remote_url(client: Github, token: str) -> str:
    user = client.get_user()
    return f"https://oauth2:{token}@github.com/{user.login}/{TEST_REPOSITORY_NAME}.git"


def prepare_remote_project(project_path: Path, token: str, client: Github) -> Repository:
    repo = clear_repository(client)
    remote_url = authenticated_remote_url(client, token)

    project_path.mkdir()
    run_command(["git", "init", "-b", "main"], cwd=project_path)
    configure_git(project_path)
    run_command(["git", "remote", "add", "origin", remote_url], cwd=project_path)
    (project_path / "README.md").write_text("# Harness remote test\n")
    run_command(["git", "add", "."], cwd=project_path)
    run_command(["git", "commit", "-m", "initial project state"], cwd=project_path)
    run_command(["git", "push", "--set-upstream", "origin", "main"], cwd=project_path)
    run_command(["git", "checkout", "-b", "dev"], cwd=project_path)
    run_command(["git", "push", "--set-upstream", "origin", "dev"], cwd=project_path)
    run_command(["git", "checkout", "-b", "test"], cwd=project_path)
    run_command(["git", "push", "--set-upstream", "origin", "test"], cwd=project_path)
    run_command(["git", "checkout", "dev"], cwd=project_path)
    install_harness(project_path)
    run_command(["git", "add", "."], cwd=project_path)
    run_command(["git", "commit", "-m", "initial harness state"], cwd=project_path)
    run_command(["git", "push", "origin", "dev"], cwd=project_path)
    return repo


def issue_titles(repo: Repository) -> set[str]:
    return {
        issue.title
        for issue in repo.get_issues(state="all")
        if issue.pull_request is None
    }
