import os
from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class Config:
    github_token: str
    openai_api_key: str
    model: str = "gpt-4o"
    strictness: str = "medium"
    style_guide: str = "none"
    max_files: int = 20
    exclude_patterns: List[str] = field(default_factory=lambda: ["*.md", "*.txt", "*.lock"])
    line_comment_threshold: float = 0.6
    github_repository: str = ""
    github_event_path: str = ""

def load_config() -> Config:
    github_token = os.environ.get("INPUT_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")
    openai_api_key = os.environ.get("INPUT_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    
    if not github_token:
        raise ValueError("Missing github_token. Provide it via INPUT_GITHUB_TOKEN or GITHUB_TOKEN.")
    if not openai_api_key:
        raise ValueError("Missing openai_api_key. Provide it via INPUT_OPENAI_API_KEY or OPENAI_API_KEY.")

    model = os.environ.get("INPUT_MODEL", "gpt-4o")
    
    strictness = os.environ.get("INPUT_STRICTNESS", "medium").lower()
    if strictness not in ["low", "medium", "high"]:
        raise ValueError(f"Invalid strictness: {strictness}. Allowed: low, medium, high.")

    style_guide = os.environ.get("INPUT_STYLE_GUIDE", "none").lower()
    if style_guide not in ["none", "google", "airbnb", "pep8", "standard"]:
        raise ValueError(f"Invalid style_guide: {style_guide}. Allowed: none, google, airbnb, pep8, standard.")

    try:
        max_files = int(os.environ.get("INPUT_MAX_FILES", "20"))
    except ValueError:
        raise ValueError("max_files must be an integer.")

    exclude_patterns_raw = os.environ.get("INPUT_EXCLUDE_PATTERNS", "*.md,*.txt,*.lock")
    exclude_patterns = [p.strip() for p in exclude_patterns_raw.split(",") if p.strip()]

    try:
        threshold = float(os.environ.get("INPUT_LINE_COMMENT_THRESHOLD", "0.6"))
    except ValueError:
        raise ValueError("line_comment_threshold must be a float.")

    github_repository = os.environ.get("GITHUB_REPOSITORY", "")
    github_event_path = os.environ.get("GITHUB_EVENT_PATH", "")

    return Config(
        github_token=github_token,
        openai_api_key=openai_api_key,
        model=model,
        strictness=strictness,
        style_guide=style_guide,
        max_files=max_files,
        exclude_patterns=exclude_patterns,
        line_comment_threshold=threshold,
        github_repository=github_repository,
        github_event_path=github_event_path
    )
