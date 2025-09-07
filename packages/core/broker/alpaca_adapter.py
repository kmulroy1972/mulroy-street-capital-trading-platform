import asyncio
import json
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import logging
from decimal import Decimal

import httpx
import websockets
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus, AssetClass
from alpaca.data.live import StockDataStream
from alpaca.data.models import Bar, Trade, Quote

from ..types import OrderIntent, Position, MarketBar

logger = logging.getLogger(__name__)

@dataclass
class AlpacaConfig:
    api_key_id: str
    api_secret_key: str
    base_url: str = "https://api.alpaca.markets"  # Always live
    feed: str = "iex"  # or "sip" for paid data

class AlpacaAdapter:
    def __init__(self, config: AlpacaConfig):
        self.config = config
        
        # Initialize LIVE trading client
        self.trading_client = TradingClient(
            api_key=config.api_key_id,
            secret_key=config.api_secret_key,
            paper=False  # ALWAYS LIVE TRADING
        )
        
        # Initialize WebSocket client for market data
        self.data_stream = StockDataStream(
            api_key=config.api_key_id,
            secret_key=config.api_secret_key,
            feed=config.feed
        )
        
        # Order tracking for idempotency
        self.pending_orders: Dict[str, str] = {}  # client_order_id -> alpaca_order_id
        self.order_callbacks: Dict[str, Any] = {}
        
        # Position cache
        self.positions_cache: Dict[str, Position] = {}
        
        # Callbacks for market data
        self.bar_callbacks: List[Callable] = []
        self.trade_callbacks: List[Callable] = []
        self.quote_callbacks: List[Callable] = []
        
        logger.warning("Alpaca adapter initialized in LIVE TRADING mode")
    
    async def connect(self) -> bool:
        """Connect to Alpaca live trading and start data streams"""
        try:
            # Test connection
            account = self.trading_client.get_account()
            logger.warning(f"Connected to Alpaca LIVE. Account status: {account.status}")
            logger.warning(f"Account equity: ${account.equity}")
            
            # Verify this is a live account
            if hasattr(account, 'trade_suspended_by_user') and account.trade_suspended_by_user:
                logger.error("Trading is suspended on this account")
                return False
            
            # Start market data stream in background
            asyncio.create_task(self._run_data_stream())
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Alpaca LIVE: {e}")
            return False
    
    async def _run_data_stream(self) -> None:
        """Run the market data stream"""
        try:
            @self.data_stream.on_bar
            async def on_bar(data: Bar):
                market_bar = MarketBar(
                    symbol=data.symbol,
                    timestamp=int(data.timestamp.timestamp()),
                    open=float(data.open),
                    high=float(data.high),
                    low=float(data.low),
                    close=float(data.close),
                    volume=float(data.volume)
                )
                for callback in self.bar_callbacks:
                    await callback(market_bar)
            
            @self.data_stream.on_trade
            async def on_trade(data: Trade):
                for callback in self.trade_callbacks:
                    await callback(data)
            
            @self.data_stream.on_quote
            async def on_quote(data: Quote):
                for callback in self.quote_callbacks:
                    await callback(data)
            
            # Run the stream
            self.data_stream.run()
            
        except Exception as e:
            logger.error(f"Market data stream error: {e}")
            # Attempt reconnection
            await asyncio.sleep(5)
            asyncio.create_task(self._run_data_stream())
    
    def subscribe_bars(self, symbols: List[str], callback: Callable) -> None:
        """Subscribe to bar data for symbols"""
        self.bar_callbacks.append(callback)
        self.data_stream.subscribe_bars(*symbols)
        logger.info(f"Subscribed to bars for {symbols}")
    
    def subscribe_trades(self, symbols: List[str], callback: Callable) -> None:
        """Subscribe to trade data for symbols"""
        self.trade_callbacks.append(callback)
        self.data_stream.subscribe_trades(*symbols)
    
    def subscribe_quotes(self, symbols: List[str], callback: Callable) -> None:
        """Subscribe to quote data for symbols"""
        self.quote_callbacks.append(callback)
        self.data_stream.subscribe_quotes(*symbols)
    
    async def get_account(self) -> Dict:
        """Get live account information"""
        try:
            account = self.trading_client.get_account()
            return {
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "portfolio_value": float(account.portfolio_value),
                "pattern_day_trader": account.pattern_day_trader,
                "trading_blocked": account.trading_blocked,
                "account_blocked": account.account_blocked,
                "trade_suspended_by_user": account.trade_suspended_by_user,
                "daytrade_count": account.daytrade_count,
                "daytrading_buying_power": float(account.daytrading_buying_power) if account.daytrading_buying_power else 0,
            }
        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            raise
    
    async def place_order(self, intent: OrderIntent, client_order_id: Optional[str] = None) -> Dict:
        """Place LIVE order with Alpaca"""
        try:
            # Generate client order ID for idempotency
            if not client_order_id:
                client_order_id = f"{intent.strategy_name}_{intent.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            
            # Check if we already have this order
            if client_order_id in self.pending_orders:
                logger.warning(f"Order {client_order_id} already pending")
                return {"status": "duplicate", "client_order_id": client_order_id}
            
            # Log the live order attempt
            logger.warning(f"PLACING LIVE ORDER: {intent.symbol} {intent.side} {intent.qty} shares")
            
            # Create order request based on type
            side = OrderSide.BUY if intent.side == "buy" else OrderSide.SELL
            
            if intent.order_type == "market":
                order_request = MarketOrderRequest(
                    symbol=intent.symbol,
                    qty=intent.qty,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    client_order_id=client_order_id
                )
            elif intent.order_type == "limit":
                if not intent.limit_price:
                    raise ValueError("Limit price required for limit order")
                order_request = LimitOrderRequest(
                    symbol=intent.symbol,
                    qty=intent.qty,
                    side=side,
                    limit_price=intent.limit_price,
                    time_in_force=TimeInForce.DAY,
                    client_order_id=client_order_id
                )
            else:
                raise ValueError(f"Unsupported order type: {intent.order_type}")
            
            # Submit LIVE order
            order = self.trading_client.submit_order(order_request)
            
            # Track order
            self.pending_orders[client_order_id] = order.id
            
            logger.warning(f"LIVE ORDER PLACED: {order.symbol} {order.side} {order.qty} @ {order.order_type} - Order ID: {order.id}")
            
            return {
                "id": order.id,
                "client_order_id": order.client_order_id,
                "symbol": order.symbol,
                "side": order.side.value,
                "qty": float(order.qty),
                "order_type": order.order_type.value,
                "status": order.status.value,
                "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
                "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to place LIVE order: {e}")
            raise
    
    async def get_positions(self) -> List[Position]:
        """Get all current LIVE positions"""
        try:
            positions = self.trading_client.get_all_positions()
            
            result = []
            for pos in positions:
                position = Position(
                    symbol=pos.symbol,
                    qty=float(pos.qty),
                    avg_entry_price=float(pos.avg_entry_price),
                    current_price=float(pos.current_price) if pos.current_price else 0,
                    unrealized_pnl=float(pos.unrealized_pl) if pos.unrealized_pl else 0,
                    realized_pnl=float(pos.realized_pl) if pos.realized_pl else 0
                )
                result.append(position)
                self.positions_cache[pos.symbol] = position
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get LIVE position for specific symbol"""
        try:
            pos = self.trading_client.get_position(symbol)
            if pos:
                return Position(
                    symbol=pos.symbol,
                    qty=float(pos.qty),
                    avg_entry_price=float(pos.avg_entry_price),
                    current_price=float(pos.current_price) if pos.current_price else 0,
                    unrealized_pnl=float(pos.unrealized_pl) if pos.unrealized_pl else 0,
                    realized_pnl=float(pos.realized_pl) if pos.realized_pl else 0
                )
            return None
        except Exception as e:
            if "position does not exist" in str(e).lower():
                return None
            logger.error(f"Failed to get position for {symbol}: {e}")
            raise
    
    async def get_orders(self, status: Optional[str] = None) -> List[Dict]:
        """Get LIVE orders with optional status filter"""
        try:
            request = GetOrdersRequest(
                status=OrderStatus.OPEN if not status else getattr(OrderStatus, status.upper()),
                limit=100,
                nested=False
            )
            
            orders = self.trading_client.get_orders(request)
            
            result = []
            for order in orders:
                result.append({
                    "id": order.id,
                    "client_order_id": order.client_order_id,
                    "symbol": order.symbol,
                    "side": order.side.value,
                    "qty": float(order.qty),
                    "order_type": order.order_type.value,
                    "status": order.status.value,
                    "limit_price": float(order.limit_price) if order.limit_price else None,
                    "stop_price": float(order.stop_price) if order.stop_price else None,
                    "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                    "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                    "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
                    "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                    "canceled_at": order.canceled_at.isoformat() if order.canceled_at else None,
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a specific LIVE order"""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.warning(f"LIVE order {order_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    async def cancel_all_orders(self) -> int:
        """Emergency cancel all LIVE orders"""
        try:
            response = self.trading_client.cancel_orders()
            cancelled_count = len(response)
            logger.warning(f"CANCELLED {cancelled_count} LIVE ORDERS")
            return cancelled_count
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            raise
    
    async def close_position(self, symbol: str) -> Dict:
        """Close a specific LIVE position"""
        try:
            order = self.trading_client.close_position(symbol)
            logger.warning(f"CLOSING LIVE POSITION: {symbol}")
            return {
                "id": order.id,
                "symbol": order.symbol,
                "qty": float(order.qty),
                "side": order.side.value,
            }
        except Exception as e:
            logger.error(f"Failed to close position {symbol}: {e}")
            raise
    
    async def close_all_positions(self) -> List[Dict]:
        """Emergency close all LIVE positions"""
        try:
            orders = self.trading_client.close_all_positions()
            logger.warning(f"CLOSING {len(orders)} LIVE POSITIONS")
            return [
                {
                    "id": order.id,
                    "symbol": order.symbol,
                    "qty": float(order.qty),
                    "side": order.side.value,
                }
                for order in orders
            ]
        except Exception as e:
            logger.error(f"Failed to close all positions: {e}")
            raise
    
    async def get_market_hours(self, date: Optional[datetime] = None) -> Dict:
        """Get market hours for a specific date"""
        try:
            if not date:
                date = datetime.now(timezone.utc)
            
            calendar = self.trading_client.get_calendar(
                start=date.date(),
                end=date.date()
            )[0]
            
            return {
                "date": calendar.date.isoformat(),
                "open": calendar.open.isoformat(),
                "close": calendar.close.isoformat(),
                "is_open": calendar.date == datetime.now(timezone.utc).date(),
            }
        except Exception as e:
            logger.error(f"Failed to get market hours: {e}")
            raise
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        try:
            clock = self.trading_client.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f"Failed to check market status: {e}")
            return False