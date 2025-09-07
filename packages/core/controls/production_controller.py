import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging
import hashlib
import redis.asyncio as redis
from decimal import Decimal

logger = logging.getLogger(__name__)

class SystemState(Enum):
    INITIALIZING = "initializing"
    TESTING = "testing"
    SHADOW = "shadow"
    CANARY = "canary"
    RAMPING = "ramping"
    LIVE = "live"
    PAUSED = "paused"
    EMERGENCY_STOP = "emergency_stop"

class ValidationLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    PARANOID = "paranoid"

@dataclass
class LiveTradingChecklist:
    """Pre-flight checklist for live trading"""
    
    # System checks
    api_connection: bool = False
    database_connection: bool = False
    redis_connection: bool = False
    market_data_streaming: bool = False
    
    # Account checks
    account_verified: bool = False
    sufficient_capital: bool = False
    no_pending_orders: bool = False
    risk_limits_set: bool = False
    
    # Strategy checks
    strategies_tested: bool = False
    backtest_profitable: bool = False
    shadow_mode_verified: bool = False
    canary_trades_successful: bool = False
    
    # Safety checks
    kill_switch_tested: bool = False
    alerts_configured: bool = False
    monitoring_active: bool = False
    rollback_plan_ready: bool = False
    
    # Compliance checks
    trading_permissions: bool = False
    pattern_day_trader_check: bool = False
    tax_implications_understood: bool = False
    
    def all_passed(self) -> bool:
        """Check if all items are checked"""
        return all(asdict(self).values())
    
    def get_failures(self) -> List[str]:
        """Get list of failed checks"""
        return [k for k, v in asdict(self).items() if not v]

class ProductionController:
    """Master controller for production trading"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.state = SystemState.INITIALIZING
        self.validation_level = ValidationLevel.STRICT
        self.checklist = LiveTradingChecklist()
        
        # Gradual rollout configuration
        self.rollout_config = {
            "max_daily_trades": 5,
            "max_position_size": 1000,
            "max_total_exposure": 5000,
            "allowed_symbols": ["SPY"],  # Start with liquid ETFs
            "allowed_strategies": [],
            "trading_hours_only": True,
            "require_confirmation": True,
        }
        
        # Emergency contacts
        self.emergency_contacts = []
        
        # Audit trail
        self.audit_log = []
        
    async def pre_flight_check(self) -> Tuple[bool, List[str]]:
        """Run comprehensive pre-flight checks before enabling live trading"""
        logger.info("Running pre-flight checks...")
        
        failures = []
        
        # 1. Check API connection
        try:
            # Check Alpaca connection
            status = await self.redis.get("alpaca:connection_status")
            self.checklist.api_connection = status == b"connected"
        except:
            failures.append("API connection check failed")
        
        # 2. Check database
        try:
            db_status = await self.redis.get("database:status")
            self.checklist.database_connection = db_status == b"healthy"
        except:
            failures.append("Database connection check failed")
        
        # 3. Check Redis
        try:
            await self.redis.ping()
            self.checklist.redis_connection = True
        except:
            failures.append("Redis connection check failed")
        
        # 4. Check market data
        try:
            last_bar = await self.redis.get("market:last_bar_time")
            if last_bar:
                last_time = datetime.fromisoformat(last_bar.decode())
                self.checklist.market_data_streaming = (datetime.utcnow() - last_time).seconds < 60
        except:
            failures.append("Market data streaming check failed")
        
        # 5. Check account
        try:
            account_data = await self.redis.get("account:snapshot")
            if account_data:
                account = json.loads(account_data)
                self.checklist.account_verified = True
                self.checklist.sufficient_capital = account.get("equity", 0) >= 25000  # PDT minimum
        except:
            failures.append("Account verification failed")
        
        # 6. Check strategies
        try:
            backtest_results = await self.redis.get("backtest:latest_results")
            if backtest_results:
                results = json.loads(backtest_results)
                self.checklist.strategies_tested = True
                self.checklist.backtest_profitable = results.get("total_pnl", 0) > 0
        except:
            failures.append("Strategy verification failed")
        
        # 7. Check safety systems
        try:
            kill_switch = await self.redis.get("safety:kill_switch_tested")
            self.checklist.kill_switch_tested = kill_switch == b"true"
            
            alerts = await self.redis.get("monitoring:alerts_configured")
            self.checklist.alerts_configured = alerts == b"true"
        except:
            failures.append("Safety systems check failed")
        
        # 8. Check monitoring
        try:
            monitoring = await self.redis.get("monitoring:status")
            self.checklist.monitoring_active = monitoring == b"active"
        except:
            failures.append("Monitoring check failed")
        
        # Get all failures
        failures.extend(self.checklist.get_failures())
        
        passed = len(failures) == 0
        
        # Log results
        logger.info(f"Pre-flight check: {'PASSED' if passed else 'FAILED'}")
        if failures:
            logger.error(f"Failed checks: {failures}")
        
        # Store results
        await self.redis.set(
            "preflight:latest",
            json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "passed": passed,
                "failures": failures,
                "checklist": asdict(self.checklist)
            })
        )
        
        return passed, failures
    
    async def start_shadow_mode(self) -> bool:
        """Start shadow trading mode"""
        logger.info("Starting shadow mode...")
        
        # Verify pre-flight
        passed, failures = await self.pre_flight_check()
        if not passed:
            logger.error(f"Cannot start shadow mode: {failures}")
            return False
        
        self.state = SystemState.SHADOW
        
        # Configure engine for shadow mode
        await self.redis.publish("engine:commands", json.dumps({
            "command": "set_mode",
            "mode": "shadow",
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Start monitoring
        asyncio.create_task(self._monitor_shadow_performance())
        
        logger.info("Shadow mode activated")
        return True
    
    async def start_canary_mode(self, initial_size: int = 1) -> bool:
        """Start canary trading with minimal size"""
        logger.info(f"Starting canary mode with size {initial_size}...")
        
        # Must complete shadow mode first
        shadow_stats = await self.redis.get("shadow:statistics")
        if not shadow_stats:
            logger.error("Must complete shadow mode first")
            return False
        
        stats = json.loads(shadow_stats)
        if stats.get("duration_hours", 0) < 24:
            logger.error("Shadow mode must run for at least 24 hours")
            return False
        
        self.state = SystemState.CANARY
        
        # Configure very conservative limits
        canary_config = {
            "max_position_size": initial_size,
            "max_daily_trades": 3,
            "allowed_symbols": ["SPY"],  # Only most liquid
            "max_total_exposure": initial_size * 100,  # $100 per share max
        }
        
        await self.redis.set("canary:config", json.dumps(canary_config))
        
        # Enable canary trading
        await self.redis.publish("engine:commands", json.dumps({
            "command": "set_mode",
            "mode": "canary",
            "config": canary_config,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Start canary monitoring
        asyncio.create_task(self._monitor_canary_trades())
        
        logger.info("Canary mode activated")
        return True
    
    async def gradual_ramp_up(self, target_size: int, days: int = 7) -> bool:
        """Gradually increase position sizes over time"""
        logger.info(f"Starting gradual ramp-up to {target_size} over {days} days")
        
        # Verify canary success
        canary_stats = await self.redis.get("canary:statistics")
        if not canary_stats:
            logger.error("Must complete canary mode first")
            return False
        
        stats = json.loads(canary_stats)
        if stats.get("success_rate", 0) < 0.8:  # 80% success rate required
            logger.error(f"Canary success rate too low: {stats.get('success_rate', 0):.1%}")
            return False
        
        self.state = SystemState.RAMPING
        
        # Calculate daily increments
        current_size = 1
        daily_increment = (target_size - current_size) / days
        
        for day in range(days):
            current_size += daily_increment
            
            # Update limits
            ramp_config = {
                "max_position_size": int(current_size),
                "max_daily_trades": min(10, 3 + day),  # Gradually increase trades
                "allowed_symbols": self._get_allowed_symbols(day),
                "max_total_exposure": int(current_size * 100 * (day + 1)),
            }
            
            await self.redis.set(f"ramp:day_{day}", json.dumps(ramp_config))
            
            # Schedule update
            await self._schedule_config_update(day, ramp_config)
            
            logger.info(f"Day {day + 1}: Position size = {int(current_size)}")
        
        return True
    
    async def enable_live_trading(self, final_confirmation: str = "") -> bool:
        """Enable full live trading with final safety check"""
        logger.warning("=" * 60)
        logger.warning("ENABLING LIVE TRADING")
        logger.warning("=" * 60)
        
        # Require explicit confirmation
        expected_confirmation = hashlib.sha256(
            f"{datetime.utcnow().date()}:ENABLE_LIVE_TRADING".encode()
        ).hexdigest()[:8]
        
        if final_confirmation != expected_confirmation:
            logger.error(f"Invalid confirmation code. Expected: {expected_confirmation}")
            return False
        
        # Final pre-flight check
        passed, failures = await self.pre_flight_check()
        if not passed:
            logger.error(f"Pre-flight check failed: {failures}")
            return False
        
        # Verify ramp-up completion
        ramp_stats = await self.redis.get("ramp:statistics")
        if not ramp_stats:
            logger.error("Must complete ramp-up period first")
            return False
        
        self.state = SystemState.LIVE
        
        # Enable live trading
        await self.redis.publish("engine:commands", json.dumps({
            "command": "enable_live_trading",
            "timestamp": datetime.utcnow().isoformat(),
            "confirmed_by": final_confirmation
        }))
        
        # Log activation
        self.audit_log.append({
            "action": "LIVE_TRADING_ENABLED",
            "timestamp": datetime.utcnow().isoformat(),
            "confirmation": final_confirmation
        })
        
        # Start production monitoring
        asyncio.create_task(self._production_monitor())
        
        # Send notifications
        await self._notify_emergency_contacts("Live trading has been enabled")
        
        logger.warning("LIVE TRADING IS NOW ACTIVE")
        return True
    
    async def emergency_stop(self, reason: str = "Manual trigger") -> bool:
        """Emergency stop - immediately halt all trading"""
        logger.critical(f"EMERGENCY STOP TRIGGERED: {reason}")
        
        self.state = SystemState.EMERGENCY_STOP
        
        # Send emergency stop command
        await self.redis.publish("engine:commands", json.dumps({
            "command": "EMERGENCY_STOP",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Cancel all orders
        await self.redis.publish("engine:commands", json.dumps({
            "command": "cancel_all_orders"
        }))
        
        # Flatten all positions if specified
        if "flatten" in reason.lower():
            await self.redis.publish("engine:commands", json.dumps({
                "command": "flatten_all_positions"
            }))
        
        # Log emergency stop
        self.audit_log.append({
            "action": "EMERGENCY_STOP",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Notify
        await self._notify_emergency_contacts(f"EMERGENCY STOP: {reason}")
        
        return True
    
    async def pause_trading(self, duration_minutes: int = 60) -> bool:
        """Temporarily pause trading"""
        logger.info(f"Pausing trading for {duration_minutes} minutes")
        
        self.state = SystemState.PAUSED
        
        await self.redis.publish("engine:commands", json.dumps({
            "command": "pause_trading",
            "duration_minutes": duration_minutes,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Schedule resume
        asyncio.create_task(self._auto_resume(duration_minutes))
        
        return True
    
    async def _monitor_shadow_performance(self):
        """Monitor shadow trading performance"""
        while self.state == SystemState.SHADOW:
            # Collect shadow trade statistics
            intents = await self.redis.lrange("shadow:intents", 0, -1)
            
            stats = {
                "total_intents": len(intents),
                "duration_hours": 0,  # Calculate from start time
                "would_be_pnl": 0,  # Calculate from prices
            }
            
            await self.redis.set("shadow:statistics", json.dumps(stats))
            await asyncio.sleep(60)  # Check every minute
    
    async def _monitor_canary_trades(self):
        """Monitor canary trades closely"""
        while self.state == SystemState.CANARY:
            # Get canary trades
            trades = await self.redis.lrange("canary:trades", 0, -1)
            
            if trades:
                success_count = sum(1 for t in trades if json.loads(t).get("pnl", 0) > 0)
                stats = {
                    "total_trades": len(trades),
                    "success_rate": success_count / len(trades),
                    "total_pnl": sum(json.loads(t).get("pnl", 0) for t in trades)
                }
                
                await self.redis.set("canary:statistics", json.dumps(stats))
                
                # Check for issues
                if stats["success_rate"] < 0.5:  # Less than 50% success
                    logger.warning("Low canary success rate, consider stopping")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _production_monitor(self):
        """Monitor production trading"""
        while self.state == SystemState.LIVE:
            # Get current metrics
            metrics = {
                "heartbeat": await self.redis.get("engine:heartbeat"),
                "daily_pnl": await self.redis.get("trading:daily_pnl"),
                "positions": await self.redis.llen("trading:positions"),
                "alerts": await self.redis.llen("alerts:active")
            }
            
            # Check for issues
            if metrics.get("daily_pnl") and float(metrics["daily_pnl"]) < -1000:
                await self.emergency_stop("Daily loss limit exceeded")
            
            await asyncio.sleep(10)  # Check every 10 seconds
    
    async def _schedule_config_update(self, day: int, config: Dict):
        """Schedule configuration update for ramp-up"""
        await asyncio.sleep(86400 * day)  # Wait for the specified day
        
        if self.state == SystemState.RAMPING:
            await self.redis.publish("engine:commands", json.dumps({
                "command": "update_config",
                "config": config,
                "day": day
            }))
    
    async def _auto_resume(self, minutes: int):
        """Auto-resume after pause"""
        await asyncio.sleep(minutes * 60)
        
        if self.state == SystemState.PAUSED:
            self.state = SystemState.LIVE
            await self.redis.publish("engine:commands", json.dumps({
                "command": "resume_trading",
                "timestamp": datetime.utcnow().isoformat()
            }))
            logger.info("Trading resumed after pause")
    
    def _get_allowed_symbols(self, day: int) -> List[str]:
        """Get allowed symbols based on ramp day"""
        # Gradually add more symbols
        base_symbols = ["SPY", "QQQ"]
        
        if day >= 3:
            base_symbols.extend(["AAPL", "MSFT"])
        if day >= 5:
            base_symbols.extend(["GOOGL", "AMZN"])
        if day >= 7:
            base_symbols.extend(["TSLA", "NVDA"])
        
        return base_symbols
    
    async def _notify_emergency_contacts(self, message: str):
        """Send notifications to emergency contacts"""
        for contact in self.emergency_contacts:
            # Send notification (email, SMS, etc.)
            logger.info(f"Notifying {contact}: {message}")