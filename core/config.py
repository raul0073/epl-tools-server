from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # ---- Mongo ----
    MONGODB_URI: str = Field(..., description="MongoDB connection URI")
    DB_NAME: str = Field(..., description="MongoDB Name")

    # ---- Server ----
    PORT: int = Field(default=8080, description="Port to run the server on")

    # Pydantic Settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings() # type: ignore
