"""GitHub API client for fetching issues."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from github import Github, GithubException
from github.Issue import Issue as GithubIssue
from github.Repository import Repository


@dataclass
class Comment:
    """Issue comment data structure."""

    id: int
    author: str
    body: str
    created_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "author": self.author,
            "body": self.body,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Issue:
    """Simplified issue data structure."""

    number: int
    title: str
    body: str
    state: str
    created_at: datetime
    updated_at: datetime
    author: str
    labels: list[str]
    comments_count: int
    url: str
    assignees: list[str] = field(default_factory=list)
    milestone: Optional[str] = None
    reactions_count: int = 0
    comments: list[Comment] = field(default_factory=list)

    @classmethod
    def from_github_issue(
        cls, issue: GithubIssue, include_comments: bool = False
    ) -> "Issue":
        """Create Issue from PyGithub Issue object."""
        comments_list = []
        if include_comments and issue.comments > 0:
            for comment in issue.get_comments():
                comments_list.append(
                    Comment(
                        id=comment.id,
                        author=comment.user.login if comment.user else "unknown",
                        body=comment.body or "",
                        created_at=comment.created_at,
                    )
                )

        return cls(
            number=issue.number,
            title=issue.title,
            body=issue.body or "",
            state=issue.state,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            author=issue.user.login if issue.user else "unknown",
            labels=[label.name for label in issue.labels],
            comments_count=issue.comments,
            url=issue.html_url,
            assignees=[a.login for a in issue.assignees] if issue.assignees else [],
            milestone=issue.milestone.title if issue.milestone else None,
            reactions_count=issue.reactions.get("total_count", 0)
            if hasattr(issue, "reactions") and issue.reactions
            else 0,
            comments=comments_list,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "author": self.author,
            "labels": self.labels,
            "comments_count": self.comments_count,
            "url": self.url,
            "assignees": self.assignees,
            "milestone": self.milestone,
            "reactions_count": self.reactions_count,
            "comments": [c.to_dict() for c in self.comments],
        }

    @property
    def age_days(self) -> int:
        """Calculate issue age in days."""
        return (datetime.now() - self.created_at.replace(tzinfo=None)).days

    @property
    def is_stale(self) -> bool:
        """Check if issue hasn't been updated in 30+ days."""
        return (datetime.now() - self.updated_at.replace(tzinfo=None)).days > 30


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, token: str):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token
        """
        self.client = Github(token)
        self._token = token

    def get_repository(self, repo_name: str) -> Repository:
        """Get repository by full name (owner/repo).

        Args:
            repo_name: Full repository name (e.g., 'owner/repo')

        Returns:
            Repository object

        Raises:
            GithubException: If repository not found or access denied
        """
        return self.client.get_repo(repo_name)

    def fetch_issues(
        self,
        repo_name: str,
        state: str = "open",
        labels: Optional[list[str]] = None,
        max_count: int = 30,
        include_comments: bool = False,
        sort: str = "created",
        direction: str = "desc",
    ) -> list[Issue]:
        """Fetch issues from a repository.

        Args:
            repo_name: Full repository name (e.g., 'owner/repo')
            state: Issue state filter ('open', 'closed', 'all')
            labels: Optional list of label names to filter by
            max_count: Maximum number of issues to fetch
            include_comments: Whether to fetch issue comments
            sort: Sort field ('created', 'updated', 'comments')
            direction: Sort direction ('asc', 'desc')

        Returns:
            List of Issue objects
        """
        repo = self.get_repository(repo_name)

        # Build query parameters
        kwargs = {"state": state, "sort": sort, "direction": direction}
        if labels:
            kwargs["labels"] = labels

        # Fetch issues
        issues_iter = repo.get_issues(**kwargs)

        result = []
        for i, issue in enumerate(issues_iter):
            if i >= max_count:
                break
            # Skip pull requests (they appear in issues API)
            if issue.pull_request is None:
                result.append(
                    Issue.from_github_issue(issue, include_comments=include_comments)
                )

        return result

    def fetch_issues_batch(
        self,
        repo_names: list[str],
        state: str = "open",
        max_per_repo: int = 30,
    ) -> dict[str, list[Issue]]:
        """Fetch issues from multiple repositories.

        Args:
            repo_names: List of repository names
            state: Issue state filter
            max_per_repo: Maximum issues per repository

        Returns:
            Dictionary mapping repo names to issue lists
        """
        results = {}
        for repo_name in repo_names:
            try:
                results[repo_name] = self.fetch_issues(
                    repo_name, state=state, max_count=max_per_repo
                )
            except GithubException as e:
                results[repo_name] = []
        return results

    def fetch_issue(self, repo_name: str, issue_number: int) -> Issue:
        """Fetch a single issue by number.

        Args:
            repo_name: Full repository name
            issue_number: Issue number

        Returns:
            Issue object
        """
        repo = self.get_repository(repo_name)
        github_issue = repo.get_issue(issue_number)
        return Issue.from_github_issue(github_issue)

    def test_connection(self) -> bool:
        """Test if the GitHub connection is working.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            user = self.client.get_user()
            _ = user.login  # Force API call
            return True
        except GithubException:
            return False

    def get_rate_limit_info(self) -> dict:
        """Get current rate limit information.

        Returns:
            Dictionary with rate limit details
        """
        try:
            rate_limit = self.client.get_rate_limit()
            # Handle different PyGithub versions/structures
            if hasattr(rate_limit, "core"):
                core = rate_limit.core
            elif hasattr(rate_limit, "resources") and hasattr(rate_limit.resources, "core"):
                core = rate_limit.resources.core
            else:
                # Fallback to a basic check or return empty info
                return {"limit": "unknown", "remaining": "unknown", "reset_at": "unknown"}

            return {
                "limit": core.limit,
                "remaining": core.remaining,
                "reset_at": core.reset.isoformat() if hasattr(core.reset, "isoformat") else str(core.reset),
            }
        except Exception:
            return {"limit": "err", "remaining": "err", "reset_at": "err"}
