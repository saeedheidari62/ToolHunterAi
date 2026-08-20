import os

import requests


class DiwarSearchError(RuntimeError):
    """Raised when the Divar search adapter cannot complete a search."""


class DiwarSearch:
    """
    Production adapter for Divar's official Finder Search API.

    This adapter intentionally owns only marketplace discovery. Individual
    advertisement details remain the responsibility of DiwarFetcher.
    """

    SEARCH_URL = "https://open-api.divar.ir/v2/open-platform/finder/post"

    def __init__(self, api_key=None, timeout=20):
        self.api_key = api_key or os.getenv("DIVAR_API_KEY")
        self.timeout = timeout

    def search(self, city, query, category="tools-materials-equipment", districts=None):
        """
        Search published Divar posts and return normalized search candidates.

        Divar's official Finder API exposes brand_model as the tool-oriented
        search field, so `query` is sent as a one-item brand_model list.
        """
        if not self.api_key:
            raise DiwarSearchError("DIVAR_API_KEY is not configured")

        if not city:
            raise ValueError("city is required")

        if not query:
            raise ValueError("query is required")

        payload = {
            "category": category,
            "city": city,
            "query": {
                "brand_model": [query]
            }
        }

        if districts:
            payload["districts"] = list(districts)

        try:
            response = requests.post(
                self.SEARCH_URL,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-API-Key": self.api_key,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise DiwarSearchError(f"Divar search request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise DiwarSearchError("Divar search returned invalid JSON") from exc

        posts = data.get("posts", [])
        return [self._normalize_post(post) for post in posts if isinstance(post, dict)]

    @staticmethod
    def _normalize_post(post):
        price = post.get("price") or {}

        return {
            "token": post.get("token", ""),
            "url": (
                f"https://divar.ir/v/{post['token']}"
                if post.get("token")
                else ""
            ),
            "title": post.get("title", ""),
            "price": price.get("value", 0) if isinstance(price, dict) else 0,
            "city": post.get("city", ""),
            "category": post.get("category", ""),
            "last_modified_at": post.get("last_modified_at"),
        }
