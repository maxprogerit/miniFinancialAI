from pgvector import Vector
from pgvector.psycopg import register_vector

from app.core.config import settings
from app.core.current_user import get_current_user_id
from app.db.database import get_connection
from app.rag.embeddings import embed_text


def search_financial_knowledge(query: str, top_k: int | None = None) -> list[dict]:
    if top_k is None:
        top_k = settings.rag_top_k

    query_embedding = embed_text(query)
    user_id = get_current_user_id()

    with get_connection() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT source, content
                FROM documents
                WHERE user_id IS NULL OR user_id = %s
                ORDER BY embedding <=> %s
                LIMIT %s;
                """,
                (user_id, Vector(query_embedding), top_k)
            )
            rows = cur.fetchall()

    return [
        {"source": row[0], "content": row[1]}
        for row in rows
    ]
