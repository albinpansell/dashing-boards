from __future__ import annotations

from typing import Any, Callable

from .source import PollingDataSource
from .types import DataType


class HttpDataSource(PollingDataSource):
    """Thin HTTP/REST data source.

    Uses `httpx` if available, otherwise falls back to `urllib.request`.
    `transform` can map the raw JSON response into the shape a component expects.
    """

    def __init__(
        self,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        body: Any = None,
        data_type: DataType = DataType.DICT,
        transform: Callable[[Any], Any] | None = None,
        timeout_s: float = 10.0,
        refresh_interval_s: float | None = None,
        source_id: str | None = None,
    ) -> None:
        super().__init__(data_type, refresh_interval_s, source_id)
        self._url = url
        self._method = method.upper()
        self._headers = headers or {}
        self._params = params or {}
        self._body = body
        self._transform = transform
        self._timeout = timeout_s

    def fetch(self) -> Any:
        data = self._fetch_raw()
        return self._transform(data) if self._transform else data

    def _fetch_raw(self) -> Any:
        try:
            import httpx

            with httpx.Client(timeout=self._timeout) as client:
                resp = client.request(
                    self._method,
                    self._url,
                    headers=self._headers,
                    params=self._params,
                    json=self._body if self._body is not None else None,
                )
                resp.raise_for_status()
                return resp.json()
        except ImportError:
            import json
            import urllib.parse
            import urllib.request

            qs = urllib.parse.urlencode(self._params)
            url = f"{self._url}?{qs}" if qs else self._url
            data_bytes = json.dumps(self._body).encode("utf-8") if self._body is not None else None
            req = urllib.request.Request(url, data=data_bytes, method=self._method, headers=self._headers)
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
