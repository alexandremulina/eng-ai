from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    openrouter_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    environment: str = "development"


settings = Settings()
