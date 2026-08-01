from functools import lru_cache
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = Field(default="GraphGuard AI")
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="INFO")
    API_V1_STR: str = Field(default="/api/v1")
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"])

    # Processing & Upload
    MAX_UPLOAD_SIZE_MB: int = Field(default=50)
    ALLOWED_FILE_TYPES: List[str] = Field(default=["pdf", "csv", "mp3"])
    REQUEST_TIMEOUT: int = Field(default=60)
    MAX_RETRIES: int = Field(default=3)

    # Models
    OPENROUTER_MODEL: str = Field(default="openai/gpt-4o-mini")
    EMBEDDING_MODEL: str = Field(default="BAAI/bge-small-en-v1.5")
    WHISPER_MODEL: str = Field(default="base")

    # Neo4j Settings
    NEO4J_URI: str = Field(default="")
    NEO4J_USERNAME: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="")
    NEO4J_DATABASE: str = Field(default="neo4j")

    # OpenRouter Settings
    OPENROUTER_API_KEY: str = Field(default="")

    # Cloudinary Settings
    CLOUDINARY_CLOUD_NAME: str = Field(default="")
    CLOUDINARY_API_KEY: str = Field(default="")
    CLOUDINARY_API_SECRET: str = Field(default="")

    @field_validator("OPENROUTER_API_KEY", "NEO4J_URI", "NEO4J_PASSWORD", "CLOUDINARY_CLOUD_NAME", mode="after")
    def validate_secrets_warning(cls, v, info):
        if not v and info.field_name in ["OPENROUTER_API_KEY", "NEO4J_URI"]:
            print(f"[WARNING]: {info.field_name} is empty. Real external API calls will be mocked/disabled.")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
