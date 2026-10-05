from contextvars import ContextVar

# Set once per request by the require_user auth dependency (app/core/deps.py)
# after it validates the JWT. Every tool/service function reads "who is
# asking" through get_current_user_id() instead of taking a user_id
# parameter, so the LLM tool-calling path (which has no concept of request
# context) doesn't need to be threaded with one.
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
