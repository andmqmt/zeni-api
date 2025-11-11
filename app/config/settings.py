from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    app_name: str = "Zeni API"
    api_v1_prefix: str = "/api/v1"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200
    access_code: str
    auto_categorize_enabled: bool = True
    # Comma-separated list of allowed origins, e.g. "https://app.example.com,https://admin.example.com"
    cors_origins: str = ""
    # Whether to allow credentials (cookies, Authorization headers with credentials).
    # Default False for security; set to True only if you really need cookies/credentials.
    cors_allow_credentials: bool = False
    
    # AI Configuration
    ai_provider: str = "gemini"
    ai_provider_api_key: str | None = None
    
    class Config:
        env_file = ".env"


settings = Settings()
