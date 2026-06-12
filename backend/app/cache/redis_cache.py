"""Redis-backed cache helpers with safe no-op fallback.

The application treats Redis as an optimization, not a dependency.  If Redis is
unreachable or the redis package is not installed, cache reads miss and writes
are skipped while the normal code path continues.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from functools import lru_cache, wraps
from typing import Any, Awaitable, Callable, Optional, TypeVar

try:
    import redis
    from redis import asyncio as aioredis
except Exception:  # pragma: no cover - optional dependency during local setup
    redis = None
    aioredis = None

log = logging.getLogger(__name__)

DEFAULT_REDIS_URL = "redis://localhost:6379/0"
DEFAULT_PREFIX = "cybernest"

T = TypeVar("T")


def _redis_url() -> str:
    return os.getenv("REDIS_URL", DEFAULT_REDIS_URL)


def _prefix() -> str:
    return os.getenv("REDIS_CACHE_PREFIX", DEFAULT_PREFIX).strip(":")


def cache_key(namespace: str, *parts: Any) -> str:
    safe_parts = [str(part).replace(" ", "_") for part in parts]
    return ":".join([_prefix(), namespace, *safe_parts])


@lru_cache(maxsize=1)
def sync_client() -> Optional[Any]:
    if redis is None:
        log.warning("redis package is not installed; Redis cache disabled")
        return None
    try:
        client = redis.Redis.from_url(
            _redis_url(),
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=False,
        )
        client.ping()
        return client
    except Exception as exc:
        log.warning("Redis cache unavailable at %s: %s", _redis_url(), exc)
        return None


@lru_cache(maxsize=1)
def async_client() -> Optional[Any]:
    if aioredis is None:
        log.warning("redis package is not installed; async Redis cache disabled")
        return None
    try:
        return aioredis.Redis.from_url(
            _redis_url(),
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=False,
        )
    except Exception as exc:
        log.warning("Async Redis cache unavailable at %s: %s", _redis_url(), exc)
        return None


def get_bytes(key: str) -> Optional[bytes]:
    client = sync_client()
    if client is None:
        return None
    try:
        value = client.get(key)
        return value if isinstance(value, bytes) else None
    except Exception as exc:
        log.debug("Redis get failed for %s: %s", key, exc)
        return None


def set_bytes(key: str, value: bytes, ttl: int | None = None) -> None:
    client = sync_client()
    if client is None:
        return
    try:
        client.set(key, value, ex=ttl)
    except Exception as exc:
        log.debug("Redis set failed for %s: %s", key, exc)


async def aget_json(key: str) -> Optional[Any]:
    client = async_client()
    if client is None:
        return None
    try:
        raw = await client.get(key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)
    except Exception as exc:
        log.debug("Redis async JSON get failed for %s: %s", key, exc)
        return None


async def aset_json(key: str, value: Any, ttl: int | None = None) -> None:
    client = async_client()
    if client is None:
        return
    try:
        raw = json.dumps(value, default=str)
        await client.set(key, raw.encode("utf-8"), ex=ttl)
    except Exception as exc:
        log.debug("Redis async JSON set failed for %s: %s", key, exc)


async def cached_json(
    key: str,
    ttl: int,
    producer: Callable[[], Awaitable[T]],
) -> T:
    cached = await aget_json(key)
    if cached is not None:
        return cached
    value = await producer()
    await aset_json(key, value, ttl=ttl)
    return value


def redis_cached_json(namespace: str, ttl: int) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for async functions returning JSON-serializable values."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            key_parts = [
                repr(arg)
                for arg in args[1:]  # skip bound self
            ]
            key_parts.extend(f"{name}={value!r}" for name, value in sorted(kwargs.items()))
            key = cache_key(namespace, *key_parts)
            return await cached_json(key, ttl, lambda: func(*args, **kwargs))

        return wrapper

    return decorator


async def close_async_client() -> None:
    client = async_client()
    if client is None:
        return
    try:
        await client.aclose()
    except Exception:
        pass
    finally:
        async_client.cache_clear()


def reset_clients() -> None:
    sync_client.cache_clear()
    async_client.cache_clear()
