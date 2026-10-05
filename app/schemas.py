from pydantic import BaseModel, Field

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
