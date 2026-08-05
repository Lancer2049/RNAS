"""Shared HTTP client with sensible defaults (timeout, connection pool)."""

import httpx

_client: httpx.AsyncClient | None = None
_sim_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """Return a shared httpx AsyncClient with default 10s timeout."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_keepalive_connections=5),
        )
    return _client


def get_sim_client() -> httpx.AsyncClient:
    """Return an httpx AsyncClient with a long timeout for simulation routes.

    Dial operations run serially with up to 12s per subscriber, so the
    compat proxy needs a much larger timeout than the default 10s.
    """
    global _sim_client
    if _sim_client is None:
        _sim_client = httpx.AsyncClient(
            timeout=httpx.Timeout(600.0),
            limits=httpx.Limits(max_keepalive_connections=5),
        )
    return _sim_client


def get_notify_client() -> httpx.AsyncClient:
    """Longer timeout client for notification test routes — outbound
    Telegram/webhook calls can take up to ~12s per channel."""
    return httpx.AsyncClient(
        timeout=httpx.Timeout(60.0),
        limits=httpx.Limits(max_keepalive_connections=5),
    )
