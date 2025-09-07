import asyncio
from typing import Dict, List, Callable, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging

from ..types import MarketBar

logger = logging.getLogger(__name__)

@dataclass
class BarAggregator:
    timeframe: int  # in seconds
    bars: deque = field(default_factory=lambda: deque(maxlen=1000))
    current_bar: Optional[MarketBar] = None
    last_bar_time: Optional[datetime] = None
    
    def add_trade(self, symbol: str, price: float, volume: float, timestamp: int) -> Optional[MarketBar]:
        """Add a trade and return completed bar if timeframe boundary crossed"""
        trade_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        bar_time = self._get_bar_time(trade_time)
        
        # If this is a new bar period, complete the current bar
        completed_bar = None
        if self.current_bar and self.last_bar_time and bar_time != self.last_bar_time:
            completed_bar = self.current_bar
            self.bars.append(completed_bar)
            self.current_bar = None
        
        # Initialize or update current bar
        if not self.current_bar:
            self.current_bar = MarketBar(
                symbol=symbol,
                timestamp=int(bar_time.timestamp()),
                open=price,
                high=price,
                low=price,
                close=price,
                volume=volume
            )
        else:
            self.current_bar.high = max(self.current_bar.high, price)
            self.current_bar.low = min(self.current_bar.low, price)
            self.current_bar.close = price
            self.current_bar.volume += volume
        
        self.last_bar_time = bar_time
        return completed_bar
    
    def _get_bar_time(self, timestamp: datetime) -> datetime:
        """Get the bar start time for given timestamp"""
        seconds_since_epoch = int(timestamp.timestamp())
        bar_start = (seconds_since_epoch // self.timeframe) * self.timeframe
        return datetime.fromtimestamp(bar_start, tz=timezone.utc)
    
    def get_latest_bars(self, count: int = 100) -> List[MarketBar]:
        """Get the latest completed bars"""
        return list(self.bars)[-count:]

class MarketDataHandler:
    def __init__(self):
        # Symbol -> timeframe -> aggregator
        self.aggregators: Dict[str, Dict[int, BarAggregator]] = defaultdict(dict)
        
        # Callbacks for completed bars
        self.bar_callbacks: List[Callable[[MarketBar], None]] = []
        
        # Standard timeframes (in seconds)
        self.timeframes = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "1d": 86400
        }
        
        logger.info("Market data handler initialized")
    
    def subscribe_symbol(self, symbol: str, timeframes: Optional[List[str]] = None) -> None:
        """Subscribe to bar aggregation for a symbol"""
        if not timeframes:
            timeframes = ["1m", "5m", "15m"]
        
        for tf_name in timeframes:
            if tf_name not in self.timeframes:
                logger.warning(f"Unknown timeframe: {tf_name}")
                continue
            
            timeframe_seconds = self.timeframes[tf_name]
            if timeframe_seconds not in self.aggregators[symbol]:
                self.aggregators[symbol][timeframe_seconds] = BarAggregator(timeframe_seconds)
                logger.info(f"Subscribed {symbol} to {tf_name} bars")
    
    def add_bar_callback(self, callback: Callable[[MarketBar], None]) -> None:
        """Add callback for completed bars"""
        self.bar_callbacks.append(callback)
    
    async def handle_trade(self, trade_data: Dict) -> None:
        """Process incoming trade data"""
        try:
            symbol = trade_data.get("symbol", "")
            price = float(trade_data.get("price", 0))
            volume = float(trade_data.get("size", 0))
            timestamp = trade_data.get("timestamp", datetime.now(timezone.utc).timestamp())
            
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()
            elif isinstance(timestamp, datetime):
                timestamp = timestamp.timestamp()
            
            # Process for all subscribed timeframes
            if symbol in self.aggregators:
                for timeframe_seconds, aggregator in self.aggregators[symbol].items():
                    completed_bar = aggregator.add_trade(symbol, price, volume, int(timestamp))
                    
                    if completed_bar:
                        logger.debug(f"Completed {timeframe_seconds}s bar for {symbol}: "
                                   f"O:{completed_bar.open:.2f} H:{completed_bar.high:.2f} "
                                   f"L:{completed_bar.low:.2f} C:{completed_bar.close:.2f} V:{completed_bar.volume}")
                        
                        # Notify callbacks
                        for callback in self.bar_callbacks:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(completed_bar)
                                else:
                                    callback(completed_bar)
                            except Exception as e:
                                logger.error(f"Error in bar callback: {e}")
                                
        except Exception as e:
            logger.error(f"Error handling trade data: {e}")
    
    async def handle_bar(self, bar: MarketBar) -> None:
        """Process incoming bar data directly"""
        try:
            # Notify callbacks for direct bar data
            for callback in self.bar_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(bar)
                    else:
                        callback(bar)
                except Exception as e:
                    logger.error(f"Error in bar callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error handling bar data: {e}")
    
    def get_bars(self, symbol: str, timeframe: str, count: int = 100) -> List[MarketBar]:
        """Get historical bars for symbol and timeframe"""
        if timeframe not in self.timeframes:
            return []
        
        timeframe_seconds = self.timeframes[timeframe]
        if symbol in self.aggregators and timeframe_seconds in self.aggregators[symbol]:
            return self.aggregators[symbol][timeframe_seconds].get_latest_bars(count)
        
        return []
    
    def get_current_bar(self, symbol: str, timeframe: str) -> Optional[MarketBar]:
        """Get the current (incomplete) bar for symbol and timeframe"""
        if timeframe not in self.timeframes:
            return None
        
        timeframe_seconds = self.timeframes[timeframe]
        if symbol in self.aggregators and timeframe_seconds in self.aggregators[symbol]:
            return self.aggregators[symbol][timeframe_seconds].current_bar
        
        return None
    
    def get_stats(self) -> Dict:
        """Get handler statistics"""
        total_symbols = len(self.aggregators)
        total_timeframes = sum(len(tfs) for tfs in self.aggregators.values())
        
        symbol_stats = {}
        for symbol, timeframes in self.aggregators.items():
            symbol_stats[symbol] = {
                tf: len(agg.bars) for tf, agg in timeframes.items()
            }
        
        return {
            "total_symbols": total_symbols,
            "total_timeframes": total_timeframes,
            "symbols": symbol_stats,
            "callbacks_registered": len(self.bar_callbacks)
        }

# Global instance
market_data_handler = MarketDataHandler()