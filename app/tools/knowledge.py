from app.schemas import KnowledgeAnswer
from app.rag import search_financial_knowledge

from .base import Tool

SEARCH_FINANCIAL_KNOWLEDGE = Tool(
    name="search_financial_knowledge",
    description=(
        "Search general financial knowledge/app documentation AND the "
        "current user's own uploaded notes - budgeting concepts, "
        "definitions (e.g. emergency fund, gross vs net income), how this "
        "app's categories or calculations work, and anything the user has "
        "personally uploaded via /documents. Use this for general "
        "financial questions or questions about the user's notes, NOT for "
        "their transaction data (use the transaction tools for that)."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The financial knowledge question to search for."
            }
        },
        "required": ["query"],
        "additionalProperties": False
    },
    handler=lambda args: search_financial_knowledge(args["query"]),
)

FINISH_WITH_KNOWLEDGE_ANSWER = Tool(
    name="finish_with_knowledge_answer",
    description=(
        "Call this as your final action once you have synthesized an "
        "answer from search_financial_knowledge results."
    ),
    parameters={
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "sources": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["answer", "sources"],
        "additionalProperties": False
    },
    response_model=KnowledgeAnswer,
)
