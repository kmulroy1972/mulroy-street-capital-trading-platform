import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class RiskLimits:
    # Account-level limits
    daily_loss_limit: Decimal
    max_position_size: Decimal
    max_portfolio_heat: Decimal  # Max % of portfolio at risk
    max_correlation: float  # Max correlation between positions
    per_trade_stop_pct: float  # Stop loss % per trade
    
    # New enhanced limits
    weekly_loss_limit: Optional[Decimal] = None
    max_position_pct: float = 0.1  # Max % of portfolio per position
    max_single_order_value: Optional[Decimal] = None
    max_orders_per_minute: int = 10
    max_daily_trades: int = 100
    margin_call_threshold: float = 0.25  # Halt at 25% drawdown
    
    def to_dict(self):
        return {k: str(v) if isinstance(v, Decimal) else v 
                for k, v in asdict(self).items()}
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: Decimal(v) if k.endswith('_limit') or k.endswith('_size') or k.endswith('_value') 
                     else v for k, v in data.items()})

class RiskManager:
    """Advanced risk management with real-time controls"""
    
    def __init__(self, limits: RiskLimits):
        self.limits = limits
        self.daily_pnl = Decimal(0)
        self.weekly_pnl = Decimal(0)
        self.daily_trades = 0
        self.orders_this_minute = 0
        self.last_order_minute = datetime.now().minute
        
        # Risk tracking
        self.is_halted = False
        self.halt_reason = None
        self.risk_level = RiskLevel.LOW
        self.violations = []
        
        # Position tracking for correlation
        self.position_sectors = {}  # symbol -> sector
        self.correlation_matrix = {}
        
        logger.info(f"Risk Manager initialized with limits: {limits.to_dict()}")
    
    def check_order_intent(self, intent, current_positions: Dict) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive risk check for order intent
        Returns (is_allowed, rejection_reason)
        """
        # Check if halted
        if self.is_halted:
            return False, f"Trading halted: {self.halt_reason}"
        
        # Check daily loss limit
        if self.daily_pnl <= -self.limits.daily_loss_limit:
            self._halt_trading("Daily loss limit exceeded")
            return False, "Daily loss limit exceeded"
        
        # Check weekly loss limit
        if self.limits.weekly_loss_limit and self.weekly_pnl <= -self.limits.weekly_loss_limit:
            self._halt_trading("Weekly loss limit exceeded")
            return False, "Weekly loss limit exceeded"
        
        # Check order size limits
        order_value = Decimal(str(intent.qty)) * Decimal(str(intent.limit_price or 0))
        if self.limits.max_single_order_value and order_value > self.limits.max_single_order_value:
            return False, f"Order value ${order_value} exceeds max ${self.limits.max_single_order_value}"
        
        # Check position size limits
        if intent.symbol in current_positions:
            current_pos = current_positions[intent.symbol]
            new_qty = current_pos.qty + intent.qty if intent.side == "buy" else current_pos.qty - intent.qty
            new_value = abs(new_qty * Decimal(str(intent.limit_price or current_pos.current_price)))
            
            if new_value > self.limits.max_position_size:
                return False, f"Position size ${new_value} would exceed max ${self.limits.max_position_size}"
        
        # Check rate limits
        current_minute = datetime.now().minute
        if current_minute != self.last_order_minute:
            self.orders_this_minute = 0
            self.last_order_minute = current_minute
        
        if self.orders_this_minute >= self.limits.max_orders_per_minute:
            return False, f"Rate limit: {self.limits.max_orders_per_minute} orders per minute"
        
        # Check daily trade limit
        if self.daily_trades >= self.limits.max_daily_trades:
            return False, f"Daily trade limit ({self.limits.max_daily_trades}) reached"
        
        # Check correlation limits
        if not self._check_correlation(intent, current_positions):
            return False, "Position correlation too high"
        
        # Check portfolio heat
        portfolio_heat = self._calculate_portfolio_heat(current_positions)
        if portfolio_heat > float(self.limits.max_portfolio_heat):
            return False, f"Portfolio heat {portfolio_heat:.2%} exceeds max {self.limits.max_portfolio_heat:.2%}"
        
        # All checks passed
        self.orders_this_minute += 1
        self.daily_trades += 1
        
        return True, None
    
    def update_pnl(self, daily_pnl: Decimal, weekly_pnl: Optional[Decimal] = None):
        """Update P&L and check for risk violations"""
        self.daily_pnl = daily_pnl
        if weekly_pnl is not None:
            self.weekly_pnl = weekly_pnl
        
        # Update risk level
        self._update_risk_level()
        
        # Check for automatic halt conditions
        if daily_pnl <= -self.limits.daily_loss_limit:
            self._halt_trading("Daily loss limit exceeded")
        elif weekly_pnl and self.limits.weekly_loss_limit and weekly_pnl <= -self.limits.weekly_loss_limit:
            self._halt_trading("Weekly loss limit exceeded")
        elif daily_pnl <= -self.limits.daily_loss_limit * Decimal(str(self.limits.margin_call_threshold)):
            self.risk_level = RiskLevel.HIGH
            logger.warning(f"Risk level HIGH: Daily P&L at {daily_pnl}")
    
    def update_daily_pnl(self, pnl: float) -> None:
        """Update daily P&L tracking"""
        self.daily_pnl = Decimal(str(pnl))
        self._update_risk_level()
    
    def update_portfolio_pnl(self, positions: Dict) -> None:
        """Update P&L from positions"""
        total_pnl = sum(Decimal(str(pos.unrealized_pnl)) for pos in positions.values())
        self.update_daily_pnl(float(total_pnl))
    
    def _calculate_portfolio_heat(self, positions: Dict) -> float:
        """Calculate total portfolio risk exposure"""
        if not positions:
            return 0.0
        
        total_risk = Decimal(0)
        total_value = Decimal(0)
        
        for symbol, pos in positions.items():
            position_value = abs(Decimal(str(pos.qty)) * Decimal(str(pos.current_price)))
            risk_amount = position_value * Decimal(str(self.limits.per_trade_stop_pct))
            total_risk += risk_amount
            total_value += position_value
        
        return float(total_risk / total_value) if total_value > 0 else 0.0
    
    def _check_correlation(self, intent, positions: Dict) -> bool:
        """Check if new position would exceed correlation limits"""
        # Simplified correlation check - in production, use actual correlation data
        if intent.symbol in self.position_sectors:
            sector = self.position_sectors[intent.symbol]
            sector_exposure = sum(1 for s, sec in self.position_sectors.items() 
                                 if sec == sector and s in positions)
            
            if sector_exposure >= 3:  # Max 3 positions in same sector
                return False
        
        return True
    
    def _update_risk_level(self):
        """Update current risk level based on metrics"""
        daily_loss_pct = float(self.daily_pnl / self.limits.daily_loss_limit) if self.limits.daily_loss_limit != 0 else 0
        
        if daily_loss_pct <= -0.75:
            self.risk_level = RiskLevel.CRITICAL
        elif daily_loss_pct <= -0.50:
            self.risk_level = RiskLevel.HIGH
        elif daily_loss_pct <= -0.25:
            self.risk_level = RiskLevel.MEDIUM
        else:
            self.risk_level = RiskLevel.LOW
    
    def _halt_trading(self, reason: str):
        """Halt all trading"""
        self.is_halted = True
        self.halt_reason = reason
        self.risk_level = RiskLevel.CRITICAL
        self.violations.append(f"{datetime.now().isoformat()}: {reason}")
        logger.error(f"TRADING HALTED: {reason}")
        
    def resume_trading(self):
        """Resume trading after halt"""
        self.is_halted = False
        self.halt_reason = None
        logger.info("Trading resumed")
    
    def emergency_halt(self) -> None:
        """Kill switch activation"""
        self._halt_trading("Emergency halt activated")
        
    def reset_daily_pnl(self) -> None:
        """Reset daily P&L tracking (called at market open)"""
        self.daily_pnl = Decimal(0)
        self.daily_trades = 0
        self.orders_this_minute = 0
    
    def get_risk_level_score(self) -> int:
        """Get numeric risk level score (0-100)"""
        risk_level_scores = {
            RiskLevel.LOW: 25,
            RiskLevel.MEDIUM: 50,
            RiskLevel.HIGH: 75,
            RiskLevel.CRITICAL: 100
        }
        return risk_level_scores.get(self.risk_level, 0)
        logger.info("Daily risk counters reset")
    
    def get_risk_status(self) -> Dict:
        """Get current risk status"""
        return {
            "is_halted": self.is_halted,
            "halt_reason": self.halt_reason,
            "risk_level": self.risk_level.value,
            "daily_pnl": float(self.daily_pnl),
            "weekly_pnl": float(self.weekly_pnl),
            "daily_trades": self.daily_trades,
            "daily_loss_limit": float(self.limits.daily_loss_limit),
            "weekly_loss_limit": float(self.limits.weekly_loss_limit) if self.limits.weekly_loss_limit else None,
            "violations": self.violations[-10:]  # Last 10 violations
        }