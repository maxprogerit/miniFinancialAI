import io

from pgvector import Vector
from pgvector.psycopg import register_vector
from pypdf import PdfReader

from app.core.current_user import get_current_user_id
from app.db.database import get_connection
from app.rag import chunk_text, embed_text

SUPPORTED_EXTENSIONS = (".txt", ".pdf")


def extract_text(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    return content.decode("utf-8")


def ingest_document(source: str, text: str) -> int:
    """Chunk, embed and store a note for the current user; returns the chunk count."""
    chunks = chunk_text(text)
    user_id = get_current_user_id()

    with get_connection() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            for index, chunk in enumerate(chunks):
                embedding = embed_text(chunk)
                cur.execute(
                    """
                    INSERT INTO documents (user_id, source, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (user_id, source, index, chunk, Vector(embedding))
                )

    return len(chunks)
