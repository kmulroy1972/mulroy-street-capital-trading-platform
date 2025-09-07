from abc import ABC, abstractmethod
from typing import List, Iterable, Literal
from ..types import MarketBar, OrderIntent

class Strategy(ABC):
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.enabled = False
        self.mode: Literal["disabled", "shadow", "canary", "enabled"] = "disabled"
        
    @abstractmethod
    def warmup(self, bars: Iterable[MarketBar]) -> None:
        """Load historical data for indicators"""
        pass
    
    @abstractmethod
    def on_bar(self, bar: MarketBar) -> List[OrderIntent]:
        """React to new market data"""
        pass
    
    @abstractmethod
    def on_timer(self, timestamp: int) -> List[OrderIntent]:
        """Periodic actions (rebalancing, etc)"""
        pass