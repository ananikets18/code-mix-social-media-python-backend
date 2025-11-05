"""
Centralized Configuration Management
Loads settings from environment variables with sensible defaults
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    api_env: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # CORS Settings
    allowed_origins: str = "http://localhost:3000"
    
    # Security
    api_key: str = "dev-api-key-change-in-production"
    jwt_secret_key: str = "dev-secret-change-in-production"
    
    # Rate Limiting
    rate_limit_per_minute: int = 30
    rate_limit_per_hour: int = 500
    
    # Model Configuration
    model_base_path: str = "./"
    glotlid_model_path: str = "./cis-lmuglotlid"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "detailed"
    
    # Resources
    indic_resources_path: str = "./indic_nlp_resources"
    
    # Cache
    cache_enabled: bool = True
    cache_file_path: str = "./data/analyze_cache.json"
    
    # Redis - Upstash Configuration
    redis_enabled: bool = False
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""
    redis_ttl: int = 3600
    redis_max_retries: int = 3
    redis_timeout: int = 10
    
    # Monitoring
    sentry_dsn: str = ""
    sentry_environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_allowed_origins_list(self) -> List[str]:
        """Parse comma-separated origins into a list"""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.api_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.api_env.lower() == "development"


# Global settings instance
settings = Settings()

# Print configuration on load (hide sensitive values)
if __name__ == "__main__":
    print("=" * 60)
    print("Configuration Loaded:")
    print("=" * 60)
    print(f"Environment: {settings.api_env}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Host: {settings.host}:{settings.port}")
    print(f"Workers: {settings.workers}")
    print(f"Allowed Origins: {settings.get_allowed_origins_list()}")
    print(f"API Key: {'*' * 20} (hidden)")
    print(f"Rate Limit: {settings.rate_limit_per_minute}/min, {settings.rate_limit_per_hour}/hr")
    print(f"Log Level: {settings.log_level}")
    print(f"Redis Enabled: {settings.redis_enabled}")
    print(f"Sentry Enabled: {bool(settings.sentry_dsn)}")
    print("=" * 60)
