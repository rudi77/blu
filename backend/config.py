from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    # OpenAI
    openai_api_key: str
    
    # BluDelta Service
    bludelta_service_url: str = "http://localhost:8081"
    bludelta_api_key: str = ""
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/blu"
    
    # Agent
    default_model: str = "gpt-4"
    max_steps: int = 6
    planning_interval: int = 2
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings() 