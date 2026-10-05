import logging

import openai
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.current_user import set_current_user_id
from app.core.deps import require_user
from app.core.rate_limit import enforce_chat_rate_limit
from app.schemas import ChatResponse, KnowledgeAnswer, UsageInfo
from app.services.agent import ask_ai

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask the financial assistant a question",
    description=(
        "Runs the user's message through the tool-calling agent and returns a "
        "structured answer, the tools the agent used to produce it, any cited "
        "document sources, and token usage for the request."
    ),
)
def chat(request: ChatRequest, user_id: int = Depends(require_user)) -> ChatResponse:
    set_current_user_id(user_id)
    enforce_chat_rate_limit(user_id)
    try:
        result = ask_ai(request.message)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except openai.OpenAIError:
        logger.exception("OpenAI API call failed while handling /chat")
        raise HTTPException(
            status_code=503,
            detail="The AI service is temporarily unavailable. Please try again.",
        )
    except Exception:
        logger.exception("Unexpected error while handling /chat")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while processing your request.",
        )

    sources = (
        result.answer.sources
        if isinstance(result.answer, KnowledgeAnswer)
        else []
    )

    return ChatResponse(
        answer=result.answer,
        tool_calls=result.tool_calls,
        sources=sources,
        usage=UsageInfo(
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
        ),
    )
