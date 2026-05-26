from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://tradeofflab:tradeofflab@db:5432/tradeofflab"
    litellm_base_url: str = "http://litellm:4000"
    litellm_model: str = "tradeofflab-default"
    litellm_api_key: str = "tradeofflab-dev-key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
