import os
from collections.abc import AsyncIterator

from groq import AsyncGroq

from app.llm.base import LLMProvider

DEFAULT_MODEL = "llama-3.3-70b-versatile"


class GroqProvider(LLMProvider):
    def __init__(self) -> None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to backend/.env"
            )
        self._client = AsyncGroq(api_key=api_key)

    async def complete(self, message: str) -> str:
        response = await self._client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": message}],
        )
        return response.choices[0].message.content or ""

    async def stream(self, message: str) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": message}],
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta