from contextvars import ContextVar

# Per-request identity, set by each route; tools read it instead of taking a user_id.
_current_user_id: ContextVar[int | None] = ContextVar("current_user_id", default=None)


def set_current_user_id(user_id: int) -> None:
    _current_user_id.set(user_id)


def get_current_user_id() -> int:
    user_id = _current_user_id.get()
    if user_id is None:
        raise RuntimeError(
            "No authenticated user in the current request context - "
            "this route is missing the require_user dependency."
        )
    return user_id
