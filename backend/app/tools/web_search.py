from typing import Any

from app.search.base import SearchProvider
from app.tools.base import Tool


class WebSearchTool(Tool):
    def __init__(self, provider: SearchProvider) -> None:
        self._provider = provider

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the web for current information. Use this for "
            "anything that requires up-to-date facts, recent events, "
            "or information not likely to be in your training data."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                }
            },
            "required": ["query"],
        }

    async def execute(self, query: str, **kwargs: Any) -> str:
        results = await self._provider.search(query, max_results=5)

        if not results:
            return f"No search results found for '{query}'"

        lines = []
        for i, result in enumerate(results, 1):
            lines.append(f"{i}. {result.title}\n   {result.url}\n   {result.snippet}")

        return "\n\n".join(lines)