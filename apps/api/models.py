from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from decimal import Decimal

class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    engine_status: str
    last_heartbeat: Optional[datetime]
    version: str
    
class AccountResponse(BaseModel):
    equity: Decimal
    cash: Decimal
    buying_power: Decimal
    positions_count: int
    daily_pnl: Decimal
    total_pnl: Decimal
    
class PositionResponse(BaseModel):
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    
class OrderResponse(BaseModel):
    id: str
    symbol: str
    side: Literal["buy", "sell"]
    order_type: str
    qty: float
    filled_qty: float
    status: Literal["new", "pending", "filled", "cancelled", "rejected"]
    created_at: datetime
    filled_at: Optional[datetime]
    limit_price: Optional[float]
    
class PnLResponse(BaseModel):
    window: Literal["1d", "1w", "1m", "ytd", "all"]
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    win_rate: float
    sharpe_ratio: Optional[float]
    max_drawdown: float
    trades_count: int
    
class StrategyInfo(BaseModel):
    name: str
    version: str
    status: Literal["disabled", "shadow", "canary", "enabled"]
    last_signal: Optional[datetime]
    positions_count: int
    daily_pnl: Decimal
    
class ConfigUpdate(BaseModel):
    daily_loss_limit: Optional[float]
    max_position_size: Optional[float]
    strategies_enabled: Optional[List[str]]
    trading_enabled: Optional[bool]
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"