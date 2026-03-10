from functools import lru_cache
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    openrouter_api_key: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_service_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    environment: str = "development"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "https://engbrain.app",
        "https://eng-ai-web.vercel.app",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()  # backward compat
