from __future__ import annotations

from datetime import UTC, datetime
from html import unescape
from html.parser import HTMLParser
from typing import Protocol
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings


class WebResearchError(RuntimeError):
    """Raised when search or page retrieval fails."""


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    url: str
    snippet: str = ""
    provider: str
    rank: int
    query: str


class RetrievedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    url: str
    excerpt: str
    query: str | None = None
    provider: str
    rank: int | None = None
    retrieved_at: datetime


class SearchProvider(Protocol):
    provider_name: str

    def search(self, *, query: str, max_results: int) -> list[SearchResult]: ...


class PageFetcher(Protocol):
    def fetch(self, *, url: str, query: str | None = None, rank: int | None = None) -> RetrievedDocument: ...


class TradeOffHTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_title = False
        self._skip_depth = 0
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag in {"p", "div", "article", "section", "main", "li", "br", "h1", "h2", "h3"}:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        normalized = " ".join(data.split())
        if not normalized:
            return
        if self._in_title:
            self.title_parts.append(normalized)
        self.text_parts.append(normalized)

    @property
    def title(self) -> str:
        return " ".join(self.title_parts).strip()

    @property
    def text(self) -> str:
        return _normalize_whitespace(" ".join(self.text_parts))


class DuckDuckGoHTMLParser(HTMLParser):
    def __init__(self, *, query: str) -> None:
        super().__init__(convert_charrefs=True)
        self.query = query
        self.results: list[SearchResult] = []
        self._current_href: str | None = None
        self._current_title_parts: list[str] = []
        self._capture_title = False
        self._capture_snippet = False
        self._current_snippet_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        class_name = attributes.get("class", "")
        if tag == "a" and "result__a" in class_name:
            self._capture_title = True
            self._current_href = attributes.get("href")
            self._current_title_parts = []
            self._current_snippet_parts = []
            return
        if tag in {"a", "div"} and "result__snippet" in class_name:
            self._capture_snippet = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._capture_title:
            self._capture_title = False
            if self._current_href:
                self.results.append(
                    SearchResult(
                        title=_normalize_whitespace(" ".join(self._current_title_parts)),
                        url=unescape(self._current_href),
                        snippet=_normalize_whitespace(" ".join(self._current_snippet_parts)),
                        provider="duckduckgo_html",
                        rank=len(self.results) + 1,
                        query=self.query,
                    )
                )
            self._current_href = None
            self._current_title_parts = []
            self._current_snippet_parts = []
        if tag in {"a", "div"} and self._capture_snippet:
            self._capture_snippet = False

    def handle_data(self, data: str) -> None:
        normalized = " ".join(data.split())
        if not normalized:
            return
        if self._capture_title:
            self._current_title_parts.append(normalized)
        elif self._capture_snippet:
            self._current_snippet_parts.append(normalized)


class DuckDuckGoHTMLSearchProvider:
    provider_name = "duckduckgo_html"

    def __init__(
        self,
        *,
        user_agent: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.user_agent = user_agent or settings.web_research_user_agent
        self.timeout_seconds = timeout_seconds or settings.web_research_timeout_seconds

    def search(self, *, query: str, max_results: int) -> list[SearchResult]:
        try:
            response = httpx.get(
                f"https://html.duckduckgo.com/html/?q={quote_plus(query)}",
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout_seconds,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise WebResearchError(f"Search failed for query '{query}': {error}") from error

        parser = DuckDuckGoHTMLParser(query=query)
        parser.feed(response.text)
        results = []
        for result in parser.results:
            normalized_url = _normalize_search_result_url(result.url)
            if not normalized_url.startswith("http"):
                normalized_url = urljoin("https://duckduckgo.com", normalized_url)
            result = result.model_copy(update={"url": normalized_url})
            results.append(result)
            if len(results) >= max_results:
                break
        return results


class HTTPPageFetcher:
    def __init__(
        self,
        *,
        user_agent: str | None = None,
        timeout_seconds: float | None = None,
        max_excerpt_chars: int = 1800,
    ) -> None:
        self.user_agent = user_agent or settings.web_research_user_agent
        self.timeout_seconds = timeout_seconds or settings.web_research_timeout_seconds
        self.max_excerpt_chars = max_excerpt_chars

    def fetch(
        self,
        *,
        url: str,
        query: str | None = None,
        rank: int | None = None,
    ) -> RetrievedDocument:
        try:
            response = httpx.get(
                url,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout_seconds,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise WebResearchError(f"Page fetch failed for '{url}': {error}") from error

        parser = TradeOffHTMLTextExtractor()
        parser.feed(response.text)
        excerpt = parser.text[: self.max_excerpt_chars].strip()
        if not excerpt:
            raise WebResearchError(f"Page '{url}' did not yield readable text.")

        return RetrievedDocument(
            title=parser.title or url,
            url=str(response.url),
            excerpt=excerpt,
            query=query,
            provider=settings.web_research_search_provider,
            rank=rank,
            retrieved_at=datetime.now(UTC),
        )


def build_search_provider() -> SearchProvider:
    provider_name = settings.web_research_search_provider
    if provider_name == "duckduckgo_html":
        return DuckDuckGoHTMLSearchProvider()
    raise WebResearchError(f"Unsupported search provider '{provider_name}'.")


def build_page_fetcher() -> PageFetcher:
    return HTTPPageFetcher()


def _normalize_whitespace(value: str) -> str:
    return " ".join(unescape(value).split()).strip()


def _normalize_search_result_url(value: str) -> str:
    normalized = unescape(value).strip()
    parsed = urlparse(normalized)
    query = parse_qs(parsed.query)
    encoded_target = query.get("uddg", [None])[0]
    if encoded_target:
        return unquote(encoded_target)
    return normalized
