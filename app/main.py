from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.transactions import router as transactions_router
from app.core.access_log import AccessLogMiddleware
from app.core.logging_config import configure_logging

configure_logging()

app = FastAPI(title="AI Financial Assistant")
app.add_middleware(AccessLogMiddleware)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(transactions_router)
app.include_router(documents_router)
