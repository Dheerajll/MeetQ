# Pydantic Settings for application configuration
# Loads DB URLs, Ollama host, JWT secrets, and other settings from environment variables
"""
Application settings.

Reads values from the .env file and exposes them
as a typed, validated Settings object.

Usage anywhere in the app:
    from app.core.config import get_settings
    settings = get_settings()
    print(settings.database_url)
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All application configuration in one place."""

    # --- Application ---
    app_name: str = "MeetQ Backend"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # --- Database (individual components) ---
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "dheeraj"
    db_name: str = "meetq_db"

    # Full async URL (constructed from parts below)
    database_url: str = ""

    # --- Server ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # --- CORS ---
    frontend_url: str = "http://localhost:3000"

    # --- Google OAuth (fill later) ---
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = (
        "http://localhost:8000/api/v1/auth/google/callback"
    )

    # --- JWT ---
    access_token_expire_minutes: int = 1440
    jwt_algorithm: str = "HS256"

    # --- Ollama (for later) ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    def model_post_init(self, __context) -> None:
        """
        Called after all fields are loaded.
        If DATABASE_URL wasn't set explicitly in .env,
        build it from the individual DB_* fields.
        """
        if not self.database_url:
            self.database_url = (
                f"postgresql+asyncpg://"
                f"{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}"
                f"/{self.db_name}"
            )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    The .env file is read only once per process.
    """
    return Settings()