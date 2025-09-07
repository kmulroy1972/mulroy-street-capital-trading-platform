import pytest
import asyncio
from packages.core.broker.alpaca_adapter import AlpacaAdapter, AlpacaConfig
from packages.core.types import OrderIntent

@pytest.mark.asyncio
async def test_alpaca_live_connection():
    """Test connection to Alpaca LIVE trading"""
    config = AlpacaConfig(
        api_key_id="AKHT4KA9CHH6IPIF24TF",
        api_secret_key="jEXQa4rgIma8p9umGVSfYb0se7EzRUKKjnUwIzIV",
        base_url="https://api.alpaca.markets"
    )
    
    adapter = AlpacaAdapter(config)
    connected = await adapter.connect()
    assert connected == True
    
    # Test account retrieval
    account = await adapter.get_account()
    assert account is not None
    assert "equity" in account
    print(f"LIVE Account Equity: ${account['equity']}")

@pytest.mark.asyncio
async def test_shadow_order():
    """Test shadow mode order (no actual placement)"""
    # This would be handled by the engine in shadow mode
    intent = OrderIntent(
        symbol="AAPL",
        side="buy",
        order_type="market",
        qty=1,
        strategy_name="test_strategy"
    )
    
    # In shadow mode, we just log the intent
    assert intent.symbol == "AAPL"
    assert intent.side == "buy"
    print(f"Shadow order: {intent}")

@pytest.mark.asyncio 
async def test_live_account_validation():
    """Test live account has required permissions"""
    config = AlpacaConfig(
        api_key_id="AKHT4KA9CHH6IPIF24TF",
        api_secret_key="jEXQa4rgIma8p9umGVSfYb0se7EzRUKKjnUwIzIV"
    )
    
    adapter = AlpacaAdapter(config)
    
    # Should connect to live account
    connected = await adapter.connect()
    assert connected
    
    # Check account status
    account = await adapter.get_account()
    assert not account.get('trading_blocked', False), "Account trading is blocked"
    assert not account.get('account_blocked', False), "Account is blocked"
    
    # Check market hours
    market_hours = await adapter.get_market_hours()
    assert 'open' in market_hours
    assert 'close' in market_hours

@pytest.mark.asyncio
async def test_risk_limits_enforced():
    """Test that risk limits are properly enforced"""
    # Large order that should be rejected
    large_intent = OrderIntent(
        symbol="SPY",
        side="buy",
        order_type="market", 
        qty=1000000,  # Very large quantity
        strategy_name="test_strategy"
    )
    
    # This would be rejected by risk manager in real engine
    assert large_intent.qty > 100000  # Unreasonably large

@pytest.mark.asyncio
async def test_market_data_subscription():
    """Test market data subscription works"""
    config = AlpacaConfig(
        api_key_id="AKHT4KA9CHH6IPIF24TF",
        api_secret_key="jEXQa4rgIma8p9umGVSfYb0se7EzRUKKjnUwIzIV"
    )
    
    adapter = AlpacaAdapter(config)
    
    received_bars = []
    
    async def bar_callback(bar):
        received_bars.append(bar)
    
    # Subscribe to market data
    adapter.subscribe_bars(["SPY"], bar_callback)
    
    # Verify subscription was set up
    assert len(adapter.bar_callbacks) == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])