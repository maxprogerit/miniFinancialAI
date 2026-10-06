from datetime import date

from pydantic import BaseModel, EmailStr, Field

class SpendingSummary(BaseModel):
    total: float = Field(
        description="Total amount spent"
    )
    currency: str = Field(
        description="Currency of spending"
    )
    category: str = Field(
        description="Spending category"
    )
    transaction_count: int = Field(
        description="Number of transactions"
    )

class Transaction(BaseModel):
    merchant: str
    amount: float
    currency: str
    category: str
    date: str


class TransactionList(BaseModel):
    transactions: list[Transaction]


class TransactionPage(BaseModel):
    """GET /transactions's response - distinct from TransactionList because
    pagination metadata is meaningless on the finish_with_transaction_list
    tool path (the LLM never paginates, it just returns what it found)."""
    transactions: list[Transaction]
    total: int = Field(description="Total matching rows, ignoring limit/offset")
    limit: int
    offset: int

class CurrencyTotal(BaseModel):
    currency: str
    total: float


class TotalSpending(BaseModel):
    totals: list[CurrencyTotal]

class CategoryList(BaseModel):
    categories: list[str]


class KnowledgeAnswer(BaseModel):
    answer: str
    sources: list[str]

class Refusal(BaseModel):
    reason:str


class ComparisonResult(BaseModel):
    category: str
    category_total: float
    overall_total: float
    currency: str
    percentage: float


class UsageInfo(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float | None = Field(
        default=None,
        description=(
            "Estimated cost in USD, or null if OPENAI_INPUT_PRICE_PER_MILLION / "
            "OPENAI_OUTPUT_PRICE_PER_MILLION aren't configured."
        ),
    )


AnswerPayload = (
    SpendingSummary
    | TransactionList
    | TotalSpending
    | CategoryList
    | KnowledgeAnswer
    | Refusal
    | ComparisonResult
)


class ChatResponse(BaseModel):
    answer: AnswerPayload = Field(
        description="The structured answer, shaped by whichever finish_* tool the agent called."
    )
    tool_calls: list[str] = Field(
        description="Names of every tool the agent called, in call order, including the finish_* tool."
    )
    sources: list[str] = Field(
        description="Document sources cited for this answer, if any (non-empty only for knowledge-base answers)."
    )
    usage: UsageInfo = Field(
        description="Token usage for this request, summed across all tool-calling rounds."
    )


class TransactionImportRow(BaseModel):
    merchant: str = Field(min_length=1)
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    category: str = Field(min_length=1)
    transaction_date: date


class TransactionImportResult(BaseModel):
    imported: int = Field(description="Number of rows successfully imported")
    skipped: int = Field(description="Number of rows rejected by validation")
    errors: list[str] = Field(description="One message per skipped row, in file order")


class DocumentUploadResult(BaseModel):
    source: str = Field(description="The identifier this document is stored and cited under")
    chunks_stored: int = Field(description="Number of chunks the document was split into")


class HealthStatus(BaseModel):
    status: str = Field(description="'ok' or 'degraded'")
    database: str = Field(description="'ok' or 'unreachable'")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
