"""Configuration management for SmartIssues."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    github_token: str = ""
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    api_provider: str = "anthropic"  # "anthropic" or "openrouter"
    default_repo: Optional[str] = None
    claude_model: str = "claude-3-5-sonnet-20241022"
    max_issues: int = 30
    cache_ttl: int = 3600
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    debug: bool = False

    @property
    def active_api_key(self) -> str:
        """Get the API key for the active provider."""
        if self.api_provider == "openrouter":
            return self.openrouter_api_key
        return self.anthropic_api_key

    @property
    def effective_model(self) -> str:
        """Get the model name formatted for the active provider."""
        if self.api_provider == "openrouter" and "/" not in self.claude_model:
            return f"anthropic/{self.claude_model}"
        return self.claude_model

    def __post_init__(self):
        """Convert string paths to Path objects."""
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """Load configuration from environment variables.

        Args:
            env_file: Optional path to .env file

        Returns:
            Config instance with loaded values
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        return cls(
            github_token=os.getenv("GITHUB_TOKEN", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            api_provider=os.getenv("API_PROVIDER", "anthropic").lower(),
            default_repo=os.getenv("DEFAULT_REPO"),
            claude_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
            max_issues=int(os.getenv("MAX_ISSUES", "30")),
            cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
            output_dir=Path(os.getenv("OUTPUT_DIR", "./output")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )

    def validate(self) -> list[str]:
        """Validate required configuration values.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.github_token:
            errors.append("GITHUB_TOKEN is required")

        if self.api_provider not in ("anthropic", "openrouter"):
            errors.append("API_PROVIDER must be 'anthropic' or 'openrouter'")

        if self.api_provider == "anthropic" and not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required when using anthropic provider")

        if self.api_provider == "openrouter" and not self.openrouter_api_key:
            errors.append("OPENROUTER_API_KEY is required when using openrouter provider")

        return errors

    def ensure_output_dir(self) -> Path:
        """Create output directory if it doesn't exist.

        Returns:
            Path to output directory
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir
