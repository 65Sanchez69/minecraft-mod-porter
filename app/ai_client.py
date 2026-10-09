import json
import os
from typing import Dict, List, Optional

import requests


class AIClient:
    """Thin wrapper around Groq API if an API key is available."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_patch(self, file_name: str, content: str, source_version: str, target_version: str) -> str:
        if not self.is_configured():
            return self._offline_patch(file_name, content, source_version, target_version)

        try:
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a careful Minecraft Forge porting assistant. "
                            "Provide actionable Java patch guidance for migration between versions. "
                            "Be conservative and keep code valid."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Port this Java source from Forge {source_version} to {target_version}. "
                            "Return a concise patch or rewrite suggestion. Do not invent unavailable APIs.\n\n"
                            f"File: {file_name}\n\n{content[:8000]}"
                        ),
                    },
                ],
                "temperature": 0.2,
            }

            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )

            if response.status_code != 200:
                raise RuntimeError(f"Groq API request failed: {response.text[:400]}")

            data = response.json()
            result = data["choices"][0]["message"]["content"]
            return result.strip() or self._offline_patch(file_name, content, source_version, target_version)
        except Exception:
            return self._offline_patch(file_name, content, source_version, target_version)

    def _offline_patch(self, file_name: str, content: str, source_version: str, target_version: str) -> str:
        return (
            f"Offline fallback patch suggestion for {file_name}\n"
            f"Source: {source_version}, Target: {target_version}\n"
            "1. Update deprecated Forge registry APIs to current Registries-based patterns.\n"
            "2. Replace old game engine accessors with current static access patterns.\n"
            "3. Review networking, rendering, and event handler signatures before final build.\n"
            "4. Validate imports after automated replacement."
        )


def summarize_ai_report(results: List[Dict[str, str]]) -> str:
    if not results:
        return "No AI suggestions generated."

    lines = ["AI Summary:"]
    for item in results:
        lines.append(f"- {item['file']}: {item['summary'][:180]}")
    return "\n".join(lines)
