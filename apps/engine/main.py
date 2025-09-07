import asyncio
import signal
import sys
from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, List, Optional
from enum import Enum
import json

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import redis.asyncio as redis
import asyncpg

from config import EngineConfig
from packages.core.broker.alpaca_adapter import AlpacaAdapter, AlpacaConfig
from packages.core.market.data_handler import market_data_handler
from packages.core.risk.risk_manager import RiskManager, RiskLimits
from packages.core.types import MarketBar, OrderIntent, Position
from packages.core.strategies.base import StrategyBase
from packages.core.monitoring.monitor import TradingMonitor, AlertSeverity
from packages.core.monitoring.notifier import AlertNotifier, WebhookChannel
from packages.core.monitoring.logging_config import setup_logging

# Setup structured logging
logger = setup_logging(log_level="INFO", log_dir="logs")

class StrategyMode(Enum):
    DISABLED = "disabled"
    SHADOW = "shadow"      # Log intents only, no orders
    CANARY = "canary"      # Place small test orders
    ENABLED = "enabled"    # Full LIVE trading

class TradingEngine:
    def __init__(self, config: EngineConfig):
        self.config = config
        self.running = False
        self.scheduler = AsyncIOScheduler()
        self.strategies: Dict[str, StrategyBase] = {}
        self.strategy_modes: Dict[str, StrategyMode] = {}
        
        # Initialize LIVE trading components
        logger.warning("=" * 50)
        logger.warning("INITIALIZING LIVE TRADING ENGINE")
        logger.warning("=" * 50)
        
        self.alpaca = AlpacaAdapter(AlpacaConfig(
            api_key_id=config.apca_api_key_id.get_secret_value(),
            api_secret_key=config.apca_api_secret_key.get_secret_value(),
            base_url=config.apca_base_url
        ))
        
        self.risk_manager = RiskManager(RiskLimits(
            daily_loss_limit=config.daily_loss_limit,
            max_position_size=config.max_position_size,
            max_portfolio_heat=0.02,
            max_correlation=0.7,
            per_trade_stop_pct=config.stop_loss_percentage / 100
        ))
        
        # Trading state
        self.trading_enabled = False  # Start disabled for safety
        self.positions: Dict[str, Position] = {}
        
        # Initialize monitoring components
        self.redis = None  # Will be set in run()
        self.monitor = None
        self.notifier = AlertNotifier()
        self.pending_orders: List[Dict] = []
        
    async def start(self) -> None:
        """Start the LIVE trading engine"""
        logger.warning(f"Starting LIVE engine {self.config.engine_id}")
        logger.warning(f"Daily loss limit: ${self.config.daily_loss_limit}")
        logger.warning(f"Max position size: ${self.config.max_position_size}")
        
        if self.config.require_confirmation:
            logger.warning("=" * 50)
            logger.warning("LIVE TRADING ENGINE STARTUP")
            logger.warning("Type 'CONFIRM' to start live trading:")
            confirmation = input()
            if confirmation != "CONFIRM":
                logger.error("Startup cancelled - confirmation not received")
                sys.exit(1)
        
        self.running = True
        
        try:
            # Connect to services
            await self._connect_services()
            
            # Connect to Alpaca LIVE
            connected = await self.alpaca.connect()
            if not connected:
                logger.error("Failed to connect to Alpaca LIVE")
                sys.exit(1)
            
            # Get and log account info
            account = await self.alpaca.get_account()
            logger.warning(f"LIVE ACCOUNT - Equity: ${account['equity']:.2f}, Cash: ${account['cash']:.2f}")
            
            # Subscribe to symbols
            await self._setup_market_data()
            
            # Load strategies
            await self._load_strategies()
            
            # Schedule tasks
            self._schedule_tasks()
            
            # Start command listener
            asyncio.create_task(self._listen_for_commands())
            
            logger.warning("LIVE TRADING ENGINE STARTED - Trading is DISABLED by default")
            logger.warning("Enable trading via admin API when ready")
            
            # Main loop
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Engine startup failed: {e}", exc_info=True)
            await self.shutdown()
            raise
    
    async def _connect_services(self) -> None:
        """Connect to Redis and Postgres"""
        self.redis = await redis.from_url(self.config.redis_url)
        self.db = await asyncpg.connect(self.config.database_url.get_secret_value())
        
        # Initialize monitoring
        self.monitor = TradingMonitor(self.redis)
        
        # Setup alert notifier with Discord if configured
        discord_webhook = self.config.discord_webhook if hasattr(self.config, 'discord_webhook') else None
        if discord_webhook:
            discord = WebhookChannel(discord_webhook, "discord")
            self.notifier.add_channel(discord, AlertSeverity.WARNING)
        
        # Register alert handler
        self.monitor.add_alert_handler(self.notifier.notify)
        
        logger.info("Connected to Redis and Postgres with monitoring enabled")
    
    async def _setup_market_data(self) -> None:
        """Setup market data subscriptions"""
        # Get watchlist from config or database
        symbols = ["SPY", "QQQ", "AAPL", "GOOGL", "MSFT", "TSLA"]  # Example symbols
        
        # Subscribe to Alpaca market data
        self.alpaca.subscribe_bars(symbols, self._on_alpaca_bar)
        
        # Setup internal bar aggregation
        for symbol in symbols:
            market_data_handler.subscribe_symbol(symbol, ["1m", "5m", "15m"])
        
        market_data_handler.add_bar_callback(self._on_market_bar)
        
        logger.info(f"Subscribed to market data for {symbols}")
    
    async def _on_alpaca_bar(self, bar: MarketBar) -> None:
        """Handle incoming bar from Alpaca"""
        await market_data_handler.handle_bar(bar)
    
    async def _on_market_bar(self, bar: MarketBar) -> None:
        """Handle aggregated market bar"""
        # Log bar to database
        await self._log_market_bar(bar)
        
        # Distribute to strategies
        for name, strategy in self.strategies.items():
            if self.strategy_modes.get(name, StrategyMode.DISABLED) != StrategyMode.DISABLED:
                try:
                    signal = await strategy.on_bar(bar)
                    if signal:
                        await self._process_strategy_signal(signal, name)
                except Exception as e:
                    logger.error(f"Strategy {name} error on bar: {e}")
    
    async def _load_strategies(self) -> None:
        """Load and initialize strategies"""
        logger.info("Loading strategies...")
        
        # Get strategy configs from Redis or database
        try:
            strategy_configs = await self.redis.get("strategies:config")
            if strategy_configs:
                configs = json.loads(strategy_configs)
                for config in configs:
                    # Dynamically import and instantiate strategies
                    # self.strategies[config['name']] = load_strategy(config)
                    pass
        except Exception as e:
            logger.warning(f"No strategy configs found: {e}")
    
    def _schedule_tasks(self) -> None:
        """Schedule periodic tasks"""
        # Heartbeat every 30 seconds
        self.scheduler.add_job(
            self._heartbeat,
            'interval',
            seconds=self.config.heartbeat_interval,
            id='heartbeat'
        )
        
        # Position reconciliation every minute
        self.scheduler.add_job(
            self._reconcile_positions,
            'interval',
            seconds=60,
            id='reconcile_positions'
        )
        
        # Account snapshot every 5 minutes
        self.scheduler.add_job(
            self._snapshot_account,
            'interval',
            seconds=300,
            id='snapshot_account'
        )
        
        # Check market hours
        self.scheduler.add_job(
            self._check_market_hours,
            'interval',
            seconds=60,
            id='check_market'
        )
        
        self.scheduler.start()
        logger.info("Scheduled tasks started")
    
    async def _heartbeat(self) -> None:
        """Send heartbeat to monitoring"""
        timestamp = datetime.utcnow().isoformat()
        await self.redis.setex(
            f"engine:{self.config.engine_id}:heartbeat",
            self.config.heartbeat_interval * 2,
            timestamp
        )
        
        # Include engine stats
        stats = {
            "timestamp": timestamp,
            "trading_enabled": self.trading_enabled,
            "positions_count": len(self.positions),
            "pending_orders": len(self.pending_orders),
            "risk_halted": self.risk_manager.is_halted,
            "strategies_active": sum(1 for mode in self.strategy_modes.values() if mode != StrategyMode.DISABLED),
            "mode": "LIVE"
        }
        await self.redis.set(f"engine:{self.config.engine_id}:stats", json.dumps(stats))
        
        logger.debug(f"Heartbeat sent: {stats}")
    
    async def _reconcile_positions(self) -> None:
        """Reconcile LIVE positions with broker"""
        try:
            # Get positions from Alpaca
            broker_positions = await self.alpaca.get_positions()
            
            # Update local cache
            self.positions = {pos.symbol: pos for pos in broker_positions}
            
            # Save to database
            for position in broker_positions:
                await self._save_position(position)
            
            logger.info(f"Reconciled {len(broker_positions)} LIVE positions")
            
        except Exception as e:
            logger.error(f"Position reconciliation failed: {e}")
    
    async def _snapshot_account(self) -> None:
        """Take LIVE account snapshot"""
        try:
            account = await self.alpaca.get_account()
            
            # Calculate P&L
            daily_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            
            # Save snapshot
            await self.db.execute("""
                INSERT INTO account_snapshots 
                (equity, cash, buying_power, positions_count, daily_pnl, total_pnl, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, 
                account['equity'],
                account['cash'], 
                account['buying_power'],
                len(self.positions),
                daily_pnl,
                daily_pnl,  # TODO: Calculate total P&L
                datetime.utcnow()
            )
            
            # Update risk manager
            self.risk_manager.update_daily_pnl(daily_pnl)
            
            # Update monitoring metrics
            if self.monitor:
                await self.monitor.update_pnl(daily_pnl, daily_pnl)  # TODO: Calculate total P&L
                self.monitor.positions_value.set(account['equity'])
                self.monitor.risk_score.set(self.risk_manager.get_risk_level_score())
            
            logger.warning(f"LIVE Account - Equity: ${account['equity']:.2f}, Daily P&L: ${daily_pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Account snapshot failed: {e}")
    
    async def _check_market_hours(self) -> None:
        """Check if market is open"""
        is_open = self.alpaca.is_market_open()
        await self.redis.set("market:is_open", str(is_open))
        
        if not is_open and self.trading_enabled:
            logger.info("Market closed")
    
    async def _process_strategy_signal(self, signal: OrderIntent, strategy_name: str) -> None:
        """Process order intent from strategy"""
        signal.strategy_name = strategy_name
        mode = self.strategy_modes.get(strategy_name, StrategyMode.DISABLED)
        
        # Check if trading is enabled
        if not self.trading_enabled:
            logger.warning(f"Trading disabled, skipping signal: {signal}")
            return
        
        # Risk checks
        is_allowed, reason = self.risk_manager.check_order_intent(signal, self.positions)
        if not is_allowed:
            logger.warning(f"Risk check failed for {signal}: {reason}")
            await self._log_rejected_order(signal, reason)
            return
        
        # Process based on mode
        if mode == StrategyMode.SHADOW:
            # Shadow mode: log only
            logger.info(f"SHADOW: Would place order {signal}")
            await self._log_shadow_order(signal)
            
        elif mode == StrategyMode.CANARY:
            # Canary mode: reduce size
            original_qty = signal.qty
            signal.qty = min(signal.qty, 10)  # Cap at 10 shares for canary
            logger.warning(f"CANARY: Reducing order size from {original_qty} to {signal.qty}")
            await self._place_live_order(signal)
            
        elif mode == StrategyMode.ENABLED:
            # Full LIVE trading
            logger.warning(f"LIVE TRADE: {signal}")
            await self._place_live_order(signal)
        
        else:
            logger.debug(f"Strategy {strategy_name} is disabled")
    
    async def _place_live_order(self, intent: OrderIntent) -> None:
        """Place LIVE order with broker"""
        try:
            # Additional safety check
            order_value = intent.qty * (intent.limit_price or 999999)
            if order_value > self.config.max_single_order_value:
                logger.error(f"Order exceeds max single order value: ${order_value:.2f} > ${self.config.max_single_order_value}")
                return
            
            order_start_time = datetime.utcnow()
            order = await self.alpaca.place_order(intent)
            order_latency = (datetime.utcnow() - order_start_time).total_seconds() * 1000
            
            # Record monitoring metrics
            if self.monitor:
                await self.monitor.record_order(order, intent.strategy_name)
                self.monitor.order_latency.labels(strategy=intent.strategy_name).observe(order_latency)
            
            # Log to database
            await self.db.execute("""
                INSERT INTO orders 
                (id, symbol, side, order_type, qty, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                order['id'],
                intent.symbol,
                intent.side,
                intent.order_type,
                intent.qty,
                order['status'],
                datetime.utcnow()
            )
            
            self.pending_orders.append(order)
            logger.warning(f"LIVE ORDER PLACED: {order}")
            
        except Exception as e:
            # Record rejection in monitoring
            if self.monitor:
                await self.monitor.record_rejection(
                    {"symbol": intent.symbol, "side": intent.side, "qty": intent.qty},
                    str(e),
                    intent.strategy_name
                )
            logger.error(f"Failed to place LIVE order {intent}: {e}")
    
    async def _log_shadow_order(self, intent: OrderIntent) -> None:
        """Log shadow order to database"""
        await self.db.execute("""
            INSERT INTO strategy_signals 
            (strategy_name, symbol, action, qty, price, execution_mode, executed, reason, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
            intent.strategy_name,
            intent.symbol,
            intent.side,
            intent.qty,
            intent.limit_price or 0,
            "shadow",
            False,
            "Shadow mode - not executed",
            datetime.utcnow()
        )
    
    async def _log_rejected_order(self, intent: OrderIntent, reason: str) -> None:
        """Log rejected order"""
        await self.db.execute("""
            INSERT INTO strategy_signals 
            (strategy_name, symbol, action, qty, price, execution_mode, executed, reason, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
            intent.strategy_name,
            intent.symbol,
            intent.side,
            intent.qty,
            intent.limit_price or 0,
            "rejected",
            False,
            reason,
            datetime.utcnow()
        )
    
    async def _save_position(self, position: Position) -> None:
        """Save position to database"""
        await self.db.execute("""
            INSERT INTO positions 
            (symbol, qty, avg_entry_price, current_price, unrealized_pnl, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (symbol) 
            DO UPDATE SET 
                qty = $2,
                avg_entry_price = $3,
                current_price = $4,
                unrealized_pnl = $5,
                updated_at = $6
        """,
            position.symbol,
            position.qty,
            position.avg_entry_price,
            position.current_price,
            position.unrealized_pnl,
            datetime.utcnow()
        )
    
    async def _log_market_bar(self, bar: MarketBar) -> None:
        """Log market bar to database"""
        await self.db.execute("""
            INSERT INTO market_bars 
            (symbol, timeframe, timestamp, open_price, high_price, low_price, close_price, volume, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING
        """,
            bar.symbol,
            "1m",  # Default timeframe
            bar.timestamp,
            bar.open,
            bar.high,
            bar.low,
            bar.close,
            bar.volume,
            datetime.utcnow()
        )
    
    async def _listen_for_commands(self) -> None:
        """Listen for commands from Redis pub/sub"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe("engine:commands")
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    command = json.loads(message['data'])
                    await self._handle_command(command)
                except Exception as e:
                    logger.error(f"Failed to handle command: {e}")
    
    async def _handle_command(self, command: Dict) -> None:
        """Handle engine command"""
        cmd_type = command.get('command')
        
        if cmd_type == 'flatten_all':
            logger.warning("FLATTEN ALL LIVE POSITIONS - EMERGENCY")
            await self.alpaca.close_all_positions()
            await self.alpaca.cancel_all_orders()
            
        elif cmd_type == 'trading_enabled':
            self.trading_enabled = command.get('enabled', False)
            logger.warning(f"LIVE TRADING {'ENABLED' if self.trading_enabled else 'DISABLED'}")
            
        elif cmd_type == 'strategy_update':
            strategy = command.get('strategy')
            status = command.get('status')
            if strategy and status:
                self.strategy_modes[strategy] = StrategyMode(status)
                logger.info(f"Strategy {strategy} set to {status}")
                
        elif cmd_type == 'config_update':
            config = command.get('config', {})
            if 'daily_loss_limit' in config:
                self.risk_manager.limits.daily_loss_limit = config['daily_loss_limit']
            if 'max_position_size' in config:
                self.risk_manager.limits.max_position_size = config['max_position_size']
            logger.info(f"Configuration updated: {config}")
            
        else:
            logger.warning(f"Unknown command: {cmd_type}")
    
    def add_strategy(self, strategy: StrategyBase, mode: str = "shadow") -> None:
        """Add a trading strategy with execution mode"""
        if mode not in ["shadow", "canary", "enabled"]:
            raise ValueError(f"Invalid strategy mode: {mode}. Must be shadow, canary, or enabled")
        
        self.strategies[strategy.name] = strategy
        self.strategy_modes[strategy.name] = StrategyMode(mode)
        logger.info(f"Added strategy {strategy.name} in {mode} mode")
    
    def update_strategy_mode(self, strategy_name: str, mode: str) -> bool:
        """Update strategy execution mode"""
        if strategy_name not in self.strategies:
            return False
        
        if mode not in ["disabled", "shadow", "canary", "enabled"]:
            return False
        
        old_mode = self.strategy_modes.get(strategy_name, StrategyMode.DISABLED)
        self.strategy_modes[strategy_name] = StrategyMode(mode)
        logger.warning(f"Updated strategy {strategy_name}: {old_mode.value} -> {mode}")
        return True
    
    def remove_strategy(self, strategy_name: str) -> bool:
        """Remove a strategy"""
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            self.strategy_modes.pop(strategy_name, None)
            logger.info(f"Removed strategy {strategy_name}")
            return True
        return False
    
    def get_strategy_status(self) -> Dict[str, Dict]:
        """Get status of all strategies"""
        status = {}
        for name, strategy in self.strategies.items():
            mode = self.strategy_modes.get(name, StrategyMode.DISABLED)
            status[name] = {
                "mode": mode.value,
                "active": getattr(strategy, 'active', True),
                "last_signal": getattr(strategy, 'last_signal_time', None)
            }
        return status
    
    async def execute_order_intent(self, intent: OrderIntent) -> bool:
        """Execute order through risk manager"""
        try:
            positions = await self.alpaca.get_positions()
            position_dict = {pos.symbol: pos for pos in positions}
            
            is_allowed, reason = self.risk_manager.check_order_intent(intent, position_dict)
            
            if not is_allowed:
                logger.warning(f"Order rejected: {reason} - {intent}")
                return False
                
            # Execute order
            order_result = await self.alpaca.place_order(intent)
            logger.info(f"Order placed: {order_result.get('id')} - {intent}")
            return True
            
        except Exception as e:
            logger.error(f"Order execution failed: {e}", exc_info=True)
            return False
    
    async def shutdown(self) -> None:
        """Graceful shutdown"""
        logger.warning("SHUTTING DOWN LIVE TRADING ENGINE...")
        self.running = False
        
        # Cancel all pending orders in live mode
        if self.trading_enabled:
            try:
                cancelled = await self.alpaca.cancel_all_orders()
                logger.warning(f"Cancelled {cancelled} pending LIVE orders")
            except Exception as e:
                logger.error(f"Failed to cancel orders during shutdown: {e}")
        
        # Close connections
        if hasattr(self, 'scheduler'):
            self.scheduler.shutdown()
            
        if hasattr(self, 'redis'):
            await self.redis.close()
            
        if hasattr(self, 'db'):
            await self.db.close()
        
        logger.warning("LIVE ENGINE SHUTDOWN COMPLETE")

async def main() -> None:
    config = EngineConfig()
    engine = TradingEngine(config)
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, initiating shutdown...")
        asyncio.create_task(engine.shutdown())
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await engine.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Engine crashed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await engine.shutdown()

if __name__ == "__main__":
    asyncio.run(main())