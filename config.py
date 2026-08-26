from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "CodeGuardian"
    app_env: str = "development"
    debug: bool = True
    database_url: str
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    github_token: str | None = None
    github_api_url: str = "https://api.github.com"
    github_default_branch: str | None = None
    github_owner: str | None = None
    codeguardian_delivery_mode: str = "simulated"
    codeguardian_demo_workspace_root: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
