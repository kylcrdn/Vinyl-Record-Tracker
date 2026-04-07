from __future__ import annotations

from typing import Any

import httpx


class DiscogsError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class DiscogsService:
    BASE_URL = "https://api.discogs.com"

    def __init__(
        self,
        consumer_key: str | None,
        consumer_secret: str | None,
        user_agent: str = "VinylRecordTracker/1.0",
    ):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.user_agent = user_agent

    @property
    def headers(self) -> dict[str, str]:
        if not self.consumer_key or not self.consumer_secret:
            raise DiscogsError(500, "Discogs API credentials are not configured.")

        return {
            "Authorization": (
                f"Discogs key={self.consumer_key}, secret={self.consumer_secret}"
            ),
            "User-Agent": self.user_agent,
        }

    async def get_release(self, release_id: int) -> dict[str, Any]:
        response = await self._request(
            "/releases/{release_id}",
            path_params={"release_id": release_id},
        )
        return response.json()

    async def search_releases(self, query: str = "") -> dict[str, Any]:
        params = {
            "type": "release",
            "q": query,
        }
        response = await self._request("/database/search", params=params)
        payload = response.json()
        results = payload.get("results", [])

        return {
            "results": [self._normalize_search_result(item) for item in results],
            "pagination": payload.get("pagination", {}),
        }

    async def _request(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        path_params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        full_path = path.format(**(path_params or {}))
        url = f"{self.BASE_URL}{full_path}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self.headers, params=params)

        if response.status_code == 404:
            raise DiscogsError(404, "Release not found on Discogs")
        if response.status_code != 200:
            raise DiscogsError(response.status_code, "Discogs API error")

        return response

    def _normalize_search_result(self, item: dict[str, Any]) -> dict[str, Any]:
        format_names = item.get("format", [])
        labels = item.get("label", [])

        return {
            "id": item.get("id"),
            "title": item.get("title", ""),
            "year": item.get("year"),
            "cover_image": item.get("cover_image", ""),
            "thumb": item.get("thumb", ""),
            "formats": format_names,
            "labels": labels,
        }