from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.schemas import TransactionImportResult, TransactionList
from app.services.transactions import import_transactions_csv, list_current_user_transactions

router = APIRouter()


@router.get(
    "/transactions",
    response_model=TransactionList,
    summary="List the current user's transactions",
    description=(
        "Returns the authenticated user's transactions, optionally filtered "
        "by spending category."
    ),
)
def list_transactions(
    category: str | None = Query(
        default=None,
        description="Optional spending category filter, e.g. 'electronics'.",
    ),
) -> TransactionList:
    try:
        rows = list_current_user_transactions(category)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return TransactionList(transactions=rows) # type: ignore


@router.post(
    "/transactions/import",
    response_model=TransactionImportResult,
    summary="Import transactions from a CSV file",
    description=(
        "Bulk-imports transactions for the authenticated user from a CSV "
        "file with columns: merchant, amount, currency, category, "
        "transaction_date (YYYY-MM-DD). Rows that fail validation are "
        "skipped and reported; valid rows in the same file are still "
        "imported."
    ),
)
async def import_transactions(file: UploadFile = File(...)) -> TransactionImportResult:
    content = await file.read()
    result = import_transactions_csv(content.decode("utf-8"))
    return TransactionImportResult(**result)
