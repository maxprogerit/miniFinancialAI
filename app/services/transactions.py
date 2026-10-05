import csv
import io

from pydantic import ValidationError

from app.core.current_user import get_current_user_id
from app.db.database import get_connection
from app.schemas import TransactionImportRow


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
                (get_current_user_id(),)
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


def _rows_to_transactions(rows) -> list[dict]:
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


def list_current_user_transactions(category: str | None = None) -> list[dict]:
    if category is not None:
        category = resolve_category(category)

    with get_connection() as conn:
        with conn.cursor() as cur:
            if category is not None:
                cur.execute(
                    """
                    SELECT merchant, amount, currency, category, transaction_date
                    FROM transactions
                    WHERE user_id = %s
                        AND category = %s
                    ORDER BY transaction_date DESC;
                    """,
                    (get_current_user_id(), category)
                )
            else:
                cur.execute(
                    """
                    SELECT merchant, amount, currency, category, transaction_date
                    FROM transactions
                    WHERE user_id = %s
                    ORDER BY transaction_date DESC;
                    """,
                    (get_current_user_id(),)
                )
            rows = cur.fetchall()

    return _rows_to_transactions(rows)


def search_current_user_transactions(category: str) -> list[dict]:
    return list_current_user_transactions(category)


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
                (get_current_user_id(), category)
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
                (get_current_user_id(),)
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


def import_current_user_transactions(rows: list[dict]) -> None:
    """Bulk-insert already-validated transaction rows for the current user."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO transactions
                    (user_id, merchant, amount, currency, category, transaction_date)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                [
                    (
                        get_current_user_id(),
                        row["merchant"],
                        row["amount"],
                        row["currency"],
                        row["category"],
                        row["transaction_date"],
                    )
                    for row in rows
                ]
            )


def import_transactions_csv(csv_text: str) -> dict:
    """Parse + validate a CSV of transactions and insert the valid rows.

    Expected columns: merchant, amount, currency, category, transaction_date
    (YYYY-MM-DD). Invalid rows are skipped and reported, not just rejected
    wholesale - one bad row shouldn't block the rest of the file.
    """
    reader = csv.DictReader(io.StringIO(csv_text))

    valid_rows: list[dict] = []
    errors: list[str] = []

    for line_number, raw_row in enumerate(reader, start=2):  # header is line 1
        try:
            row = TransactionImportRow.model_validate(raw_row)
        except ValidationError as e:
            field_errors = ", ".join(
                f"{err['loc'][0]}: {err['msg']}" for err in e.errors()
            )
            errors.append(f"Line {line_number}: {field_errors}")
            continue

        valid_rows.append({
            "merchant": row.merchant,
            "amount": row.amount,
            "currency": row.currency.upper(),
            "category": row.category,
            "transaction_date": row.transaction_date,
        })

    if valid_rows:
        import_current_user_transactions(valid_rows)

    return {
        "imported": len(valid_rows),
        "skipped": len(errors),
        "errors": errors,
    }
