FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Seeding the shared knowledge base needs OPENAI_API_KEY + a reachable DB,
# so it runs as a startup step rather than at build time. It's idempotent
# (see seed_documents.py) - safe on every container start/restart.
CMD ["sh", "-c", "python seed_documents.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
