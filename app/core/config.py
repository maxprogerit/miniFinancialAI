from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    openai_model: str = "gpt-5.6-luna"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_timeout_seconds: float = 30.0
    database_url: str
    rag_top_k: int = 3
    jwt_secret: str
    jwt_access_token_expire_minutes: int = 60
    chat_rate_limit_per_minute: int = 20


settings = Settings()  # type: ignore[call-arg]
