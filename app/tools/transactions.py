from app.schemas import CategoryList, TransactionList, SpendingSummary, TotalSpending, ComparisonResult
from app.services.transactions import (
    list_current_user_categories,
    search_current_user_transactions,
    calculate_category_spending,
    get_current_user_total_spending,
    compare_category_to_total,
)
from .base import Tool

LIST_CURRENT_USER_CATEGORIES = Tool(
    name="list_current_user_categories",
    description=(
        "List the distinct spending categories that the current "
        "authenticated user has transactions in. Use this when the "
        "user asks what categories they spend money in."
    ),
    parameters={
        "type": "object",
        "properties": {},
        "additionalProperties": False
    },
    handler=lambda args: list_current_user_categories(),
)
FINISH_WITH_CATEGORY_LIST = Tool(
    name="finish_with_category_list",
    description=(
        "Call this as your final action once you have the user's "
        "category list from list_current_user_categories."
    ),
    parameters={
        "type": "object",
        "properties": {
            "categories": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["categories"],
        "additionalProperties": False
    },
    response_model=CategoryList,
)

SEARCH_CURRENT_USER_TRANSACTIONS = Tool(
    name="search_current_user_transactions",
    description=(
        "Search the current authenticated user's transactions "
        "by spending category."
    ),
    parameters={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": (
                    "Spending category, for example "
                    "electronics, groceries, restaurant, sport, travel."
                )
            }
        },
        "required": ["category"],
        "additionalProperties": False
    },
    handler=lambda args: search_current_user_transactions(args["category"]),
)
FINISH_WITH_TRANSACTION_LIST = Tool(
    name="finish_with_transaction_list",
    description=(
        "Call this as your final action once you have the transaction "
        "list from search_current_user_transactions."
    ),
    parameters={
        "type": "object",
        "properties": {
            "transactions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "merchant": {"type": "string"},
                        "amount": {"type": "number"},
                        "currency": {"type": "string"},
                        "category": {"type": "string"},
                        "date": {"type": "string"}
                    },
                    "required": ["merchant", "amount", "currency", "category", "date"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["transactions"],
        "additionalProperties": False
    },
    response_model=TransactionList,
)

CALCULATE_CATEGORY_SPENDING = Tool(
    name="calculate_category_spending",
    description=(
        "Calculate the exact total spending and transaction count "
        "for the current authenticated user in a category. "
        "Use this when the user asks how much they spent."
    ),
    parameters={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Spending category."
            }
        },
        "required": ["category"],
        "additionalProperties": False
    },
    handler=lambda args: calculate_category_spending(args["category"]),
)
FINISH_WITH_SPENDING_SUMMARY = Tool(
    name="finish_with_spending_summary",
    description=(
        "Call this as your final action once you have the exact total "
        "from calculate_category_spending."
    ),
    parameters={
        "type": "object",
        "properties": {
            "total": {"type": "number"},
            "currency": {"type": "string"},
            "category": {"type": "string"},
            "transaction_count": {"type": "integer"}
        },
        "required": ["total", "currency", "category", "transaction_count"],
        "additionalProperties": False
    },
    response_model=SpendingSummary,
)
GET_CURRENT_USER_TOTAL_SPENDING = Tool(
    name="get_current_user_total_spending",
    description=(
        "Calculate the current authenticated user's total spending "
        "grouped by currency."
    ),
    parameters={
        "type": "object",
        "properties": {},
        "additionalProperties": False
    },
    handler=lambda args: get_current_user_total_spending(),
)
FINISH_WITH_TOTAL_SPENDING = Tool(
    name="finish_with_total_spending",
    description=(
        "Call this as your final action once you have the user's total "
        "spending from get_current_user_total_spending."
    ),
    parameters={
        "type": "object",
        "properties": {
            "totals": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "currency": {"type": "string"},
                        "total": {"type": "number"}
                    },
                    "required": ["currency", "total"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["totals"],
        "additionalProperties": False
    },
    response_model=TotalSpending,
)

COMPARE_CATEGORY_TO_TOTAL = Tool(
    name="compare_category_to_total",
    description=(
        "Compute the exact percentage that one spending category "
        "represents of the current user's total spending in the same "
        "currency. Use this when the user asks to compare a category "
        "to their overall spending."
    ),
    parameters={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Spending category to compare against the total."
            }
        },
        "required": ["category"],
        "additionalProperties": False
    },
    handler=lambda args: compare_category_to_total(args["category"]),
)
FINISH_WITH_COMPARISON = Tool(
    name="finish_with_comparison",
    description=(
        "Call this as your final action once you have the result from "
        "compare_category_to_total."
    ),
    parameters={
        "type": "object",
        "properties": {
            "category": {"type": "string"},
            "category_total": {"type": "number"},
            "overall_total": {"type": "number"},
            "currency": {"type": "string"},
            "percentage": {"type": "number"}
        },
        "required": [
            "category", "category_total", "overall_total",
            "currency", "percentage"
        ],
        "additionalProperties": False
    },
    response_model=ComparisonResult,
)
