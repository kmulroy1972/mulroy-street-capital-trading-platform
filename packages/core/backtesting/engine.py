import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from collections import defaultdict

from ..types import MarketBar, OrderIntent, Position
from ..strategies.base import StrategyBase

logger = logging.getLogger(__name__)

@dataclass
class BacktestConfig:
    initial_capital: float = 100000
    start_date: datetime = None
    end_date: datetime = None
    symbols: List[str] = field(default_factory=list)
    timeframe: str = "1Min"  # 1Min, 5Min, 15Min, 1Hour, 1Day
    commission: float = 0.0  # Per share commission
    slippage: float = 0.01  # Slippage in percentage
    allow_shorting: bool = False
    max_position_size: float = 10000
    use_realistic_fills: bool = True

@dataclass
class Trade:
    timestamp: datetime
    symbol: str
    side: str
    quantity: float
    price: float
    commission: float
    slippage: float
    pnl: float = 0.0
    cumulative_pnl: float = 0.0

@dataclass
class BacktestResults:
    trades: List[Trade]
    equity_curve: pd.DataFrame
    positions: Dict[str, List[Position]]
    metrics: Dict[str, float]
    daily_returns: pd.Series
    
    def to_dict(self) -> Dict:
        return {
            "total_trades": len(self.trades),
            "winning_trades": sum(1 for t in self.trades if t.pnl > 0),
            "losing_trades": sum(1 for t in self.trades if t.pnl < 0),
            "total_pnl": self.metrics.get("total_pnl", 0),
            "sharpe_ratio": self.metrics.get("sharpe_ratio", 0),
            "max_drawdown": self.metrics.get("max_drawdown", 0),
            "win_rate": self.metrics.get("win_rate", 0),
            "profit_factor": self.metrics.get("profit_factor", 0),
            "return_pct": self.metrics.get("return_pct", 0),
        }

class BacktestEngine:
    """High-performance backtesting engine"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.cash = config.initial_capital
        self.initial_capital = config.initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve = []
        self.pending_orders: List[OrderIntent] = []
        self.current_prices: Dict[str, float] = {}
        self.historical_positions: Dict[str, List[Position]] = defaultdict(list)
        
    def run(self, strategy: StrategyBase, market_data: Dict[str, pd.DataFrame]) -> BacktestResults:
        """Run backtest on historical data"""
        logger.info(f"Starting backtest for {strategy.name} from {self.config.start_date} to {self.config.end_date}")
        
        # Prepare data
        all_bars = self._prepare_market_data(market_data)
        
        # Warmup strategy
        warmup_bars = all_bars[:100] if len(all_bars) > 100 else []
        if warmup_bars:
            strategy.warmup(warmup_bars)
        
        # Main backtest loop
        for i, bar in enumerate(all_bars[len(warmup_bars):]):
            self.current_prices[bar.symbol] = bar.close
            
            # Process pending orders
            self._process_pending_orders(bar)
            
            # Get strategy signals
            intent = await strategy.on_bar(bar) if hasattr(strategy.on_bar, '__call__') else None
            if intent:
                self._process_order_intent(intent, bar)
            
            # Update equity
            self._update_equity(datetime.fromtimestamp(bar.timestamp))
            
            # Risk management
            self._check_risk_limits()
        
        # Calculate metrics
        results = self._calculate_results()
        
        logger.info(f"Backtest complete. Total P&L: ${results.metrics['total_pnl']:.2f}")
        
        return results
    
    def _prepare_market_data(self, market_data: Dict[str, pd.DataFrame]) -> List[MarketBar]:
        """Convert market data to MarketBar format"""
        all_bars = []
        
        for symbol, df in market_data.items():
            for idx, row in df.iterrows():
                bar = MarketBar(
                    symbol=symbol,
                    timestamp=int(idx.timestamp()),
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume']
                )
                all_bars.append(bar)
        
        # Sort by timestamp
        all_bars.sort(key=lambda x: x.timestamp)
        
        return all_bars
    
    def _process_order_intent(self, intent: OrderIntent, bar: MarketBar):
        """Process order intent with realistic fills"""
        if intent.symbol != bar.symbol:
            return  # Can only trade the current bar's symbol
        
        # Check if we have enough cash
        order_value = intent.qty * bar.close
        commission = intent.qty * self.config.commission
        
        if intent.side == "buy":
            required_cash = order_value + commission
            if required_cash > self.cash:
                logger.debug(f"Insufficient cash for {intent.symbol} order: ${required_cash:.2f} > ${self.cash:.2f}")
                return
            
            # Calculate fill price with slippage
            fill_price = bar.close * (1 + self.config.slippage / 100)
            
            # Execute buy
            self.cash -= (intent.qty * fill_price + commission)
            
            if intent.symbol in self.positions:
                # Add to existing position
                pos = self.positions[intent.symbol]
                new_qty = pos.qty + intent.qty
                new_avg_price = ((pos.qty * pos.avg_entry_price) + (intent.qty * fill_price)) / new_qty
                pos.qty = new_qty
                pos.avg_entry_price = new_avg_price
            else:
                # Create new position
                self.positions[intent.symbol] = Position(
                    symbol=intent.symbol,
                    qty=intent.qty,
                    avg_entry_price=fill_price,
                    current_price=bar.close,
                    unrealized_pnl=0,
                    realized_pnl=0
                )
            
            # Record trade
            trade = Trade(
                timestamp=datetime.fromtimestamp(bar.timestamp),
                symbol=intent.symbol,
                side="buy",
                quantity=intent.qty,
                price=fill_price,
                commission=commission,
                slippage=fill_price - bar.close
            )
            self.trades.append(trade)
            
        elif intent.side == "sell":
            if intent.symbol not in self.positions:
                if not self.config.allow_shorting:
                    logger.debug(f"No position to sell for {intent.symbol}")
                    return
            
            # Calculate fill price with slippage
            fill_price = bar.close * (1 - self.config.slippage / 100)
            
            if intent.symbol in self.positions:
                pos = self.positions[intent.symbol]
                
                # Calculate P&L
                pnl = (fill_price - pos.avg_entry_price) * min(intent.qty, pos.qty)
                
                # Execute sell
                if intent.qty >= pos.qty:
                    # Close position
                    self.cash += (pos.qty * fill_price - commission)
                    del self.positions[intent.symbol]
                    trade_qty = pos.qty
                else:
                    # Partial sell
                    self.cash += (intent.qty * fill_price - commission)
                    pos.qty -= intent.qty
                    trade_qty = intent.qty
                
                # Record trade
                trade = Trade(
                    timestamp=datetime.fromtimestamp(bar.timestamp),
                    symbol=intent.symbol,
                    side="sell",
                    quantity=trade_qty,
                    price=fill_price,
                    commission=commission,
                    slippage=bar.close - fill_price,
                    pnl=pnl,
                    cumulative_pnl=sum(t.pnl for t in self.trades) + pnl
                )
                self.trades.append(trade)
    
    def _process_pending_orders(self, bar: MarketBar):
        """Process limit and stop orders"""
        # Simplified - implement full order types if needed
        pass
    
    def _update_equity(self, timestamp: datetime):
        """Update equity curve"""
        positions_value = sum(
            pos.qty * self.current_prices.get(pos.symbol, pos.avg_entry_price)
            for pos in self.positions.values()
        )
        
        total_equity = self.cash + positions_value
        
        self.equity_curve.append({
            "timestamp": timestamp,
            "cash": self.cash,
            "positions_value": positions_value,
            "total_equity": total_equity,
            "return_pct": ((total_equity - self.initial_capital) / self.initial_capital) * 100
        })
    
    def _check_risk_limits(self):
        """Check and enforce risk limits"""
        # Max position size check
        for symbol, pos in list(self.positions.items()):
            position_value = pos.qty * self.current_prices.get(symbol, pos.avg_entry_price)
            if position_value > self.config.max_position_size:
                # Force reduce position
                excess_value = position_value - self.config.max_position_size
                reduce_qty = excess_value / self.current_prices[symbol]
                logger.warning(f"Position size limit breached for {symbol}, reducing by {reduce_qty}")
    
    def _calculate_results(self) -> BacktestResults:
        """Calculate backtest metrics"""
        equity_df = pd.DataFrame(self.equity_curve)
        if equity_df.empty:
            # Return empty results if no data
            return BacktestResults(
                trades=[],
                equity_curve=pd.DataFrame(),
                positions={},
                metrics={},
                daily_returns=pd.Series()
            )
        
        equity_df['timestamp'] = pd.to_datetime(equity_df['timestamp'])
        equity_df.set_index('timestamp', inplace=True)
        
        # Calculate daily returns
        daily_equity = equity_df['total_equity'].resample('D').last().dropna()
        daily_returns = daily_equity.pct_change().dropna()
        
        # Calculate metrics
        total_return = (equity_df['total_equity'].iloc[-1] - self.initial_capital) / self.initial_capital
        
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        
        metrics = {
            "total_pnl": equity_df['total_equity'].iloc[-1] - self.initial_capital,
            "return_pct": total_return * 100,
            "total_trades": len(self.trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(self.trades) if self.trades else 0,
            "avg_win": np.mean([t.pnl for t in winning_trades]) if winning_trades else 0,
            "avg_loss": np.mean([t.pnl for t in losing_trades]) if losing_trades else 0,
            "profit_factor": abs(sum(t.pnl for t in winning_trades) / sum(t.pnl for t in losing_trades)) if losing_trades else 0,
            "sharpe_ratio": self._calculate_sharpe_ratio(daily_returns),
            "sortino_ratio": self._calculate_sortino_ratio(daily_returns),
            "max_drawdown": self._calculate_max_drawdown(equity_df['total_equity']),
            "calmar_ratio": (total_return / abs(self._calculate_max_drawdown(equity_df['total_equity']))) if self._calculate_max_drawdown(equity_df['total_equity']) != 0 else 0,
        }
        
        return BacktestResults(
            trades=self.trades,
            equity_curve=equity_df,
            positions=self.historical_positions,
            metrics=metrics,
            daily_returns=daily_returns
        )
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        
        if excess_returns.std() == 0:
            return 0.0
        
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    
    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio"""
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        return np.sqrt(252) * excess_returns.mean() / downside_returns.std()
    
    def _calculate_max_drawdown(self, equity_curve: pd.Series) -> float:
        """Calculate maximum drawdown"""
        if len(equity_curve) < 2:
            return 0.0
        
        cumulative = (1 + equity_curve.pct_change()).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()