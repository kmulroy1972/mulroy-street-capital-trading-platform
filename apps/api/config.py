from pydantic import BaseSettings, Field, SecretStr
from typing import List

class APIConfig(BaseSettings):
    # Database
    database_url: SecretStr = Field(..., env="DATABASE_URL")
    
    # Redis
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    
    # JWT
    jwt_secret: SecretStr = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(30, env="JWT_EXPIRE_MINUTES")
    
    # API Settings
    api_title: str = Field("Alpaca Trading API", env="API_TITLE")
    api_version: str = Field("1.0.0", env="API_VERSION")
    cors_origins: List[str] = Field(["http://localhost:3000"], env="CORS_ORIGINS")
    
    # Admin users (temporary - should be in DB)
    admin_username: str = Field("admin", env="ADMIN_USERNAME")
    admin_password: SecretStr = Field(..., env="ADMIN_PASSWORD")
    
    class Config:
        env_file = ".env"
        case_sensitive = False