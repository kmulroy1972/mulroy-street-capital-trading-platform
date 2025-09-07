#!/usr/bin/env python3
"""
Strategy Development Script
Provides tools for developing, testing, and hot-reloading strategies
"""

import asyncio
import argparse
import logging
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from packages.strategies.strategy_loader import StrategyLoader
from packages.core.data.market_data import MarketDataProvider
from packages.core.broker.alpaca_adapter import AlpacaAdapter
from packages.core.types import MarketBar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyDeveloper:
    """Development environment for strategies"""
    
    def __init__(self):
        self.loader = StrategyLoader()
        self.market_data = MarketDataProvider()
        self.broker = AlpacaAdapter()
        
    async def create_strategy(self, name: str, template: str = "momentum"):
        """Create a new strategy from template"""
        strategy_dir = Path(f"packages/strategies/{name}")
        strategy_dir.mkdir(exist_ok=True)
        
        # Create __init__.py
        (strategy_dir / "__init__.py").touch()
        
        # Create strategy.py from template
        template_content = self._get_template(template, name)
        with open(strategy_dir / "strategy.py", "w") as f:
            f.write(template_content)
        
        # Create config.json
        config_content = self._get_default_config(name)
        with open(strategy_dir / "config.json", "w") as f:
            json.dump(config_content, f, indent=4)
        
        logger.info(f"Created strategy: {name} in {strategy_dir}")
        
    def _get_template(self, template: str, name: str) -> str:
        """Get strategy template code"""
        class_name = ''.join(word.capitalize() for word in name.split('_')) + 'Strategy'
        
        if template == "momentum":
            return f'''from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np
from collections import deque

from packages.core.strategies.base import StrategyBase
from packages.core.types import MarketBar, OrderIntent

class {class_name}(StrategyBase):
    """
    {name.replace('_', ' ').title()} Strategy
    Edit this file and save - the engine will hot-reload it!
    """
    
    def __init__(self, config: Dict = None):
        super().__init__(
            name="{name}",
            version="1.0.0"
        )
        
        # Load config or use defaults
        config = config or {{}}
        self.lookback_period = config.get("lookback_period", 20)
        self.signal_threshold = config.get("signal_threshold", 0.02)
        self.position_size = config.get("position_size", 100)
        self.stop_loss_pct = config.get("stop_loss_pct", 0.01)
        self.take_profit_pct = config.get("take_profit_pct", 0.02)
        
        # State that persists across reloads
        self.price_history = {{}}
        self.positions = {{}}
        
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
        
        # TODO: Implement your strategy logic here
        # Example: Simple momentum detection
        prices = list(self.price_history[bar.symbol])
        momentum = (prices[-1] - prices[0]) / prices[0]
        
        # Generate buy signal
        if momentum > self.signal_threshold and bar.symbol not in self.positions:
            self.positions[bar.symbol] = {{
                "entry_price": bar.close,
                "qty": self.position_size,
                "entry_time": datetime.now()
            }}
            
            return OrderIntent(
                symbol=bar.symbol,
                side="buy",
                order_type="limit",
                qty=self.position_size,
                limit_price=bar.close * 1.001,
                strategy_name=self.name
            )
        
        # Generate sell signal
        elif bar.symbol in self.positions:
            position = self.positions[bar.symbol]
            pnl_pct = (bar.close - position["entry_price"]) / position["entry_price"]
            
            if pnl_pct >= self.take_profit_pct or pnl_pct <= -self.stop_loss_pct:
                del self.positions[bar.symbol]
                
                return OrderIntent(
                    symbol=bar.symbol,
                    side="sell",
                    order_type="market",
                    qty=position["qty"],
                    strategy_name=self.name
                )
        
        return None
    
    def get_state(self) -> Dict:
        """Get strategy state for persistence"""
        return {{
            "price_history": {{k: list(v) for k, v in self.price_history.items()}},
            "positions": self.positions
        }}
    
    def set_state(self, state: Dict) -> None:
        """Restore strategy state after reload"""
        if "price_history" in state:
            self.price_history = {{
                k: deque(v, maxlen=self.lookback_period) 
                for k, v in state["price_history"].items()
            }}
        if "positions" in state:
            self.positions = state["positions"]
'''
        
        return "# Template not found"
    
    def _get_default_config(self, name: str) -> Dict:
        """Get default strategy configuration"""
        return {
            "enabled": True,
            "mode": "shadow",
            "parameters": {
                "lookback_period": 20,
                "signal_threshold": 0.02,
                "position_size": 100,
                "stop_loss_pct": 0.01,
                "take_profit_pct": 0.02,
                "max_positions": 3,
                "trade_symbols": ["SPY", "QQQ", "AAPL"]
            },
            "risk_limits": {
                "max_position_value": 5000,
                "max_daily_loss": 200,
                "max_trades_per_day": 10
            },
            "schedule": {
                "start_time": "09:30",
                "end_time": "15:30",
                "days": ["mon", "tue", "wed", "thu", "fri"]
            }
        }
    
    async def backtest_strategy(self, name: str, start_date: str, end_date: str, symbols: List[str]):
        """Run a backtest for a strategy"""
        logger.info(f"Starting backtest for {name}: {start_date} to {end_date}")
        
        strategy = self.loader.load_strategy(name)
        if not strategy:
            logger.error(f"Failed to load strategy: {name}")
            return
        
        # TODO: Implement backtesting logic
        # This would fetch historical data and run the strategy
        logger.info("Backtesting implementation pending...")
    
    async def test_strategy(self, name: str, symbols: List[str], duration_minutes: int = 30):
        """Test strategy with live data in shadow mode"""
        logger.info(f"Testing strategy {name} for {duration_minutes} minutes")
        
        strategy = self.loader.load_strategy(name)
        if not strategy:
            logger.error(f"Failed to load strategy: {name}")
            return
        
        # Subscribe to market data
        await self.market_data.connect()
        
        signals_generated = 0
        start_time = datetime.now()
        
        try:
            while (datetime.now() - start_time).seconds < duration_minutes * 60:
                # Get latest bars
                for symbol in symbols:
                    bar = await self.market_data.get_latest_bar(symbol)
                    if bar:
                        signal = await strategy.on_bar(bar)
                        if signal:
                            signals_generated += 1
                            logger.info(f"Signal generated: {signal.side} {signal.qty} {signal.symbol}")
                
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Test stopped by user")
        
        finally:
            await self.market_data.disconnect()
            logger.info(f"Test completed. Generated {signals_generated} signals")
    
    def watch_strategies(self):
        """Start file watcher for hot-reloading"""
        def on_reload(strategy_name):
            logger.info(f"🔥 Strategy {strategy_name} hot-reloaded!")
        
        self.loader.start_file_watcher(callback=on_reload)
        logger.info("Strategy file watcher started. Press Ctrl+C to stop.")
        
        try:
            while True:
                asyncio.sleep(1)
        except KeyboardInterrupt:
            self.loader.stop_file_watcher()
            logger.info("File watcher stopped")

async def main():
    parser = argparse.ArgumentParser(description="Strategy Development Tools")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create strategy command
    create_parser = subparsers.add_parser('create', help='Create new strategy')
    create_parser.add_argument('name', help='Strategy name (e.g., my_strategy)')
    create_parser.add_argument('--template', default='momentum', help='Template to use')
    
    # Test strategy command
    test_parser = subparsers.add_parser('test', help='Test strategy with live data')
    test_parser.add_argument('name', help='Strategy name to test')
    test_parser.add_argument('--symbols', nargs='+', default=['SPY'], help='Symbols to test')
    test_parser.add_argument('--duration', type=int, default=30, help='Test duration in minutes')
    
    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run strategy backtest')
    backtest_parser.add_argument('name', help='Strategy name to backtest')
    backtest_parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    backtest_parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    backtest_parser.add_argument('--symbols', nargs='+', default=['SPY'], help='Symbols to backtest')
    
    # Watch command
    watch_parser = subparsers.add_parser('watch', help='Watch strategies for changes')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all strategies')
    
    args = parser.parse_args()
    developer = StrategyDeveloper()
    
    if args.command == 'create':
        await developer.create_strategy(args.name, args.template)
        
    elif args.command == 'test':
        await developer.test_strategy(args.name, args.symbols, args.duration)
        
    elif args.command == 'backtest':
        await developer.backtest_strategy(args.name, args.start, args.end, args.symbols)
        
    elif args.command == 'watch':
        developer.watch_strategies()
        
    elif args.command == 'list':
        strategies = developer.loader.load_all_strategies()
        print(f"\\nFound {len(strategies)} strategies:")
        for name, strategy in strategies.items():
            print(f"  📈 {name} v{strategy.version}")
        print()
        
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())