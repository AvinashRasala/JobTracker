"""
Central application configuration.
All values are loaded from environment variables (see .env.example).
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "JobTrack AI"
    ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql://jobtrack:jobtrack@localhost:5432/jobtrack"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Plain comma-separated string rather than a list -- pydantic-settings
    # requires list-typed env vars to be valid JSON (e.g. '["a","b"]'), which
    # is easy to get subtly wrong in a plain-text env var editor like
    # Render's and fails with an opaque JSONDecodeError. A comma-separated
    # string can't be malformed the same way.
    # e.g. ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    # Optional: matches Vercel's per-deploy preview URLs (e.g. my-app-git-branch-user.vercel.app)
    # in addition to the exact origins above. Leave blank to disable.
    ALLOWED_ORIGIN_REGEX: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/gmail/callback"
    # Where to send the browser after the Google OAuth flow completes.
    FRONTEND_URL: str = "http://localhost:3000"
    # Used to encrypt Gmail OAuth tokens at rest. Generate with:
    # python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ENCRYPTION_KEY: str = ""

    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """
        Render, Heroku, and some other hosts provide connection strings as
        'postgres://...'. Modern SQLAlchemy only recognizes 'postgresql://',
        so we rewrite it here rather than requiring the person to edit the
        host's auto-generated env var.
        """
        if value.startswith("postgres://"):
            return "postgresql://" + value[len("postgres://"):]
        return value

    @property
    def allowed_origins_list(self) -> list[str]:
        """
        Parses ALLOWED_ORIGINS into a list for CORSMiddleware. Accepts a
        plain comma-separated string (the documented format) and, for
        backwards compatibility, a JSON array string too.
        """
        value = self.ALLOWED_ORIGINS.strip()
        if not value:
            return []
        if value.startswith("["):
            import json
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(origin).strip() for origin in parsed if str(origin).strip()]
            except (json.JSONDecodeError, TypeError):
                pass
        return [origin.strip() for origin in value.split(",") if origin.strip()]


settings = Settings()
