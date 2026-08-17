import httpx
from bs4 import BeautifulSoup

from app.search.base import SearchProvider, SearchResult

SEARCH_URL = "https://html.duckduckgo.com/html/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class DuckDuckGoProvider(SearchProvider):
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                SEARCH_URL,
                data={"q": query},
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for result_div in soup.select(".result")[:max_results]:
            title_tag = result_div.select_one(".result__title a")
            snippet_tag = result_div.select_one(".result__snippet")

            if title_tag is None:
                continue

            title = title_tag.get_text(strip=True)
            url = title_tag.get("href", "")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            results.append(SearchResult(title=title, url=url, snippet=snippet))

        return results