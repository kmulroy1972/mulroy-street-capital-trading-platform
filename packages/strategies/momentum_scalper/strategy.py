from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np
from collections import deque

from packages.core.strategies.base import StrategyBase
from packages.core.types import MarketBar, OrderIntent

class MomentumScalperStrategy(StrategyBase):
    """
    Example momentum scalping strategy that can be modified on the fly
    Edit this file and save - the engine will hot-reload it!
    """
    
    def __init__(self, config: Dict = None):
        super().__init__(
            name="momentum_scalper",
            version="1.0.0"
        )
        
        # Load config or use defaults
        config = config or {}
        self.lookback_period = config.get("lookback_period", 20)
        self.momentum_threshold = config.get("momentum_threshold", 0.02)
        self.position_size = config.get("position_size", 100)
        self.stop_loss_pct = config.get("stop_loss_pct", 0.01)
        self.take_profit_pct = config.get("take_profit_pct", 0.02)
        
        # State that persists across reloads
        self.price_history = {}
        self.positions = {}
        self.pending_orders = {}
        
    def warmup(self, bars: List[MarketBar]) -> None:
        """Initialize with historical data"""
        for bar in bars:
            if bar.symbol not in self.price_history:
                self.price_history[bar.symbol] = deque(maxlen=self.lookback_period)
            self.price_history[bar.symbol].append(bar.close)
    
    async def on_bar(self, bar: MarketBar) -> Optional[OrderIntent]:
        """Generate trading signals on new bar"""
        # Update price history
        if bar.symbol not in self.price_history:
            self.price_history[bar.symbol] = deque(maxlen=self.lookback_period)
        self.price_history[bar.symbol].append(bar.close)
        
        # Need enough history
        if len(self.price_history[bar.symbol]) < self.lookback_period:
            return None
        
        # Calculate momentum
        prices = list(self.price_history[bar.symbol])
        momentum = (prices[-1] - prices[0]) / prices[0]
        
        # Generate signals
        if momentum > self.momentum_threshold and bar.symbol not in self.positions:
            # Buy signal
            intent = OrderIntent(
                symbol=bar.symbol,
                side="buy",
                order_type="limit",
                qty=self.position_size,
                limit_price=bar.close * 1.001,  # Slight premium to ensure fill
                strategy_name=self.name
            )
            self.positions[bar.symbol] = {
                "entry_price": bar.close,
                "qty": self.position_size,
                "entry_time": datetime.now()
            }
            return intent
            
        elif bar.symbol in self.positions:
            position = self.positions[bar.symbol]
            pnl_pct = (bar.close - position["entry_price"]) / position["entry_price"]
            
            # Check exit conditions
            if pnl_pct >= self.take_profit_pct or pnl_pct <= -self.stop_loss_pct:
                # Exit signal
                intent = OrderIntent(
                    symbol=bar.symbol,
                    side="sell",
                    order_type="market",
                    qty=position["qty"],
                    strategy_name=self.name
                )
                del self.positions[bar.symbol]
                return intent
        
        return None
    
    async def on_timer(self, timestamp: int) -> List[OrderIntent]:
        """Check for time-based exits"""
        intents = []
        current_time = datetime.fromtimestamp(timestamp)
        
        # Close positions older than 30 minutes
        for symbol, position in list(self.positions.items()):
            if current_time - position["entry_time"] > timedelta(minutes=30):
                intent = OrderIntent(
                    symbol=symbol,
                    side="sell",
                    order_type="market",
                    qty=position["qty"],
                    strategy_name=self.name
                )
                intents.append(intent)
                del self.positions[symbol]
        
        return intents
    
    def get_state(self) -> Dict:
        """Get strategy state for persistence"""
        return {
            "price_history": {k: list(v) for k, v in self.price_history.items()},
            "positions": self.positions,
            "pending_orders": self.pending_orders
        }
    
    def set_state(self, state: Dict) -> None:
        """Restore strategy state after reload"""
        if "price_history" in state:
            self.price_history = {
                k: deque(v, maxlen=self.lookback_period) 
                for k, v in state["price_history"].items()
            }
        if "positions" in state:
            self.positions = state["positions"]
        if "pending_orders" in state:
            self.pending_orders = state["pending_orders"]
        
        logger.info(f"State restored: {len(self.positions)} positions, {len(self.price_history)} symbols tracked")