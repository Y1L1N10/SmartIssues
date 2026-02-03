"""SmartIssues - AI-driven GitHub Issues analysis tool."""

__version__ = "0.1.0"
__author__ = "SmartIssues Team"

from .config import Config
from .github_client import GitHubClient
from .processor import IssueProcessor
from .formatter import ReportFormatter
from .cache import CacheManager

__all__ = [
    "Config",
    "GitHubClient",
    "IssueProcessor",
    "ReportFormatter",
    "CacheManager",
]
