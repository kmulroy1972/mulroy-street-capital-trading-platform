from dataclasses import dataclass
from typing import Optional, List, Literal
from datetime import datetime
from decimal import Decimal

@dataclass
class MarketBar:
    symbol: str
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class OrderIntent:
    symbol: str
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    qty: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    tag: str = ""
    strategy_name: str = ""
    
@dataclass
class Position:
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float

__all__ = ["MarketBar", "OrderIntent", "Position"]