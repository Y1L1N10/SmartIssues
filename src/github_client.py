"""GitHub API client for fetching issues."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from github import Github, GithubException
from github.Issue import Issue as GithubIssue
from github.Repository import Repository


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

    @classmethod
    def from_github_issue(cls, issue: GithubIssue) -> "Issue":
        """Create Issue from PyGithub Issue object."""
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
        }


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
    ) -> list[Issue]:
        """Fetch issues from a repository.

        Args:
            repo_name: Full repository name (e.g., 'owner/repo')
            state: Issue state filter ('open', 'closed', 'all')
            labels: Optional list of label names to filter by
            max_count: Maximum number of issues to fetch

        Returns:
            List of Issue objects
        """
        repo = self.get_repository(repo_name)

        # Build query parameters
        kwargs = {"state": state}
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
                result.append(Issue.from_github_issue(issue))

        return result

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
        rate_limit = self.client.get_rate_limit()
        core = rate_limit.core
        return {
            "limit": core.limit,
            "remaining": core.remaining,
            "reset_at": core.reset.isoformat(),
        }
