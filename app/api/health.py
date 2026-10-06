import logging

from fastapi import APIRouter

from app.db.database import get_connection
from app.schemas import HealthStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Health check",
    description="Reports whether the API process is up and whether it can reach the database.",
)
def health() -> HealthStatus:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
        database = "ok"
    except Exception:
        logger.exception("Health check: database unreachable")
        database = "unreachable"

    return HealthStatus(status="ok" if database == "ok" else "degraded", database=database)
