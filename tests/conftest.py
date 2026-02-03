"""Pytest configuration and fixtures for SmartIssues tests."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.github_client import Issue
from src.processor import AnalysisResult, Category, Priority


@pytest.fixture
def sample_issue():
    """Create a sample Issue for testing."""
    return Issue(
        number=42,
        title="Sample Test Issue",
        body="This is a test issue body with some content.",
        state="open",
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        updated_at=datetime(2024, 1, 16, 14, 45, 0),
        author="testuser",
        labels=["bug", "help wanted"],
        comments_count=3,
        url="https://github.com/owner/repo/issues/42",
    )


@pytest.fixture
def sample_issues():
    """Create a list of sample Issues for testing."""
    return [
        Issue(
            number=1,
            title="Bug: Application crashes on startup",
            body="The app crashes when I try to open it.",
            state="open",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            author="user1",
            labels=["bug"],
            comments_count=5,
            url="https://github.com/owner/repo/issues/1",
        ),
        Issue(
            number=2,
            title="Feature request: Dark mode",
            body="Please add dark mode support.",
            state="open",
            created_at=datetime(2024, 1, 2),
            updated_at=datetime(2024, 1, 2),
            author="user2",
            labels=["enhancement"],
            comments_count=10,
            url="https://github.com/owner/repo/issues/2",
        ),
        Issue(
            number=3,
            title="Documentation update needed",
            body="The README is outdated.",
            state="open",
            created_at=datetime(2024, 1, 3),
            updated_at=datetime(2024, 1, 3),
            author="user3",
            labels=["documentation"],
            comments_count=1,
            url="https://github.com/owner/repo/issues/3",
        ),
    ]


@pytest.fixture
def sample_analysis_result():
    """Create a sample AnalysisResult for testing."""
    return AnalysisResult(
        issue_number=42,
        category=Category.BUG,
        priority=Priority.HIGH,
        summary="This is a critical bug that needs immediate attention.",
        suggested_labels=["bug", "critical", "needs-triage"],
        estimated_effort="medium",
        key_points=[
            "Application crash on startup",
            "Affects all users",
            "Regression from v2.0",
        ],
        related_topics=["startup", "initialization", "error-handling"],
    )


@pytest.fixture
def sample_analysis_results(sample_issues):
    """Create sample AnalysisResults matching sample_issues."""
    return [
        AnalysisResult(
            issue_number=1,
            category=Category.BUG,
            priority=Priority.CRITICAL,
            summary="Critical crash issue.",
            suggested_labels=["bug", "critical"],
            estimated_effort="large",
            key_points=["Crashes on startup"],
            related_topics=["crash", "startup"],
        ),
        AnalysisResult(
            issue_number=2,
            category=Category.FEATURE,
            priority=Priority.MEDIUM,
            summary="Dark mode feature request.",
            suggested_labels=["enhancement", "ui"],
            estimated_effort="medium",
            key_points=["User wants dark theme"],
            related_topics=["ui", "theme"],
        ),
        AnalysisResult(
            issue_number=3,
            category=Category.DOCUMENTATION,
            priority=Priority.LOW,
            summary="Documentation needs update.",
            suggested_labels=["docs"],
            estimated_effort="small",
            key_points=["README outdated"],
            related_topics=["docs", "readme"],
        ),
    ]


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub client."""
    mock = MagicMock()
    mock.test_connection.return_value = True
    mock.get_rate_limit_info.return_value = {
        "limit": 5000,
        "remaining": 4999,
        "reset_at": "2024-01-01T12:00:00",
    }
    return mock


@pytest.fixture
def mock_processor():
    """Create a mock IssueProcessor."""
    mock = MagicMock()
    mock.test_connection.return_value = True
    return mock
