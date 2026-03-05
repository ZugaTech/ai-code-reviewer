import asyncio
import logging
import tiktoken
from typing import List, Dict, Any
from config import Config
from github_client import GitHubClient
from openai_client import OpenAIClient, ReviewComment
from diff_parser import parse_diff

logger = logging.getLogger(__name__)

def count_tokens(text: str, model: str) -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def format_hunk_for_prompt(hunk: Dict[str, Any]) -> str:
    lines = []
    lines.append(hunk["hunk_header"])
    for l in hunk["lines"]:
        prefix = "+" if l["type"] == "added" else "-" if l["type"] == "removed" else " "
        lines.append(f"{prefix}{l['content']}")
    return "\n".join(lines)

class Reviewer:
    def __init__(self, config: Config, github: GitHubClient, ai: OpenAIClient):
        self.config = config
        self.github = github
        self.ai = ai

    async def orchestrate(self, owner: str, repo: str, pr_number: int):
        try:
            logger.info(f"Starting review for PR #{pr_number} in {owner}/{repo}")
            
            raw_diff = await self.github.get_pull_request_diff(owner, repo, pr_number)
            if not raw_diff:
                logger.warning("Empty diff, nothing to review.")
                return

            files = parse_diff(raw_diff, self.config.exclude_patterns)
            
            # Limit files
            if len(files) > self.config.max_files:
                logger.info(f"Limiting review to max {self.config.max_files} files.")
                files = files[:self.config.max_files]

            all_comments: List[ReviewComment] = []
            
            for f in files:
                for hunk in f["hunks"]:
                    hunk_text = format_hunk_for_prompt(hunk)
                    if count_tokens(hunk_text, self.config.model) > 3000:
                        logger.warning(f"Skipping hunk in {f['filename']} (too large to safely review)")
                        continue
                        
                    comments = await self.ai.review_hunk(hunk_text, f["filename"], self.config)
                    all_comments.extend(comments)

            # Filter duplicates & apply threshold
            filtered_comments = []
            seen = set()
            for c in all_comments:
                if c.confidence >= self.config.line_comment_threshold:
                    key = (c.filename, c.line)
                    if key not in seen:
                        seen.add(key)
                        filtered_comments.append(c)

            summary = await self.ai.generate_summary(filtered_comments, {"owner": owner, "repo": repo, "pr": pr_number}, self.config)

            gh_comments = []
            for c in filtered_comments:
                gh_comments.append({
                    "path": c.filename,
                    "line": c.line,
                    "side": c.side,
                    "body": c.body
                })

            if gh_comments:
                await self.github.post_review(owner, repo, pr_number, gh_comments, summary)
            else:
                await self.github.post_issue_comment(owner, repo, pr_number, summary)
                
            logger.info("Review completed successfully.")
            
        except Exception as e:
            logger.exception(f"Fatal error during orchestration: {e}")
            raise
