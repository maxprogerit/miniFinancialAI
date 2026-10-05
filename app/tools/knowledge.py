from app.schemas import KnowledgeAnswer
from app.rag import search_financial_knowledge

from .base import Tool

SEARCH_FINANCIAL_KNOWLEDGE = Tool(
    name="search_financial_knowledge",
    description=(
        "Search general financial knowledge and app documentation - "
        "budgeting concepts, definitions (e.g. emergency fund, gross "
        "vs net income), how this app's categories or calculations "
        "work. Use this for general financial questions, NOT for the "
        "current user's own transaction data."
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
