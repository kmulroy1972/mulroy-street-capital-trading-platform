from pydantic import BaseSettings, Field, SecretStr

class EngineConfig(BaseSettings):
    # Alpaca LIVE settings
    apca_api_key_id: SecretStr = Field(..., env="APCA_API_KEY_ID")
    apca_api_secret_key: SecretStr = Field(..., env="APCA_API_SECRET_KEY")
    apca_base_url: str = Field("https://api.alpaca.markets", env="APCA_API_BASE_URL")
    
    # Database
    database_url: SecretStr = Field(..., env="DATABASE_URL")
    
    # Redis
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    
    # Engine settings
    engine_id: str = Field("engine-live-001", env="ENGINE_ID")
    heartbeat_interval: int = Field(30, env="HEARTBEAT_INTERVAL")
    
    # Risk limits - CRITICAL FOR LIVE TRADING
    daily_loss_limit: float = Field(1000.0, env="DAILY_LOSS_LIMIT")
    max_position_size: float = Field(10000.0, env="MAX_POSITION_SIZE")
    max_single_order_value: float = Field(5000.0, env="MAX_SINGLE_ORDER_VALUE")
    
    # Safety settings for live trading
    require_confirmation: bool = Field(True, env="REQUIRE_CONFIRMATION")
    enable_stop_loss: bool = Field(True, env="ENABLE_STOP_LOSS")
    stop_loss_percentage: float = Field(2.0, env="STOP_LOSS_PERCENTAGE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False