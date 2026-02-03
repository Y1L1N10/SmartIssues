"""Output formatting for reports and todos."""

from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .github_client import Issue
from .processor import AnalysisResult, BatchAnalysisSummary


class ReportFormatter:
    """Format analysis results into various output formats."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize formatter.

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"

        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def format_report(
        self,
        repo_name: str,
        issues: list[Issue],
        results: list[AnalysisResult],
        summary: Union[dict, BatchAnalysisSummary],
    ) -> str:
        """Format a full analysis report.

        Args:
            repo_name: Repository name
            issues: List of analyzed issues
            results: Analysis results
            summary: Summary statistics

        Returns:
            Formatted markdown report
        """
        template = self.env.get_template("report.md.jinja2")

        # Create issue-result mapping
        issue_map = {issue.number: issue for issue in issues}
        combined = []
        for result in results:
            issue = issue_map.get(result.issue_number)
            if issue:
                combined.append({"issue": issue, "analysis": result})

        # Convert BatchAnalysisSummary to dict if needed
        if isinstance(summary, BatchAnalysisSummary):
            summary_dict = summary.to_dict()
        else:
            summary_dict = summary

        return template.render(
            repo_name=repo_name,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            items=combined,
            summary=summary_dict,
        )

    def format_todo_list(
        self,
        results: list[AnalysisResult],
        issues: list[Issue],
        summary: Union[dict, BatchAnalysisSummary] = None,
    ) -> str:
        """Format analysis results as a todo list.

        Args:
            results: Analysis results
            issues: Original issues
            summary: Optional summary for recommendations

        Returns:
            Formatted markdown todo list
        """
        template = self.env.get_template("todo.md.jinja2")

        issue_map = {issue.number: issue for issue in issues}
        combined = []
        for result in results:
            issue = issue_map.get(result.issue_number)
            if issue:
                combined.append({"issue": issue, "analysis": result})

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        combined.sort(key=lambda x: priority_order.get(x["analysis"].priority.value, 4))

        # Convert BatchAnalysisSummary to dict if needed
        summary_dict = None
        if summary:
            if isinstance(summary, BatchAnalysisSummary):
                summary_dict = summary.to_dict()
            else:
                summary_dict = summary

        return template.render(
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            items=combined,
            summary=summary_dict,
        )

    def format_console_output(
        self,
        results: list[AnalysisResult],
        issues: list[Issue],
        summary: Union[dict, BatchAnalysisSummary] = None,
    ) -> str:
        """Format results for console output.

        Args:
            results: Analysis results
            issues: Original issues
            summary: Optional summary for recommendations

        Returns:
            Formatted string for console display
        """
        issue_map = {issue.number: issue for issue in issues}
        lines = []

        # Sort by priority for display
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_results = sorted(
            results, key=lambda x: priority_order.get(x.priority.value, 4)
        )

        for result in sorted_results:
            issue = issue_map.get(result.issue_number)
            if not issue:
                continue

            priority_indicator = {
                "critical": "[CRITICAL]",
                "high": "[HIGH]    ",
                "medium": "[MEDIUM]  ",
                "low": "[LOW]     ",
            }

            lines.append(
                f"{priority_indicator.get(result.priority.value, '[?]')} "
                f"#{issue.number} [{result.category.value}] {issue.title}"
            )
            lines.append(f"    Summary: {result.summary}")
            lines.append(f"    Effort: {result.estimated_effort}")
            if result.action_items:
                lines.append(f"    Actions: {', '.join(result.action_items[:2])}")
            lines.append(f"    URL: {issue.url}")
            lines.append("")

        # Add recommendations if available
        if summary:
            if isinstance(summary, BatchAnalysisSummary):
                recommendations = summary.ai_recommendations
            else:
                recommendations = summary.get("ai_recommendations", "")

            if recommendations:
                lines.append("=" * 60)
                lines.append("AI RECOMMENDATIONS")
                lines.append("=" * 60)
                lines.append(recommendations)
                lines.append("")

        return "\n".join(lines)

    def format_json_output(
        self,
        results: list[AnalysisResult],
        issues: list[Issue],
        summary: Union[dict, BatchAnalysisSummary] = None,
    ) -> dict:
        """Format results as JSON-serializable dict.

        Args:
            results: Analysis results
            issues: Original issues
            summary: Optional summary

        Returns:
            Dictionary ready for JSON serialization
        """
        issue_map = {issue.number: issue for issue in issues}

        items = []
        for result in results:
            issue = issue_map.get(result.issue_number)
            if issue:
                items.append({
                    "issue": issue.to_dict(),
                    "analysis": result.to_dict(),
                })

        output = {
            "generated_at": datetime.now().isoformat(),
            "total_issues": len(results),
            "items": items,
        }

        if summary:
            if isinstance(summary, BatchAnalysisSummary):
                output["summary"] = summary.to_dict()
            else:
                output["summary"] = summary

        return output

    def save_report(self, content: str, output_path: Path) -> Path:
        """Save report content to file.

        Args:
            content: Report content
            output_path: Output file path

        Returns:
            Path to saved file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return output_path
