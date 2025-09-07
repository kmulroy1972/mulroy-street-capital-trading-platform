from typing import List, Dict, Optional
from collections import deque
import numpy as np
from datetime import datetime
import logging

from packages.core.strategies.base import StrategyBase
from packages.core.types import MarketBar, OrderIntent

logger = logging.getLogger(__name__)

class MeanReversionStrategy(StrategyBase):
    """
    Mean Reversion Strategy
    Buys when price is below moving average by threshold
    Sells when price returns to mean or hits stop loss
    """
    
    def __init__(self, config: Dict = None):
        super().__init__(
            name="mean_reversion",
            version="2.0.0"
        )
        
        config = config or {}
        
        # Strategy parameters (optimizable)
        self.lookback_period = config.get("lookback_period", 20)
        self.entry_threshold = config.get("entry_threshold", 0.02)  # 2% below MA
        self.exit_threshold = config.get("exit_threshold", 0.01)   # 1% above MA
        self.stop_loss = config.get("stop_loss", 0.03)            # 3% stop loss
        self.position_size = config.get("position_size", 100)
        
        # State
        self.price_history = {}
        self.moving_averages = {}
        self.positions = {}
        self.entry_prices = {}
        
    def warmup(self, bars: List[MarketBar]) -> None:
        """Initialize with historical data"""
        for bar in bars:
            if bar.symbol not in self.price_history:
                self.price_history[bar.symbol] = deque(maxlen=self.lookback_period)
            self.price_history[bar.symbol].append(bar.close)
            
            # Calculate initial moving average
            if len(self.price_history[bar.symbol]) == self.lookback_period:
                self.moving_averages[bar.symbol] = np.mean(self.price_history[bar.symbol])
    
    async def on_bar(self, bar: MarketBar) -> Optional[OrderIntent]:
        """Generate trading signals"""
        # Update price history
        if bar.symbol not in self.price_history:
            self.price_history[bar.symbol] = deque(maxlen=self.lookback_period)
        self.price_history[bar.symbol].append(bar.close)
        
        # Need enough history
        if len(self.price_history[bar.symbol]) < self.lookback_period:
            return None
        
        # Calculate moving average
        ma = np.mean(self.price_history[bar.symbol])
        self.moving_averages[bar.symbol] = ma
        
        # Calculate deviation from mean
        deviation = (bar.close - ma) / ma
        
        # Check for entry signal
        if bar.symbol not in self.positions:
            if deviation < -self.entry_threshold:  # Price below MA by threshold
                # Buy signal
                intent = OrderIntent(
                    symbol=bar.symbol,
                    side="buy",
                    order_type="market",
                    qty=self.position_size,
                    strategy_name=self.name
                )
                
                # Track position
                self.positions[bar.symbol] = self.position_size
                self.entry_prices[bar.symbol] = bar.close
                
                return intent
                
        # Check for exit signal
        else:
            entry_price = self.entry_prices[bar.symbol]
            pnl_pct = (bar.close - entry_price) / entry_price
            
            # Exit conditions
            should_exit = False
            exit_reason = ""
            
            if deviation > self.exit_threshold:  # Price above MA by threshold
                should_exit = True
                exit_reason = "mean_reversion"
            elif pnl_pct <= -self.stop_loss:  # Stop loss hit
                should_exit = True
                exit_reason = "stop_loss"
            elif pnl_pct >= self.exit_threshold * 2:  # Take profit
                should_exit = True
                exit_reason = "take_profit"
            
            if should_exit:
                # Sell signal
                intent = OrderIntent(
                    symbol=bar.symbol,
                    side="sell",
                    order_type="market",
                    qty=self.positions[bar.symbol],
                    strategy_name=self.name
                )
                
                # Clear position
                del self.positions[bar.symbol]
                del self.entry_prices[bar.symbol]
                
                return intent
        
        return None
    
    async def on_timer(self, timestamp: int) -> List[OrderIntent]:
        """No timer-based actions for this strategy"""
        return []
    
    def get_state(self) -> Dict:
        """Get strategy state for persistence"""
        return {
            "price_history": {k: list(v) for k, v in self.price_history.items()},
            "moving_averages": self.moving_averages,
            "positions": self.positions,
            "entry_prices": self.entry_prices
        }
    
    def set_state(self, state: Dict) -> None:
        """Restore strategy state"""
        if "price_history" in state:
            self.price_history = {
                k: deque(v, maxlen=self.lookback_period) 
                for k, v in state["price_history"].items()
            }
        if "moving_averages" in state:
            self.moving_averages = state["moving_averages"]
        if "positions" in state:
            self.positions = state["positions"]
        if "entry_prices" in state:
            self.entry_prices = state["entry_prices"]
            
        logger.info(f"State restored: {len(self.positions)} positions, {len(self.price_history)} symbols tracked")