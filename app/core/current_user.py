# Placeholder for the authenticated user's id. Every data-access function in
# this app resolves "who is asking" through get_current_user_id() rather than
# a module-level constant, so the real JWT-based lookup (coming with auth)
# is a one-function change instead of a search-and-replace across services.
CURRENT_USER_ID = 1


def get_current_user_id() -> int:
    return CURRENT_USER_ID
