from dataclasses import dataclass
from pathlib import Path

from src.utils import git
from src.utils.errors import GitError


@dataclass(frozen=True)
class DivergenceReport:
    source_ref: str
    destination_ref: str
    destination_only: list[str]
    source_only: list[str]
    destination_tip_is_merge: bool
    destination_only_are_merges: bool


@dataclass(frozen=True)
class ReunifyResult:
    performed: bool
    reunify_branch: str
    destination_ref: str
    tip: str
    message: str


def inspect_divergence(
    source_ref: str,
    destination_ref: str,
    cwd: Path | None = None,
) -> DivergenceReport:
    destination_only = git.commit_onelines(destination_ref, source_ref, cwd=cwd)
    source_only = git.commit_onelines(source_ref, destination_ref, cwd=cwd)
    destination_shas = git.commits_reachable_from(destination_ref, source_ref, cwd=cwd)
    destination_only_are_merges = bool(destination_shas) and all(
        git.is_merge_commit(sha, cwd=cwd) for sha in destination_shas
    )
    return DivergenceReport(
        source_ref=source_ref,
        destination_ref=destination_ref,
        destination_only=destination_only,
        source_only=source_only,
        destination_tip_is_merge=git.is_merge_commit(destination_ref, cwd=cwd),
        destination_only_are_merges=destination_only_are_merges,
    )


def format_divergence_report(report: DivergenceReport) -> str:
    lines = [
        f"Fast-forward is impossible: '{report.destination_ref}' is not an ancestor of '{report.source_ref}'.",
        "",
        f"Commits on {report.destination_ref} not in {report.source_ref}:",
    ]
    if report.destination_only:
        lines.extend(f"  - {line}" for line in report.destination_only)
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append(f"Commits on {report.source_ref} not in {report.destination_ref}:")
    if report.source_only:
        lines.extend(f"  - {line}" for line in report.source_only)
    else:
        lines.append("  (none)")
    lines.append("")
    if report.destination_tip_is_merge:
        subject = git.commit_subject(report.destination_ref)
        lines.append(f"Destination tip is a merge commit: {subject}")
    else:
        lines.append("Destination tip is not a merge commit.")
    if report.destination_only_are_merges:
        lines.append("Destination-only commits are all merge commits (safe for automatic reunify).")
    else:
        lines.append("Destination-only commits include non-merge history (automatic reunify refused).")
    lines.append("")
    lines.append(
        "Promotion history diverged, often because a promotion pull request was completed with a GitHub merge commit instead of the harness fast-forward path."
    )
    lines.append(
        "Do not complete promotion pull requests with GitHub's Merge, Squash, or Rebase buttons. Use the harness pr merge command."
    )
    return "\n".join(lines)


def _require_clean_tree(cwd: Path | None = None) -> None:
    if git.has_uncommitted_changes(cwd=cwd):
        raise GitError("Promotion reunify requires a clean working tree.")


def reunify_merge_destination_into_branch(
    reunify_branch: str,
    destination_ref: str,
    *,
    start_point: str | None = None,
    cwd: Path | None = None,
) -> ReunifyResult:
    """Merge destination_ref into reunify_branch with --no-ff, push, and restore the previous branch.

    Automatic reunify is allowed only when every commit on the destination side of the divergence is a merge commit.
    """
    _require_clean_tree(cwd)
    previous = git.current_branch(cwd=cwd)
    checkout_start = start_point or reunify_branch
    message = f"Reunify promotion history: merge {destination_ref} into {reunify_branch}"
    try:
        if start_point is not None or not git.local_branch_exists(reunify_branch, cwd=cwd):
            git.checkout_new_branch(reunify_branch, checkout_start, cwd=cwd)
        else:
            git.checkout(reunify_branch, cwd=cwd)

        if git.is_ancestor(destination_ref, "HEAD", cwd=cwd):
            tip = git.rev_parse("HEAD", cwd=cwd)
            return ReunifyResult(
                performed=False,
                reunify_branch=reunify_branch,
                destination_ref=destination_ref,
                tip=tip,
                message=f"No reunify needed: '{destination_ref}' is already an ancestor of '{reunify_branch}'.",
            )

        report = inspect_divergence("HEAD", destination_ref, cwd=cwd)
        if not report.destination_only_are_merges:
            raise GitError(format_divergence_report(report))

        try:
            if git.is_ancestor("HEAD", destination_ref, cwd=cwd):
                git.merge_ff_only(destination_ref, cwd=cwd)
                action = "fast-forwarding"
            else:
                git.merge_no_ff(destination_ref, message, cwd=cwd)
                action = "merging"
        except GitError as error:
            git.merge_abort(cwd=cwd)
            details = format_divergence_report(report)
            raise GitError(
                f"Promotion reunify merge failed.\n{details}\n\nGit reported: {error}"
            ) from error

        tip = git.rev_parse("HEAD", cwd=cwd)
        git.push(reunify_branch, cwd=cwd)
        return ReunifyResult(
            performed=True,
            reunify_branch=reunify_branch,
            destination_ref=destination_ref,
            tip=tip,
            message=(
                f"Reunified promotion history by {action} '{destination_ref}' into '{reunify_branch}' "
                f"({tip[:12]}). Fast-forward promotion can proceed."
            ),
        )
    finally:
        if previous is not None and git.current_branch(cwd=cwd) != previous:
            try:
                git.checkout(previous, cwd=cwd)
            except GitError:
                pass


def ensure_destination_is_ancestor(
    source_ref: str,
    destination_ref: str,
    reunify_branch: str,
    *,
    start_point: str | None = None,
    cwd: Path | None = None,
) -> ReunifyResult | None:
    """Return a reunify result when reunify ran; None when ancestry already holds.

    Raises GitError when ancestry fails and reunify cannot restore it.
    """
    git.fetch(cwd=cwd)
    if git.is_ancestor(destination_ref, source_ref, cwd=cwd):
        return None

    result = reunify_merge_destination_into_branch(
        reunify_branch,
        destination_ref,
        start_point=start_point,
        cwd=cwd,
    )
    git.fetch(cwd=cwd)

    if git.remote_branch_exists(reunify_branch, cwd=cwd):
        effective_source = f"origin/{reunify_branch}"
    else:
        effective_source = reunify_branch

    if not git.is_ancestor(destination_ref, effective_source, cwd=cwd):
        report = inspect_divergence(effective_source, destination_ref, cwd=cwd)
        raise GitError(
            "Promotion reunify completed, but the destination is still not an ancestor of the source.\n"
            + format_divergence_report(report)
        )
    return result
