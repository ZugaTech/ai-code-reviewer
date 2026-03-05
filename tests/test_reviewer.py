import pytest
import pytest_asyncio
from src.config import Config
from src.reviewer import Reviewer
from src.openai_client import ReviewComment

class MockGitHubClient:
    def __init__(self):
        self.posted_reviews = []
        self.posted_comments = []

    async def get_pull_request_diff(self, owner, repo, pr_number):
        return """diff --git a/test.py b/test.py
index e69de29..d95f3ad 100644
--- a/test.py
+++ b/test.py
@@ -1,1 +1,2 @@
-print("A")
+print("B")
+print("C")"""

    async def get_pull_request_files(self, owner, repo, pr_number):
        return []

    async def post_review(self, owner, repo, pr_number, comments, summary):
        self.posted_reviews.append((owner, repo, pr_number, comments, summary))

    async def post_issue_comment(self, owner, repo, pr_number, body):
        self.posted_comments.append(body)

    async def close(self):
        pass

class MockOpenAIClient:
    async def review_hunk(self, hunk_data, filename, config):
        return [
            ReviewComment(filename=filename, line=2, side="RIGHT", body="Consider better naming.", confidence=0.9)
        ]

    async def generate_summary(self, comments, metadata, config):
        return "Summary of the review."

@pytest.mark.asyncio
async def test_reviewer_orchestrate():
    config = Config(github_token="fake", openai_api_key="fake")
    github = MockGitHubClient()
    openai = MockOpenAIClient()

    reviewer = Reviewer(config, github, openai)
    await reviewer.orchestrate("octocat", "Hello-World", 1)

    assert len(github.posted_reviews) == 1
    assert github.posted_reviews[0][4] == "Summary of the review."
    assert len(github.posted_reviews[0][3]) == 1
