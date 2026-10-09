import os
from typing import Optional


class AIClient:
    """Groq API client for optional AI patches."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)
