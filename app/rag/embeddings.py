from openai import OpenAI

from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)


def embed_text(text: str) -> list[float]:
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text
    )
    return response.data[0].embedding
