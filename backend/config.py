import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database configuration with Docker support
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/llm_chat_app"
    )
    
    # Security settings
    secret_key: str = os.getenv(
        "SECRET_KEY", 
        "your-secret-key-here-change-this-in-production"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # LLM API keys
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
    
    # Environment detection
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    @property
    def is_docker(self) -> bool:
        """Check if running in Docker container"""
        return os.path.exists("/.dockerenv") or os.getenv("DOCKER_ENV") == "true"
    
    @property
    def effective_database_url(self) -> str:
        """Get effective database URL based on environment"""
        if self.is_docker:
            # Use postgres service name in Docker
            return self.database_url.replace("localhost", "postgres")
        return self.database_url

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()