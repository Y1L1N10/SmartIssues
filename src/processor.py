"""Claude AI processor for analyzing GitHub issues."""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Literal

import anthropic
from openai import OpenAI

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
    issue_title: str
    issue_url: str
    category: Category
    priority: Priority
    summary: str
    suggested_labels: list[str]
    estimated_effort: str
    key_points: list[str]
    related_topics: list[str]
    action_items: list[str] = None
    blockers: list[str] = None

    def __post_init__(self):
        if self.action_items is None:
            self.action_items = []
        if self.blockers is None:
            self.blockers = []

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "issue_number": self.issue_number,
            "issue_title": self.issue_title,
            "issue_url": self.issue_url,
            "category": self.category.value,
            "priority": self.priority.value,
            "summary": self.summary,
            "suggested_labels": self.suggested_labels,
            "estimated_effort": self.estimated_effort,
            "key_points": self.key_points,
            "related_topics": self.related_topics,
            "action_items": self.action_items,
            "blockers": self.blockers,
        }


@dataclass
class BatchAnalysisSummary:
    """Summary of batch analysis results."""

    total_issues: int
    by_category: dict
    by_priority: dict
    by_effort: dict
    high_priority_issues: list[int]
    stale_issues: list[int]
    quick_wins: list[int]  # Low effort + high value
    ai_recommendations: str

    def to_dict(self) -> dict:
        return {
            "total_issues": self.total_issues,
            "by_category": self.by_category,
            "by_priority": self.by_priority,
            "by_effort": self.by_effort,
            "high_priority_issues": self.high_priority_issues,
            "stale_issues": self.stale_issues,
            "quick_wins": self.quick_wins,
            "ai_recommendations": self.ai_recommendations,
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

Metadata:
- Current Labels: {labels}
- Author: {author}
- Created: {created_at}
- Age: {age_days} days
- Comments: {comments_count}
- Assignees: {assignees}
- Milestone: {milestone}
{comments_section}

Respond with a JSON object in this exact format:
{{
    "category": "bug|feature|enhancement|documentation|question|maintenance|security|other",
    "priority": "critical|high|medium|low",
    "summary": "Brief 2-3 sentence summary",
    "suggested_labels": ["label1", "label2"],
    "estimated_effort": "trivial|small|medium|large|extra-large",
    "key_points": ["point1", "point2"],
    "related_topics": ["topic1", "topic2"],
    "action_items": ["specific action 1", "specific action 2"],
    "blockers": ["blocker if any"]
}}"""

    BATCH_SUMMARY_PROMPT = """Based on the analysis of {count} GitHub issues, provide strategic recommendations.

Issue Statistics:
- By Category: {by_category}
- By Priority: {by_priority}
- By Effort: {by_effort}
- High Priority Issues: {high_priority}
- Stale Issues (30+ days): {stale_count}

Provide a concise summary (3-5 sentences) with:
1. Overall project health assessment
2. Top priorities to address
3. Quick wins (low effort, high impact)
4. Suggested workflow improvements

Respond in plain text, not JSON."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        provider: Literal["anthropic", "openrouter"] = "anthropic",
        debug: bool = False,
    ):
        """Initialize the processor.

        Args:
            api_key: API key (Anthropic or OpenRouter)
            model: Model to use
            provider: API provider ("anthropic" or "openrouter")
            debug: Enable debug logging
        """
        self.provider = provider
        self.model = model
        self.debug = debug

        if provider == "openrouter":
            self.openai_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/Y1L1N10/SmartIssues",
                    "X-Title": "SmartIssues",
                }
            )
            self.anthropic_client = None
        else:
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
            self.openai_client = None

    def analyze_issue(self, issue: Issue) -> AnalysisResult:
        """Analyze a single issue using Claude.

        Args:
            issue: Issue to analyze

        Returns:
            AnalysisResult with AI analysis
        """
        # Build comments section if available
        comments_section = ""
        if hasattr(issue, "comments") and issue.comments:
            comments_text = "\n".join(
                [f"  - {c.author}: {c.body[:200]}..." for c in issue.comments[:5]]
            )
            comments_section = f"\nRecent Comments:\n{comments_text}"

        prompt = self.ANALYSIS_PROMPT_TEMPLATE.format(
            number=issue.number,
            title=issue.title,
            body=issue.body[:4000] if issue.body else "No description provided",
            labels=", ".join(issue.labels) if issue.labels else "None",
            author=issue.author,
            created_at=issue.created_at.strftime("%Y-%m-%d"),
            age_days=issue.age_days if hasattr(issue, "age_days") else "N/A",
            comments_count=issue.comments_count,
            assignees=", ".join(issue.assignees) if hasattr(issue, "assignees") and issue.assignees else "None",
            milestone=issue.milestone if hasattr(issue, "milestone") and issue.milestone else "None",
            comments_section=comments_section,
        )

        response_text = self._call_api(prompt)
        analysis_data = self._parse_response(response_text)

        return AnalysisResult(
            issue_number=issue.number,
            issue_title=issue.title,
            issue_url=issue.url,
            category=Category(analysis_data.get("category", "other")),
            priority=Priority(analysis_data.get("priority", "medium")),
            summary=analysis_data.get("summary", ""),
            suggested_labels=analysis_data.get("suggested_labels", []),
            estimated_effort=analysis_data.get("estimated_effort", "medium"),
            key_points=analysis_data.get("key_points", []),
            related_topics=analysis_data.get("related_topics", []),
            action_items=analysis_data.get("action_items", []),
            blockers=analysis_data.get("blockers", []),
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

    def generate_batch_summary(
        self, results: list[AnalysisResult], issues: list[Issue] = None
    ) -> BatchAnalysisSummary:
        """Generate a comprehensive summary of multiple analysis results.

        Args:
            results: List of analysis results
            issues: Original issues (for stale detection)

        Returns:
            BatchAnalysisSummary with statistics and AI recommendations
        """
        if not results:
            return BatchAnalysisSummary(
                total_issues=0,
                by_category={},
                by_priority={},
                by_effort={},
                high_priority_issues=[],
                stale_issues=[],
                quick_wins=[],
                ai_recommendations="No issues to analyze.",
            )

        by_category = {}
        by_priority = {}
        by_effort = {}

        for result in results:
            cat = result.category.value
            pri = result.priority.value
            effort = result.estimated_effort

            by_category[cat] = by_category.get(cat, 0) + 1
            by_priority[pri] = by_priority.get(pri, 0) + 1
            by_effort[effort] = by_effort.get(effort, 0) + 1

        # Find high priority items
        high_priority_issues = [
            r.issue_number
            for r in results
            if r.priority in (Priority.CRITICAL, Priority.HIGH)
        ]

        # Find stale issues
        stale_issues = []
        if issues:
            for issue in issues:
                if hasattr(issue, "is_stale") and issue.is_stale:
                    stale_issues.append(issue.number)

        # Find quick wins (small/trivial effort + high/critical priority)
        quick_wins = [
            r.issue_number
            for r in results
            if r.estimated_effort in ("trivial", "small")
            and r.priority in (Priority.CRITICAL, Priority.HIGH)
        ]

        # Generate AI recommendations
        ai_recommendations = self._generate_recommendations(
            len(results), by_category, by_priority, by_effort,
            high_priority_issues, len(stale_issues)
        )

        return BatchAnalysisSummary(
            total_issues=len(results),
            by_category=by_category,
            by_priority=by_priority,
            by_effort=by_effort,
            high_priority_issues=high_priority_issues,
            stale_issues=stale_issues,
            quick_wins=quick_wins,
            ai_recommendations=ai_recommendations,
        )

    def _generate_recommendations(
        self,
        count: int,
        by_category: dict,
        by_priority: dict,
        by_effort: dict,
        high_priority: list,
        stale_count: int,
    ) -> str:
        """Generate AI-powered recommendations for the issue set."""
        prompt = self.BATCH_SUMMARY_PROMPT.format(
            count=count,
            by_category=json.dumps(by_category),
            by_priority=json.dumps(by_priority),
            by_effort=json.dumps(by_effort),
            high_priority=len(high_priority),
            stale_count=stale_count,
        )

        try:
            return self._call_api(prompt, max_tokens=500)
        except Exception:
            return "Unable to generate AI recommendations."

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

    def _call_api(self, prompt: str, max_tokens: int = 1024) -> str:
        """Call the appropriate API based on provider.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            Response text from the API
        """
        if self.provider == "openrouter":
            message = self.openai_client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            return message.choices[0].message.content
        else:
            message = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text

    def test_connection(self) -> bool:
        """Test if the API connection is working.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.provider == "openrouter":
                message = self.openai_client.chat.completions.create(
                    model=self.model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hello"}],
                )
                return len(message.choices) > 0
            else:
                message = self.anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hello"}],
                )
                return len(message.content) > 0
        except Exception as e:
            if hasattr(self, "debug") and self.debug:
                print(f"DEBUG: API connection test failed: {e}")
            return False
