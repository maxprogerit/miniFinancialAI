from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.transactions import router as transactions_router
from app.core.access_log import AccessLogMiddleware
from app.core.logging_config import configure_logging

configure_logging()

app = FastAPI(title="AI Financial Assistant")

# Permissive by design: auth here is a Bearer token (Authorization header),
# never a cookie, so allow_credentials stays False and a wildcard origin is
# safe - no browser session/cookie can be riding along with these requests.
# Tighten this to a real origin list before this ever serves non-demo users.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AccessLogMiddleware)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(transactions_router)
app.include_router(documents_router)
app.include_router(health_router)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def frontend_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
