import httpx
import logging
import asyncio
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self.client = httpx.AsyncClient(headers=self.headers, base_url=self.base_url)

    async def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        for attempt in range(4):
            try:
                if method.lower() == "get":
                    response = await self.client.get(url, **kwargs)
                elif method.lower() == "post":
                    response = await self.client.post(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported method {method}")
                
                if response.status_code == 403 and "rate limit" in response.text.lower():
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited. Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                if attempt == 3:
                    logger.error(f"HTTP error on {method} {url}: {e.response.text}")
                    raise
                await asyncio.sleep(2 ** attempt)
        raise Exception("Max retries exceeded")

    async def get_pull_request_diff(self, owner: str, repo: str, pr_number: int) -> str:
        url = f"/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = self.headers.copy()
        headers["Accept"] = "application/vnd.github.v3.diff"
        
        response = await self._request_with_retry("get", url, headers=headers)
        return response.text

    async def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        url = f"/repos/{owner}/{repo}/pulls/{pr_number}/files"
        response = await self._request_with_retry("get", url)
        return response.json()

    async def post_review(self, owner: str, repo: str, pr_number: int, comments: List[Dict[str, Any]], summary_body: str, event: str = "COMMENT") -> None:
        url = f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        payload = {
            "body": summary_body,
            "event": event,
            "comments": comments
        }
        await self._request_with_retry("post", url, json=payload)

    async def post_issue_comment(self, owner: str, repo: str, pr_number: int, body: str) -> None:
        url = f"/repos/{owner}/{repo}/issues/{pr_number}/comments"
        payload = {"body": body}
        await self._request_with_retry("post", url, json=payload)

    async def close(self) -> None:
        await self.client.aclose()
