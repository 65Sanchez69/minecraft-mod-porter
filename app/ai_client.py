import os
from typing import Optional


class AIClient:
    """Optional Groq API client for AI-assisted patches."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.enabled = bool(self.api_key)

    def is_available(self) -> bool:
        return self.enabled
