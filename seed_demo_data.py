"""Seeds the two demo users + their demo transactions.

Schema creation is Alembic's job now (alembic/versions/0001_baseline_schema.py)
- this script only inserts data, and only once (skips if any user already
  exists), so it's safe to run on every container start.
"""
from app.db.database import get_connection
from app.services.auth import register_user

DEMO_PASSWORD = "DemoPass123!"

DEMO1_TRANSACTIONS = [
    ("Apple", 1500, "EUR", "electronics", "2026-08-03"),
    ("NVIDIA", 600, "EUR", "electronics", "2026-08-05"),
    ("Restaurant Bella", 80, "EUR", "restaurant", "2026-08-07"),
    ("Amazon", 120, "EUR", "electronics", "2026-08-10"),
    ("Supermarket", 250, "EUR", "groceries", "2026-08-12"),
    ("Swimming Pool", 100, "EUR", "sport", "2026-08-15"),
    ("Restaurant Roma", 60, "EUR", "restaurant", "2026-08-20"),
    ("Hotel", 300, "EUR", "travel", "2026-08-25"),
    ("Restaurant Tokyo", 90, "EUR", "restaurant", "2026-07-05"),
    ("Amazon", 200, "EUR", "electronics", "2026-07-10"),
    ("Supermarket", 180, "EUR", "groceries", "2026-07-15"),
]

DEMO2_TRANSACTIONS = [
    ("Apple", 3000, "EUR", "electronics", "2026-08-03"),
]


def main():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM users;")
            if cur.fetchone()[0] > 0: # type: ignore
                print("Demo users already seeded, skipping.")
                return

    demo1_id = register_user("demo1@example.com", DEMO_PASSWORD)
    demo2_id = register_user("demo2@example.com", DEMO_PASSWORD)

    rows = (
        [(demo1_id, *t) for t in DEMO1_TRANSACTIONS]
        + [(demo2_id, *t) for t in DEMO2_TRANSACTIONS]
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO transactions
                    (user_id, merchant, amount, currency, category, transaction_date)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                rows,
            )

    print(f"Seeded 2 demo users and {len(rows)} transactions.")


if __name__ == "__main__":
    main()
