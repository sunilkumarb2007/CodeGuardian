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

    openrouter_api_key: str | None = None
    openrouter_model: str = "meta-llama/llama-3-8b-instruct:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str | None = None
    openrouter_site_name: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
