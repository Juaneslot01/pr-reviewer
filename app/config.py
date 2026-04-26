from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GITHUB_TOKEN: str
    GITHUB_WEBHOOK_SECRET: str
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "deepseek/deepseek-chat-v3-0324:free"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
