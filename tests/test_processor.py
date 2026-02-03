"""Tests for Claude AI processor module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.github_client import Issue
from src.processor import (
    AnalysisResult,
    Category,
    IssueProcessor,
    Priority,
)


class TestPriorityAndCategory:
    """Tests for Priority and Category enums."""

    def test_priority_values(self):
        """Test Priority enum values."""
        assert Priority.CRITICAL.value == "critical"
        assert Priority.HIGH.value == "high"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.LOW.value == "low"

    def test_category_values(self):
        """Test Category enum values."""
        assert Category.BUG.value == "bug"
        assert Category.FEATURE.value == "feature"
        assert Category.ENHANCEMENT.value == "enhancement"
        assert Category.DOCUMENTATION.value == "documentation"


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_to_dict(self):
        """Test AnalysisResult serialization."""
        result = AnalysisResult(
            issue_number=1,
            category=Category.BUG,
            priority=Priority.HIGH,
            summary="Test summary",
            suggested_labels=["bug", "urgent"],
            estimated_effort="medium",
            key_points=["Point 1", "Point 2"],
            related_topics=["testing"],
        )

        data = result.to_dict()

        assert data["issue_number"] == 1
        assert data["category"] == "bug"
        assert data["priority"] == "high"
        assert data["summary"] == "Test summary"
        assert data["suggested_labels"] == ["bug", "urgent"]


class TestIssueProcessor:
    """Tests for IssueProcessor."""

    @patch("src.processor.anthropic.Anthropic")
    def test_init(self, mock_anthropic_class):
        """Test processor initialization."""
        processor = IssueProcessor("test_api_key", "claude-sonnet-4-20250514")

        mock_anthropic_class.assert_called_once_with(api_key="test_api_key")
        assert processor.model == "claude-sonnet-4-20250514"

    @patch("src.processor.anthropic.Anthropic")
    def test_parse_response_valid_json(self, mock_anthropic_class):
        """Test parsing valid JSON response."""
        processor = IssueProcessor("test_key")

        response = '{"category": "bug", "priority": "high", "summary": "Test"}'
        result = processor._parse_response(response)

        assert result["category"] == "bug"
        assert result["priority"] == "high"

    @patch("src.processor.anthropic.Anthropic")
    def test_parse_response_code_block(self, mock_anthropic_class):
        """Test parsing JSON in markdown code block."""
        processor = IssueProcessor("test_key")

        response = '```json\n{"category": "feature", "priority": "medium"}\n```'
        result = processor._parse_response(response)

        assert result["category"] == "feature"

    @patch("src.processor.anthropic.Anthropic")
    def test_parse_response_invalid(self, mock_anthropic_class):
        """Test handling invalid JSON response."""
        processor = IssueProcessor("test_key")

        response = "This is not valid JSON"
        result = processor._parse_response(response)

        # Should return defaults
        assert result["category"] == "other"
        assert result["priority"] == "medium"

    @patch("src.processor.anthropic.Anthropic")
    def test_analyze_issue(self, mock_anthropic_class):
        """Test analyzing a single issue."""
        mock_anthropic = MagicMock()
        mock_anthropic_class.return_value = mock_anthropic

        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(
                text='{"category": "bug", "priority": "high", "summary": "Test", '
                '"suggested_labels": ["bug"], "estimated_effort": "small", '
                '"key_points": ["fix it"], "related_topics": ["testing"]}'
            )
        ]
        mock_anthropic.messages.create.return_value = mock_message

        processor = IssueProcessor("test_key")

        issue = Issue(
            number=1,
            title="Test Issue",
            body="Test body",
            state="open",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            author="user",
            labels=["bug"],
            comments_count=0,
            url="https://example.com",
        )

        result = processor.analyze_issue(issue)

        assert result.issue_number == 1
        assert result.category == Category.BUG
        assert result.priority == Priority.HIGH

    @patch("src.processor.anthropic.Anthropic")
    def test_generate_batch_summary(self, mock_anthropic_class):
        """Test generating summary from multiple results."""
        processor = IssueProcessor("test_key")

        results = [
            AnalysisResult(
                issue_number=1,
                category=Category.BUG,
                priority=Priority.HIGH,
                summary="",
                suggested_labels=[],
                estimated_effort="",
                key_points=[],
                related_topics=[],
            ),
            AnalysisResult(
                issue_number=2,
                category=Category.BUG,
                priority=Priority.CRITICAL,
                summary="",
                suggested_labels=[],
                estimated_effort="",
                key_points=[],
                related_topics=[],
            ),
            AnalysisResult(
                issue_number=3,
                category=Category.FEATURE,
                priority=Priority.LOW,
                summary="",
                suggested_labels=[],
                estimated_effort="",
                key_points=[],
                related_topics=[],
            ),
        ]

        summary = processor.generate_batch_summary(results)

        assert summary["total"] == 3
        assert summary["by_category"]["bug"] == 2
        assert summary["by_category"]["feature"] == 1
        assert summary["by_priority"]["high"] == 1
        assert summary["by_priority"]["critical"] == 1
        assert 1 in summary["high_priority_issues"]
        assert 2 in summary["high_priority_issues"]

    @patch("src.processor.anthropic.Anthropic")
    def test_test_connection_success(self, mock_anthropic_class):
        """Test successful API connection check."""
        mock_anthropic = MagicMock()
        mock_anthropic_class.return_value = mock_anthropic

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Hello")]
        mock_anthropic.messages.create.return_value = mock_message

        processor = IssueProcessor("test_key")
        result = processor.test_connection()

        assert result is True
