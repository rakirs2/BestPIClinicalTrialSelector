"""HTTP client for the ClinicalTrials.gov v2 API."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


@dataclass(slots=True)
class PageResult:
    studies: list[dict[str, Any]]
    next_page_token: Optional[str]


class ClinicalTrialsClient:
    """Thin wrapper around the v2 Studies endpoint."""

    def __init__(
        self,
        base_url: str,
        page_size: int = 100,
        rate_limit_per_sec: float = 3.0,
        timeout_seconds: float = 60.0,
    ) -> None:
        self._base_url = base_url
        self._page_size = page_size
        self._min_interval = 1.0 / rate_limit_per_sec
        self._last_request_ts = 0.0
        self._rate_lock = asyncio.Lock()
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(timeout_seconds))

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_first_page(self, since: Optional[str] = None) -> PageResult:
        return await self._fetch_page(None, since)

    async def fetch_page(self, page_token: Optional[str], since: Optional[str] = None) -> PageResult:
        return await self._fetch_page(page_token, since)

    @retry(
        reraise=True,
        retry=retry_if_exception_type(httpx.HTTPError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(5),
    )
    async def _fetch_page(self, page_token: Optional[str], since: Optional[str]) -> PageResult:
        params: Dict[str, Any] = {
            "pageSize": self._page_size,
        }
        if page_token:
            params["pageToken"] = page_token
        if since:
            params["lastUpdatePostDateMin"] = since

        await self._throttle()
        response = await self._client.get(self._base_url, params=params)
        response.raise_for_status()
        data = response.json()
        studies = data.get("studies", [])
        next_token = data.get("nextPageToken")
        return PageResult(studies=studies, next_page_token=next_token)

    async def _throttle(self) -> None:
        async with self._rate_lock:
            now = time.monotonic()
            elapsed = now - self._last_request_ts
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_request_ts = time.monotonic()
