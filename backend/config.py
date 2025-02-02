from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    """Application settings"""
    # OpenAI
    openai_api_key: str
    
    # BluDelta Service
    bludelta_service_url: str = "http://localhost:8081"
    bludelta_api_key: str = ""
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/bludelta"
    
    # Agent
    default_model: str = "gpt-4o-mini"
    max_steps: int = 6
    planning_interval: int = 2
    
    # OpenTelemetry Configuration
    otel_exporter_otlp_endpoint: str = "http://localhost:6006/v1/traces"
    otel_service_name: str = "bluapp-backend"
    phoenix_collector_endpoint: str = "http://localhost:6006"
    
    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings() 