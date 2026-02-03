# SmartIssues

AI-driven GitHub Issues analysis tool powered by Claude.

## Features

- **Automatic Issue Fetching**: Fetch issues from any GitHub repository (public or private)
- **AI-Powered Analysis**: Use Claude AI to categorize, prioritize, and summarize issues
- **Markdown Reports**: Generate detailed reports with insights and recommendations
- **Todo Lists**: Create actionable task lists sorted by priority
- **CLI Interface**: Easy-to-use command line interface
- **GitHub Actions**: Automate report generation with scheduled workflows
- **Caching**: Local cache support for faster repeated analysis
- **Multi-repo Support**: Analyze multiple repositories in batch

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/smartissues.git
cd smartissues

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:
```env
GITHUB_TOKEN=your_github_personal_access_token
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Getting API Keys

- **GitHub Token**: Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens) and create a token with `repo` scope
- **Anthropic API Key**: Sign up at [Anthropic Console](https://console.anthropic.com/) and create an API key

## Usage

### Check Configuration

```bash
python cli.py check
```

### Analyze Issues

```bash
# Basic analysis (console output)
python cli.py analyze owner/repo

# Generate markdown report
python cli.py analyze owner/repo --format report --output report.md

# Generate todo list
python cli.py analyze owner/repo --format todo --output todo.md

# Filter by state and labels
python cli.py analyze owner/repo --state open --labels bug --labels critical

# Limit number of issues
python cli.py analyze owner/repo --max-issues 10
```

### Repository Info

```bash
python cli.py info owner/repo
```

### Cache Management

```bash
# View cache stats
python cli.py cache

# Clear all cache
python cli.py cache --clear

# Remove expired entries
python cli.py cache --cleanup
```

## CLI Options

```
Usage: cli.py [OPTIONS] COMMAND [ARGS]...

Commands:
  analyze  Analyze issues from a GitHub repository
  cache    Manage the local cache
  check    Check API connections and configuration
  info     Show information about a repository

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.
```

### Analyze Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--state` | Filter by issue state (open/closed/all) | open |
| `--max-issues, -n` | Maximum issues to fetch | 30 |
| `--labels, -l` | Filter by labels (can use multiple times) | - |
| `--output, -o` | Output file path | - |
| `--format, -f` | Output format (console/report/todo) | console |
| `--no-cache` | Disable caching | False |

## GitHub Actions

The project includes GitHub Actions workflows for automated analysis:

### Auto Report (`auto_report.yml`)

- Runs daily at 9:00 AM UTC
- Can be triggered manually with custom repository input
- Generates and uploads report as artifact
- Optionally creates an issue with the report

### CI (`ci.yml`)

- Runs on push and pull requests
- Tests across Python 3.10, 3.11, 3.12
- Includes linting with ruff and type checking with mypy

## Project Structure

```
SmartIssues/
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── github_client.py    # GitHub API wrapper
│   ├── processor.py        # Claude AI analysis
│   ├── formatter.py        # Output formatting
│   ├── utils.py            # Utility functions
│   └── cache.py            # Local cache management
├── templates/
│   ├── report.md.jinja2    # Report template
│   └── todo.md.jinja2      # Todo template
├── tests/
│   ├── test_github_client.py
│   └── test_processor.py
├── .github/workflows/
│   ├── auto_report.yml
│   └── ci.yml
├── cli.py                  # CLI entry point
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html
```

### Code Style

```bash
# Install dev tools
pip install ruff mypy

# Run linter
ruff check .

# Run type checker
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
