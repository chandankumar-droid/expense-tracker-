from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables / .env file.
    No secrets are hardcoded anywhere — all values come from outside.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    supabase_url: str
    supabase_key: str


# Module-level singleton — imported by the DI factory, never used as a global elsewhere.
settings = Settings()
