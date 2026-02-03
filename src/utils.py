"""Utility functions for SmartIssues."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def generate_cache_key(repo_name: str, **kwargs) -> str:
    """Generate a cache key from repository name and parameters.

    Args:
        repo_name: Repository full name
        **kwargs: Additional parameters to include in key

    Returns:
        SHA256 hash string
    """
    data = {"repo": repo_name, **kwargs}
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]


def parse_repo_name(repo_input: str) -> tuple[str, str]:
    """Parse repository input into owner and repo name.

    Args:
        repo_input: Repository in format 'owner/repo' or full URL

    Returns:
        Tuple of (owner, repo_name)

    Raises:
        ValueError: If format is invalid
    """
    # Handle GitHub URLs
    if "github.com" in repo_input:
        parts = repo_input.rstrip("/").split("/")
        if len(parts) >= 2:
            return parts[-2], parts[-1].replace(".git", "")

    # Handle owner/repo format
    if "/" in repo_input:
        parts = repo_input.split("/")
        if len(parts) == 2:
            return parts[0], parts[1]

    raise ValueError(
        f"Invalid repository format: {repo_input}. Use 'owner/repo' format."
    )


def format_datetime(dt: datetime) -> str:
    """Format datetime for display.

    Args:
        dt: Datetime object

    Returns:
        Formatted string
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, create if needed.

    Args:
        path: Directory path

    Returns:
        The path (for chaining)
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(name: str) -> str:
    """Convert string to safe filename.

    Args:
        name: Original name

    Returns:
        Safe filename string
    """
    # Replace problematic characters
    unsafe_chars = '<>:"/\\|?*'
    result = name
    for char in unsafe_chars:
        result = result.replace(char, "_")
    return result[:200]  # Limit length


def load_json_file(path: Path) -> dict[str, Any]:
    """Load JSON from file.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(data: dict[str, Any], path: Path) -> Path:
    """Save data to JSON file.

    Args:
        data: Data to save
        path: Output path

    Returns:
        Path to saved file
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    return path
