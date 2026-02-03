"""Tests for GitHub client module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.github_client import GitHubClient, Issue


class TestIssue:
    """Tests for Issue dataclass."""

    def test_from_github_issue(self):
        """Test creating Issue from GitHub API response."""
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test body content"
        mock_issue.state = "open"
        mock_issue.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_issue.updated_at = datetime(2024, 1, 2, 12, 0, 0)
        mock_issue.user.login = "testuser"
        mock_issue.labels = [MagicMock(name="bug"), MagicMock(name="help wanted")]
        mock_issue.comments = 5
        mock_issue.html_url = "https://github.com/owner/repo/issues/123"

        issue = Issue.from_github_issue(mock_issue)

        assert issue.number == 123
        assert issue.title == "Test Issue"
        assert issue.body == "Test body content"
        assert issue.state == "open"
        assert issue.author == "testuser"
        assert issue.comments_count == 5

    def test_to_dict(self):
        """Test Issue serialization to dictionary."""
        issue = Issue(
            number=1,
            title="Test",
            body="Body",
            state="open",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 2),
            author="user",
            labels=["bug"],
            comments_count=0,
            url="https://example.com",
        )

        data = issue.to_dict()

        assert data["number"] == 1
        assert data["title"] == "Test"
        assert data["labels"] == ["bug"]
        assert "created_at" in data


class TestGitHubClient:
    """Tests for GitHubClient."""

    @patch("src.github_client.Github")
    def test_init(self, mock_github_class):
        """Test client initialization."""
        client = GitHubClient("test_token")
        mock_github_class.assert_called_once_with("test_token")

    @patch("src.github_client.Github")
    def test_get_repository(self, mock_github_class):
        """Test getting a repository."""
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github
        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        client = GitHubClient("test_token")
        repo = client.get_repository("owner/repo")

        mock_github.get_repo.assert_called_once_with("owner/repo")
        assert repo == mock_repo

    @patch("src.github_client.Github")
    def test_test_connection_success(self, mock_github_class):
        """Test successful connection check."""
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github
        mock_user = MagicMock()
        mock_user.login = "testuser"
        mock_github.get_user.return_value = mock_user

        client = GitHubClient("test_token")
        result = client.test_connection()

        assert result is True

    @patch("src.github_client.Github")
    def test_fetch_issues(self, mock_github_class):
        """Test fetching issues from repository."""
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github
        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        # Create mock issues
        mock_issue = MagicMock()
        mock_issue.number = 1
        mock_issue.title = "Test Issue"
        mock_issue.body = "Body"
        mock_issue.state = "open"
        mock_issue.created_at = datetime(2024, 1, 1)
        mock_issue.updated_at = datetime(2024, 1, 1)
        mock_issue.user.login = "user"
        mock_issue.labels = []
        mock_issue.comments = 0
        mock_issue.html_url = "https://example.com"
        mock_issue.pull_request = None  # Not a PR

        mock_repo.get_issues.return_value = [mock_issue]

        client = GitHubClient("test_token")
        issues = client.fetch_issues("owner/repo", max_count=10)

        assert len(issues) == 1
        assert issues[0].number == 1

    @patch("src.github_client.Github")
    def test_get_rate_limit_info(self, mock_github_class):
        """Test getting rate limit information."""
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github

        mock_rate_limit = MagicMock()
        mock_rate_limit.core.limit = 5000
        mock_rate_limit.core.remaining = 4999
        mock_rate_limit.core.reset = datetime(2024, 1, 1, 13, 0, 0)
        mock_github.get_rate_limit.return_value = mock_rate_limit

        client = GitHubClient("test_token")
        info = client.get_rate_limit_info()

        assert info["limit"] == 5000
        assert info["remaining"] == 4999
        assert "reset_at" in info
