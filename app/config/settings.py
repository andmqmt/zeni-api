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
    cors_origins: str = ""  # Comma-separated list of allowed origins
    
    class Config:
        env_file = ".env"


settings = Settings()
