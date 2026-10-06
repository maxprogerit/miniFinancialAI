FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Schema (Alembic), then demo data, then the knowledge base, then the app -
# all three seed/migration steps are idempotent, safe on every container
# start/restart, not just the first one.
CMD ["sh", "-c", "alembic upgrade head && python seed_demo_data.py && python seed_documents.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
