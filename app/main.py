from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.transactions import router as transactions_router

app = FastAPI(title="AI Financial Assistant")
app.include_router(chat_router)
app.include_router(transactions_router)
