from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.core.current_user import set_current_user_id
from app.core.deps import require_user
from app.schemas import TransactionImportResult, TransactionPage
from app.services.transactions import import_transactions_csv, list_current_user_transactions

router = APIRouter()


@router.get(
    "/transactions",
    response_model=TransactionPage,
    summary="List the current user's transactions",
    description=(
        "Returns the authenticated user's transactions, optionally filtered "
        "by spending category, paginated via limit/offset."
    ),
)
def list_transactions(
    category: str | None = Query(
        default=None,
        description="Optional spending category filter, e.g. 'electronics'.",
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Max rows to return."),
    offset: int = Query(default=0, ge=0, description="Rows to skip, for paging."),
    user_id: int = Depends(require_user),
) -> TransactionPage:
    set_current_user_id(user_id)
    try:
        rows, total = list_current_user_transactions(category, limit=limit, offset=offset)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return TransactionPage(transactions=rows, total=total, limit=limit, offset=offset) # type: ignore


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
async def import_transactions(
    file: UploadFile = File(...),
    user_id: int = Depends(require_user),
) -> TransactionImportResult:
    set_current_user_id(user_id)
    content = await file.read()
    result = import_transactions_csv(content.decode("utf-8"))
    return TransactionImportResult(**result)
