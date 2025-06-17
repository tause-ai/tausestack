from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables and/or a .env file.
    """
    APP_NAME: str = "TauseStack App"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # Pydantic-settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",          # Load from a .env file
        env_file_encoding='utf-8',
        case_sensitive=False,     # Environment variables are case-insensitive
        extra='ignore'            # Ignore extra fields from env
    )

# Create a single, importable instance of the settings
settings = Settings()
