import pytest
from decimal import Decimal
from packages.core.risk.risk_manager import RiskManager, RiskLimits
from packages.core.types import OrderIntent, Position

def test_risk_manager_daily_loss_limit():
    limits = RiskLimits(
        daily_loss_limit=Decimal("1000"),
        max_position_size=Decimal("10000"),
        max_portfolio_heat=Decimal("0.02"),
        max_correlation=0.7,
        per_trade_stop_pct=0.02
    )
    
    manager = RiskManager(limits)
    manager.update_daily_pnl(Decimal("-500"))
    assert not manager.is_halted
    
    manager.update_daily_pnl(Decimal("-600"))
    assert manager.is_halted

def test_risk_manager_position_size_limit():
    limits = RiskLimits(
        daily_loss_limit=Decimal("1000"),
        max_position_size=Decimal("5000"),
        max_portfolio_heat=Decimal("0.02"),
        max_correlation=0.7,
        per_trade_stop_pct=0.02
    )
    
    manager = RiskManager(limits)
    
    # Order within limits
    small_order = OrderIntent(
        symbol="AAPL",
        side="buy",
        order_type="market",
        qty=10,
        strategy_name="test"
    )
    
    is_allowed, reason = manager.check_order_intent(small_order, {})
    assert is_allowed
    
    # Order exceeding limits
    large_order = OrderIntent(
        symbol="AAPL",
        side="buy",
        order_type="limit",
        qty=100,
        limit_price=100.0,
        strategy_name="test"
    )
    
    is_allowed, reason = manager.check_order_intent(large_order, {})
    assert not is_allowed
    assert "max position limit" in reason

def test_risk_manager_emergency_halt():
    limits = RiskLimits(
        daily_loss_limit=Decimal("1000"),
        max_position_size=Decimal("10000"),
        max_portfolio_heat=Decimal("0.02"),
        max_correlation=0.7,
        per_trade_stop_pct=0.02
    )
    
    manager = RiskManager(limits)
    assert not manager.is_halted
    
    manager.emergency_halt()
    assert manager.is_halted
    
    # Orders should be rejected when halted
    order = OrderIntent(
        symbol="AAPL",
        side="buy",
        order_type="market",
        qty=1,
        strategy_name="test"
    )
    
    is_allowed, reason = manager.check_order_intent(order, {})
    assert not is_allowed
    assert "halted" in reason

def test_risk_manager_reset():
    limits = RiskLimits(
        daily_loss_limit=Decimal("1000"),
        max_position_size=Decimal("10000"),
        max_portfolio_heat=Decimal("0.02"),
        max_correlation=0.7,
        per_trade_stop_pct=0.02
    )
    
    manager = RiskManager(limits)
    manager.update_daily_pnl(Decimal("-500"))
    assert manager.daily_pnl == Decimal("-500")
    
    manager.reset_daily_pnl()
    assert manager.daily_pnl == Decimal("0")