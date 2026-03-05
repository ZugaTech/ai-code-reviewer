import json
from dataclasses import dataclass
from typing import List, Dict, Any
import tiktoken
from openai import AsyncOpenAI
from config import Config

@dataclass
class ReviewComment:
    filename: str
    line: int
    side: str
    body: str
    confidence: float

class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    def _get_system_prompt(self, strictness: str, style_guide: str) -> str:
        prompt = "You are an expert AI code reviewer. "
        
        if strictness == "low":
            prompt += "Only flag clear bugs and security issues. Be concise. "
        elif strictness == "medium":
            prompt += "Flag bugs, performance issues, and code clarity problems. Suggest improvements. "
        elif strictness == "high":
            prompt += "Exhaustively review for bugs, security, performance, readability, test coverage gaps, and style guide violations. Be specific. "

        if style_guide != "none":
            guide_descriptions = {
                "google": "Follow the Google Style Guide for the target language.",
                "airbnb": "Follow the Airbnb Style Guide.",
                "pep8": "Strictly adhere to PEP 8 standards for Python.",
                "standard": "Follow standard idiomatic coding practices tightly."
            }
            prompt += guide_descriptions.get(style_guide, "")

        prompt += """
Respond primarily with JSON containing a list of `comments`.
Format:
{
  "comments": [
    {
      "filename": "string",
      "line": 123,
      "side": "RIGHT",
      "body": "Your review comment here",
      "confidence": 0.8
    }
  ]
}
For `side`, use "RIGHT" for modifications/additions, or "LEFT" if referring to old code.
Line number must be the EXACT code line in the hunk you are commenting on.
"""
        return prompt

    async def review_hunk(self, hunk_data: str, filename: str, config: Config) -> List[ReviewComment]:
        system_prompt = self._get_system_prompt(config.strictness, config.style_guide)
        user_prompt = f"Review the following diff for file `{filename}`.\n\n```diff\n{hunk_data}\n```\nProvide structural comments for issues found."

        try:
            response = await self.client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            if not content:
                return []
                
            data = json.loads(content)
            comments = []
            for item in data.get("comments", []):
                comments.append(ReviewComment(
                    filename=item["filename"],
                    line=item["line"],
                    side=item["side"],
                    body=item["body"],
                    confidence=float(item.get("confidence", 1.0))
                ))
            return comments
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error reviewing hunk: {e}")
            return []

    async def generate_summary(self, all_comments: List[ReviewComment], pr_metadata: Dict[str, Any], config: Config) -> str:
        if not all_comments:
            return "LGTM! No structural or stylistic issues found by AI Reviewer."
            
        system_prompt = "You are a senior tech lead. Summarize the AI code review comments."
        user_prompt = f"PR metadata: {json.dumps(pr_metadata)}\nTotal issues found: {len(all_comments)}\n"
        
        sample_comments = [f"{c.filename}:{c.line} - {c.body}" for c in all_comments[:10]]
        user_prompt += "Sample issues:\n" + "\n".join(sample_comments)
        user_prompt += "\nWrite a friendly PR review summary (1-2 paragraphs)."

        try:
            response = await self.client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content or "Summary could not be generated."
        except Exception as e:
            return f"Reviewed successfully, {len(all_comments)} comments generated."
