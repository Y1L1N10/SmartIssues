#!/usr/bin/env python3
"""SmartIssues CLI - AI-driven GitHub Issues analysis tool."""

import sys
from datetime import datetime
from pathlib import Path

import click

from src.cache import CacheManager
from src.config import Config
from src.formatter import ReportFormatter
from src.github_client import GitHubClient
from src.processor import IssueProcessor
from src.utils import generate_cache_key


@click.group()
@click.version_option(version="0.1.0", prog_name="SmartIssues")
@click.pass_context
def cli(ctx):
    """SmartIssues - AI-driven GitHub Issues analysis tool.

    Analyze GitHub issues using Claude AI to get intelligent categorization,
    priority assessment, and actionable summaries.
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = Config.from_env()


@cli.command()
@click.argument("repo")
@click.option(
    "--state",
    type=click.Choice(["open", "closed", "all"]),
    default="open",
    help="Filter issues by state",
)
@click.option(
    "--max-issues", "-n", type=int, default=30, help="Maximum number of issues to fetch"
)
@click.option(
    "--labels", "-l", multiple=True, help="Filter by labels (can be used multiple times)"
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output file path for the report"
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["report", "todo", "console"]),
    default="console",
    help="Output format",
)
@click.option("--no-cache", is_flag=True, help="Disable caching")
@click.pass_context
def analyze(ctx, repo, state, max_issues, labels, output, output_format, no_cache):
    """Analyze issues from a GitHub repository.

    REPO should be in the format 'owner/repo' (e.g., 'facebook/react').
    """
    config = ctx.obj["config"]

    # Validate configuration
    errors = config.validate()
    if errors:
        for error in errors:
            click.echo(click.style(f"Error: {error}", fg="red"), err=True)
        sys.exit(1)

    # Initialize components
    github_client = GitHubClient(config.github_token)
    processor = IssueProcessor(
        config.active_api_key,
        config.effective_model,
        provider=config.api_provider,
    )
    formatter = ReportFormatter()
    cache = CacheManager(default_ttl=config.cache_ttl)

    # Check cache
    cache_key = generate_cache_key(repo, state=state, labels=list(labels))
    cached_results = None if no_cache else cache.get(cache_key)

    if cached_results:
        click.echo("Using cached results...")
        issues_data = cached_results["issues"]
        results_data = cached_results["results"]

        # Reconstruct objects from cache (simplified for demo)
        click.echo(f"Found {len(issues_data)} cached issues")
    else:
        # Fetch issues
        click.echo(f"Fetching issues from {repo}...")
        try:
            issues = github_client.fetch_issues(
                repo,
                state=state,
                labels=list(labels) if labels else None,
                max_count=max_issues,
            )
        except Exception as e:
            click.echo(click.style(f"Error fetching issues: {e}", fg="red"), err=True)
            sys.exit(1)

        if not issues:
            click.echo("No issues found matching the criteria.")
            return

        click.echo(f"Found {len(issues)} issues. Analyzing with Claude AI...")

        # Analyze issues
        def progress_callback(current, total):
            click.echo(f"  Analyzing issue {current}/{total}...", nl=False)
            click.echo("\r", nl=False)

        try:
            results = processor.analyze_issues(issues, on_progress=progress_callback)
            click.echo()  # New line after progress
        except Exception as e:
            click.echo(click.style(f"Error analyzing issues: {e}", fg="red"), err=True)
            sys.exit(1)

        # Cache results
        if not no_cache:
            cache.set(
                cache_key,
                {
                    "issues": [i.to_dict() for i in issues],
                    "results": [r.to_dict() for r in results],
                },
            )

        # Generate output
        summary = processor.generate_batch_summary(results)

        if output_format == "console":
            output_text = formatter.format_console_output(results, issues)
            click.echo("\n" + output_text)

            # Print summary
            click.echo("\n--- Summary ---")
            click.echo(f"Total issues: {summary['total']}")
            click.echo(f"By priority: {summary['by_priority']}")
            click.echo(f"By category: {summary['by_category']}")

        elif output_format == "report":
            output_text = formatter.format_report(repo, issues, results, summary)
            if output:
                output_path = Path(output)
            else:
                config.ensure_output_dir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = config.output_dir / f"report_{timestamp}.md"

            formatter.save_report(output_text, output_path)
            click.echo(f"Report saved to: {output_path}")

        elif output_format == "todo":
            output_text = formatter.format_todo_list(results, issues)
            if output:
                output_path = Path(output)
            else:
                config.ensure_output_dir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = config.output_dir / f"todo_{timestamp}.md"

            formatter.save_report(output_text, output_path)
            click.echo(f"Todo list saved to: {output_path}")


@cli.command()
@click.pass_context
def check(ctx):
    """Check API connections and configuration."""
    config = ctx.obj["config"]

    click.echo("Checking configuration...")

    # Check config
    errors = config.validate()
    if errors:
        for error in errors:
            click.echo(click.style(f"  [FAIL] {error}", fg="red"))
    else:
        click.echo(click.style("  [OK] Configuration valid", fg="green"))

    # Check GitHub connection
    if config.github_token:
        click.echo("Checking GitHub connection...")
        try:
            client = GitHubClient(config.github_token)
            if client.test_connection():
                click.echo(click.style("  [OK] GitHub API connected", fg="green"))
                rate_limit = client.get_rate_limit_info()
                click.echo(f"       Rate limit: {rate_limit['remaining']}/{rate_limit['limit']}")
            else:
                click.echo(click.style("  [FAIL] GitHub API connection failed", fg="red"))
        except Exception as e:
            click.echo(click.style(f"  [FAIL] GitHub error: {e}", fg="red"))

    # Check AI API connection
    if config.active_api_key:
        provider_name = "OpenRouter" if config.api_provider == "openrouter" else "Anthropic"
        click.echo(f"Checking {provider_name} API connection...")
        click.echo(f"       Provider: {config.api_provider}")
        click.echo(f"       Model: {config.effective_model}")
        try:
            processor = IssueProcessor(
                config.active_api_key,
                config.effective_model,
                provider=config.api_provider,
            )
            if processor.test_connection():
                click.echo(click.style(f"  [OK] {provider_name} API connected", fg="green"))
            else:
                click.echo(click.style(f"  [FAIL] {provider_name} API connection failed", fg="red"))
        except Exception as e:
            click.echo(click.style(f"  [FAIL] {provider_name} error: {e}", fg="red"))


@cli.command()
@click.option("--clear", is_flag=True, help="Clear all cache entries")
@click.option("--cleanup", is_flag=True, help="Remove expired entries only")
def cache(clear, cleanup):
    """Manage the local cache."""
    cache_manager = CacheManager()

    if clear:
        count = cache_manager.clear()
        click.echo(f"Cleared {count} cache entries.")
    elif cleanup:
        count = cache_manager.cleanup_expired()
        click.echo(f"Removed {count} expired entries.")
    else:
        stats = cache_manager.get_stats()
        click.echo("Cache Statistics:")
        click.echo(f"  Location: {stats['cache_dir']}")
        click.echo(f"  Total entries: {stats['total_entries']}")
        click.echo(f"  Valid entries: {stats['valid_entries']}")
        click.echo(f"  Expired entries: {stats['expired_entries']}")
        click.echo(f"  Total size: {stats['total_size_bytes']} bytes")


@cli.command()
@click.argument("repo")
@click.pass_context
def info(ctx, repo):
    """Show information about a repository."""
    config = ctx.obj["config"]

    if not config.github_token:
        click.echo(click.style("Error: GITHUB_TOKEN is required", fg="red"), err=True)
        sys.exit(1)

    client = GitHubClient(config.github_token)

    try:
        repository = client.get_repository(repo)
        click.echo(f"Repository: {repository.full_name}")
        click.echo(f"Description: {repository.description or 'No description'}")
        click.echo(f"Stars: {repository.stargazers_count}")
        click.echo(f"Open Issues: {repository.open_issues_count}")
        click.echo(f"Language: {repository.language or 'Not specified'}")
        click.echo(f"URL: {repository.html_url}")
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
