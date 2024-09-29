import os
from functools import lru_cache
from pydantic import ConfigDict
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration Settings with Updated Environment Variables"""

    # New API Keys
    TAVILY_API_KEY: str
    OPENAI_API_KEY: str

    # MongoDB Configuration
    MONGODB_USER: str
    MONGODB_PASSWORD: str
    MONGODB_CLUSTER: str
    MONGODB_DB: str

    # Additional Settings (if any) can be added here

    # Root and Log Directories
    APP_ROOT_DIRECTORY: str = os.getcwd()
    LOG_DIRECTORY: str = os.path.join(APP_ROOT_DIRECTORY, "logs")

    # Pydantic Configuration
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignores any extra variables not defined in the Settings class
    )


@lru_cache()
def get_config() -> Settings:
    """Retrieve the current configuration settings."""
    return Settings()


config = get_config()
