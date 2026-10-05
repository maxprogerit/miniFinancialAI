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
