import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException

from app.core.config import settings

_WINDOW_SECONDS = 60

_lock = Lock()
_request_times: dict[int, deque] = defaultdict(deque)


def enforce_chat_rate_limit(user_id: int) -> None:
    """Sliding-window limit, per authenticated user (not per IP - with real
    auth in place, user_id is a far more meaningful key than an IP address,
    which can be shared or spoofed behind a proxy).

    In-memory and per-process - fine for this single-process app, but would
    need a shared store (e.g. Redis) behind multiple workers/instances.
    """
    now = time.monotonic()

    with _lock:
        timestamps = _request_times[user_id]
        while timestamps and now - timestamps[0] > _WINDOW_SECONDS:
            timestamps.popleft()

        if len(timestamps) >= settings.chat_rate_limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Rate limit exceeded: max {settings.chat_rate_limit_per_minute} "
                    f"requests per {_WINDOW_SECONDS} seconds."
                ),
            )

        timestamps.append(now)
