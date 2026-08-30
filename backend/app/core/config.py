import os
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "CodeGuardian"
    app_env: str = "development"
    debug: bool = True
    database_url: str
    redis_url: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    github_token: str | None = None
    github_api_url: str = "https://api.github.com"
    github_default_branch: str | None = None
    github_owner: str | None = None
    github_app_id: str | None = "4763885"
    github_app_private_key: str | None = None
    github_app_private_key_path: str | None = None
    github_webhook_secret: str | None = None
    frontend_origin: str | None = None
    frontend_url: str | None = "http://localhost:5173"
    resend_api_key: str | None = None
    alert_email: str | None = "sunilkumarb200703@gmail.com"
    sender_email: str = "onboarding@resend.dev"
    approval_token_secret: str | None = None

    openrouter_api_key: str | None = None
    openrouter_model: str = "poolside/laguna-s-2.1:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str | None = None
    openrouter_site_name: str | None = None

    # Generic & Direct Provider Configuration (Sarvam, DeepSeek, OpenRouter)
    ai_provider: str = "sarvam"
    ai_base_url: str = "https://api.sarvam.ai"
    ai_model: str = "sarvam-105b"
    
    sarvam_api_key: str | None = None
    sarvam_base_url: str = "https://api.sarvam.ai"
    sarvam_model: str = "sarvam-105b"

    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
