from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Chatbot"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str
    database_test_url: str

    gemini_api_key: str
    gemini_model: str
    gemini_embedding_model: str
    embedding_batch_size: int = 20
    document_processing_concurrency: int = 2

    upload_dir: str = "uploads"

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    redis_url: str = "redis://localhost:6379"
    embedding_cache_ttl: int = 86400  # 24 hours in seconds
    embedding_cache_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


settings = Settings()
