from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.agent import ask_ai
from app.schemas import (
    SpendingSummary,
    TransactionList,
    TotalSpending,
    CategoryList,
    KnowledgeAnswer,
    Refusal,
    ComparisonResult
)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


ChatResponse = (
    SpendingSummary
    | TransactionList
    | TotalSpending
    | CategoryList
    | KnowledgeAnswer
    | Refusal
    | ComparisonResult
)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:

    try:
        answer, _ = ask_ai(request.message)
        return answer # type: ignore
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
