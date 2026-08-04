from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Chatbot"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str
    database_test_url: str

    secret_key: str 
    algorithm: str
    access_token_expire_minutes: int

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


settings = Settings()