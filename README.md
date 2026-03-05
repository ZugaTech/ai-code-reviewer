# AI Code Reviewer

A complete, production-ready GitHub Action that automatically reviews pull requests using OpenAI's GPT-4.

## Architecture

```
   GitHub PR     →   GitHub Action   →   AI Code Reviewer
 (Code Pushed)       (ai-review.yml)
                           ↓
                   Extract Diff (httpx)
                           ↓
                Parse Hunks & Split (tiktoken)
                           ↓
               OpenAI API (JSON Output format)
                           ↓
            Post Inline Comments + PR Summary Summary
```

## Quickstart

Add this to `.github/workflows/ai-review.yml` in your repo:

```yaml
name: AI Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: AI Code Reviewer
        uses: your-org/ai-code-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          model: "gpt-4o"
```

## Inputs

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `github_token` | Required | (none) | GitHub token for API calls |
| `openai_api_key` | Required | (none) | OpenAI API key |
| `model` | Optional | `gpt-4o` | Which OpenAI model to use |
| `strictness` | Optional | `medium` | One of "low", "medium", "high" |
| `style_guide` | Optional | `none` | "none", "google", "airbnb", "pep8", "standard" |
| `max_files` | Optional | `20` | Max number of changed files to review per PR |
| `exclude_patterns` | Optional | `*.md,*.txt,*.lock` | Glob patterns to skip |
| `line_comment_threshold`| Optional | `0.6` | Confidence threshold (0–1) |

## Example Output

*(Placeholder for screenshot)*
The AI posts inline comments on specific lines of code, pointing out potential bugs, performance flaws, and code clarity issues. It also leaves a summary comment on the PR itself.

## Local Development

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

## Security Note
Never log API keys. Always use GitHub Secrets like `secrect.OPENAI_API_KEY`.
