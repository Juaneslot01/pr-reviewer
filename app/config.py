from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    github_token: str = Field(..., alias="GITHUB_TOKEN", min_length=1)
    github_webhook_secret: str = Field(..., alias="GITHUB_WEBHOOK_SECRET", min_length=1)
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY", min_length=1)
    openrouter_model: str = Field(
        default="minimax/minimax-m2.5:free",
        alias="OPENROUTER_MODEL",
        min_length=1,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
        str_min_length=1,
        populate_by_name=True,
    )


settings = Settings()
