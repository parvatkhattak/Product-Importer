"""Application configuration."""
import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://user:password@localhost:5432/product_importer"
    )
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Application
    environment: str = os.getenv("ENVIRONMENT", "development")
    cors_origins: str = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:8000,http://localhost:3000"
    )
    
    # Upload settings
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "10000"))
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
