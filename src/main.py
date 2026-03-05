import asyncio
import os
import sys
import json
import logging
from config import load_config
from github_client import GitHubClient
from openai_client import OpenAIClient
from reviewer import Reviewer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        config = load_config()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    gh_repo = config.github_repository
    event_path = config.github_event_path

    if not gh_repo or not event_path:
        logger.error("Missing GITHUB_REPOSITORY or GITHUB_EVENT_PATH in environment")
        sys.exit(1)

    try:
        with open(event_path, "r", encoding="utf-8") as f:
            event_data = json.load(f)
    except Exception as e:
        logger.error(f"Could not read event payload: {e}")
        sys.exit(1)

    if "pull_request" not in event_data:
        logger.info("Not a pull request event. Exiting gracefully.")
        sys.exit(0)

    pr_number = event_data["pull_request"]["number"]
    owner, repo = gh_repo.split("/", 1)

    gh_client = GitHubClient(token=config.github_token)
    ai_client = OpenAIClient(api_key=config.openai_api_key)
    reviewer = Reviewer(config, gh_client, ai_client)

    try:
        await reviewer.orchestrate(owner, repo, pr_number)
    except Exception:
        sys.exit(1)
    finally:
        await gh_client.close()

if __name__ == "__main__":
    asyncio.run(main())
