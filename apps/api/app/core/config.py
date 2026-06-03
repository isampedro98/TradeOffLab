from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://tradeofflab:tradeofflab@db:5432/tradeofflab"
    litellm_base_url: str = "http://litellm:4000"
    litellm_model: str = "tradeofflab-default"
    litellm_api_key: str = "tradeofflab-dev-key"
    litellm_timeout_seconds: float = 180.0
    litellm_timeout_criteria_seconds: float = 90.0
    litellm_timeout_assumptions_seconds: float = 120.0
    litellm_timeout_evidence_seconds: float = 180.0
    litellm_timeout_tradeoff_matrix_seconds: float = 150.0
    litellm_timeout_tradeoff_self_check_seconds: float = 90.0
    litellm_timeout_adversarial_review_seconds: float = 180.0
    litellm_timeout_recommendation_memo_seconds: float = 150.0
    litellm_response_format_strategy: str = "json_schema"
    tradeoff_matrix_retry_limit: int = 2
    tradeoff_matrix_self_check_enabled: bool = False
    web_research_user_agent: str = (
        "TradeOffLabBot/0.1 (+https://github.com/tradeofflab/tradeofflab)"
    )
    web_research_timeout_seconds: float = 20.0
    web_research_search_provider: str = "duckduckgo_html"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
