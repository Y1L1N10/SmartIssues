"""Claude AI processor for analyzing GitHub issues."""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import anthropic

from .github_client import Issue


class Priority(Enum):
    """Issue priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(Enum):
    """Issue category types."""

    BUG = "bug"
    FEATURE = "feature"
    ENHANCEMENT = "enhancement"
    DOCUMENTATION = "documentation"
    QUESTION = "question"
    MAINTENANCE = "maintenance"
    SECURITY = "security"
    OTHER = "other"


@dataclass
class AnalysisResult:
    """Result of AI analysis on an issue."""

    issue_number: int
    category: Category
    priority: Priority
    summary: str
    suggested_labels: list[str]
    estimated_effort: str
    key_points: list[str]
    related_topics: list[str]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "issue_number": self.issue_number,
            "category": self.category.value,
            "priority": self.priority.value,
            "summary": self.summary,
            "suggested_labels": self.suggested_labels,
            "estimated_effort": self.estimated_effort,
            "key_points": self.key_points,
            "related_topics": self.related_topics,
        }


class IssueProcessor:
    """Process GitHub issues using Claude AI."""

    SYSTEM_PROMPT = """You are an expert software development analyst. Your task is to analyze GitHub issues and provide structured insights.

For each issue, you should:
1. Categorize it (bug, feature, enhancement, documentation, question, maintenance, security, other)
2. Assess priority (critical, high, medium, low)
3. Provide a concise summary (2-3 sentences)
4. Suggest appropriate labels
5. Estimate effort level (trivial, small, medium, large, extra-large)
6. Extract key points
7. Identify related topics/areas

Always respond with valid JSON in the exact format specified."""

    ANALYSIS_PROMPT_TEMPLATE = """Analyze the following GitHub issue and provide a structured analysis.

Issue #{number}: {title}

Content:
{body}

Current Labels: {labels}
Author: {author}
Created: {created_at}
Comments: {comments_count}

Respond with a JSON object in this exact format:
{{
    "category": "bug|feature|enhancement|documentation|question|maintenance|security|other",
    "priority": "critical|high|medium|low",
    "summary": "Brief 2-3 sentence summary",
    "suggested_labels": ["label1", "label2"],
    "estimated_effort": "trivial|small|medium|large|extra-large",
    "key_points": ["point1", "point2"],
    "related_topics": ["topic1", "topic2"]
}}"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """Initialize the processor.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def analyze_issue(self, issue: Issue) -> AnalysisResult:
        """Analyze a single issue using Claude.

        Args:
            issue: Issue to analyze

        Returns:
            AnalysisResult with AI analysis
        """
        prompt = self.ANALYSIS_PROMPT_TEMPLATE.format(
            number=issue.number,
            title=issue.title,
            body=issue.body[:4000] if issue.body else "No description provided",
            labels=", ".join(issue.labels) if issue.labels else "None",
            author=issue.author,
            created_at=issue.created_at.strftime("%Y-%m-%d"),
            comments_count=issue.comments_count,
        )

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse the response
        response_text = message.content[0].text
        analysis_data = self._parse_response(response_text)

        return AnalysisResult(
            issue_number=issue.number,
            category=Category(analysis_data.get("category", "other")),
            priority=Priority(analysis_data.get("priority", "medium")),
            summary=analysis_data.get("summary", ""),
            suggested_labels=analysis_data.get("suggested_labels", []),
            estimated_effort=analysis_data.get("estimated_effort", "medium"),
            key_points=analysis_data.get("key_points", []),
            related_topics=analysis_data.get("related_topics", []),
        )

    def analyze_issues(
        self, issues: list[Issue], on_progress: Optional[callable] = None
    ) -> list[AnalysisResult]:
        """Analyze multiple issues.

        Args:
            issues: List of issues to analyze
            on_progress: Optional callback for progress updates (receives current, total)

        Returns:
            List of AnalysisResult objects
        """
        results = []
        total = len(issues)

        for i, issue in enumerate(issues):
            result = self.analyze_issue(issue)
            results.append(result)

            if on_progress:
                on_progress(i + 1, total)

        return results

    def generate_batch_summary(self, results: list[AnalysisResult]) -> dict:
        """Generate a summary of multiple analysis results.

        Args:
            results: List of analysis results

        Returns:
            Summary dictionary with statistics and insights
        """
        if not results:
            return {"total": 0, "by_category": {}, "by_priority": {}}

        by_category = {}
        by_priority = {}

        for result in results:
            cat = result.category.value
            pri = result.priority.value

            by_category[cat] = by_category.get(cat, 0) + 1
            by_priority[pri] = by_priority.get(pri, 0) + 1

        # Find high priority items
        high_priority_issues = [
            r.issue_number
            for r in results
            if r.priority in (Priority.CRITICAL, Priority.HIGH)
        ]

        return {
            "total": len(results),
            "by_category": by_category,
            "by_priority": by_priority,
            "high_priority_issues": high_priority_issues,
        }

    def _parse_response(self, response_text: str) -> dict:
        """Parse JSON response from Claude.

        Args:
            response_text: Raw response text

        Returns:
            Parsed dictionary
        """
        # Try to extract JSON from the response
        text = response_text.strip()

        # Handle markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (code block markers)
            text = "\n".join(lines[1:-1])

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Return defaults if parsing fails
            return {
                "category": "other",
                "priority": "medium",
                "summary": "Unable to parse AI response",
                "suggested_labels": [],
                "estimated_effort": "medium",
                "key_points": [],
                "related_topics": [],
            }

    def test_connection(self) -> bool:
        """Test if the Anthropic API connection is working.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}],
            )
            return len(message.content) > 0
        except anthropic.APIError:
            return False
