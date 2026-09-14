import os
from pathlib import Path
from dotenv import load_dotenv

# Eagerly load .env file from /app/.env or current workspace
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv(override=True)

try:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
        ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
        GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")

        class Config:
            env_file = ".env"
            extra = "ignore"

    settings = Settings()
except ImportError:
    class Settings:
        OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
        ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
        GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")

    settings = Settings()

