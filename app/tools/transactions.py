from app.db.database import get_connection
from app.schemas import CategoryList, TransactionList, SpendingSummary, TotalSpending, ComparisonResult
from .base import Tool

CURRENT_USER_ID = 1

def list_current_user_categories() -> list:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT category
                FROM transactions
                WHERE user_id = %s
                ORDER BY category;
                """,
                (CURRENT_USER_ID,)
            )
            rows = cur.fetchall()
    return [row[0] for row in rows]
def resolve_category(category: str) -> str:
    valid_categories = list_current_user_categories()
    normalized = category.strip().lower().rstrip("s")

    for valid in valid_categories:
        if valid.lower().rstrip("s") == normalized:
            return valid

    raise ValueError(
        f"Unknown category '{category}'. "
        f"Valid categories: {', '.join(valid_categories)}"
    )
def search_current_user_transactions(category: str) -> list:
    category = resolve_category(category)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    merchant,
                    amount,
                    currency,
                    category,
                    transaction_date
                FROM transactions
                WHERE user_id = %s
                    AND category = %s
                ORDER BY transaction_date DESC;
                """,
                (CURRENT_USER_ID, category)
            )
            rows = cur.fetchall()

    return [
        {
            "merchant": row[0],
            "amount": float(row[1]),
            "currency": row[2],
            "category": row[3],
            "date": str(row[4])
        }
        for row in rows
    ]

def calculate_category_spending(category: str) -> dict:
    category = resolve_category(category)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    currency,
                    SUM(amount),
                    COUNT(*)
                FROM transactions
                WHERE user_id = %s
                  AND category = %s
                GROUP BY currency;
                """,
                (CURRENT_USER_ID, category)
            )
            rows = cur.fetchall()

    if not rows:
        return {
            "total": 0,
            "currency": "EUR",
            "category": category,
            "transaction_count": 0
        }
    currency, total, count = rows[0]

    return {
        "total": float(total),
        "currency": currency,
        "category": category,
        "transaction_count": count
    }
def get_current_user_total_spending() -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    currency,
                    SUM(amount)
                FROM transactions
                WHERE user_id = %s
                GROUP BY currency;
                """,
                (CURRENT_USER_ID,)
            )
            rows = cur.fetchall()

    return {
        currency: float(total)
        for currency, total in rows
    }

def compare_category_to_total(category: str) -> dict:
    category_summary = calculate_category_spending(category)
    currency = category_summary["currency"]

    totals_by_currency = get_current_user_total_spending()
    overall_total = totals_by_currency.get(currency, 0.0)

    percentage = (
        round(category_summary["total"] / overall_total * 100, 1)
        if overall_total else 0.0
    )

    return {
        "category": category,
        "category_total": category_summary["total"],
        "overall_total": overall_total,
        "currency": currency,
        "percentage": percentage,
    }


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
