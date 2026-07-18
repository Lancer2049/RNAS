"""Shared HTTP client with sensible defaults (timeout, connection pool)."""

import httpx

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """Return a shared httpx AsyncClient with default 10s timeout."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_keepalive_connections=5),
        )
    return _client
