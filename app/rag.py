from openai import OpenAI
from pgvector import Vector
from pgvector.psycopg import register_vector

from app.core.config import settings
from app.db.database import get_connection

client = OpenAI(api_key=settings.openai_api_key)


def embed_text(text: str) -> list[float]:
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text
    )
    return response.data[0].embedding


def search_financial_knowledge(query: str, top_k: int = 3) -> list[dict]:
    query_embedding = embed_text(query)

    with get_connection() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT source, content
                FROM documents
                ORDER BY embedding <=> %s
                LIMIT %s;
                """,
                (Vector(query_embedding), top_k)
            )
            rows = cur.fetchall()

    return [
        {"source": row[0], "content": row[1]}
        for row in rows
    ]
