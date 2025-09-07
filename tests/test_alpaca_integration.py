import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime, timezone

from packages.core.broker.alpaca_adapter import AlpacaAdapter, AlpacaConfig
from packages.core.market.data_handler import MarketDataHandler
from packages.core.types import OrderIntent, MarketBar, Position

@pytest.fixture
def alpaca_config():
    return AlpacaConfig(
        api_key_id="test_key",
        api_secret_key="test_secret",
        paper=True
    )

@pytest.fixture
def alpaca_adapter(alpaca_config):
    with patch('packages.core.broker.alpaca_adapter.TradingClient'), \
         patch('packages.core.broker.alpaca_adapter.StockDataStream'):
        return AlpacaAdapter(alpaca_config)

@pytest.fixture
def market_data_handler():
    return MarketDataHandler()

@pytest.fixture
def sample_bar():
    return MarketBar(
        symbol="SPY",
        timestamp=int(datetime.now(timezone.utc).timestamp()),
        open=420.50,
        high=421.25,
        low=420.00,
        close=421.00,
        volume=1000000
    )

@pytest.fixture
def sample_order_intent():
    return OrderIntent(
        symbol="SPY",
        side="buy",
        qty=100,
        order_type="market",
        strategy_name="test_strategy"
    )

class TestAlpacaAdapter:
    @pytest.mark.asyncio
    async def test_connect_success(self, alpaca_adapter):
        # Mock successful connection
        alpaca_adapter.trading_client.get_account.return_value = Mock(status="ACTIVE")
        
        result = await alpaca_adapter.connect()
        assert result is True

    @pytest.mark.asyncio
    async def test_connect_failure(self, alpaca_adapter):
        # Mock connection failure
        alpaca_adapter.trading_client.get_account.side_effect = Exception("Connection failed")
        
        result = await alpaca_adapter.connect()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_account(self, alpaca_adapter):
        # Mock account data
        mock_account = Mock()
        mock_account.equity = "100000.00"
        mock_account.cash = "50000.00"
        mock_account.buying_power = "200000.00"
        mock_account.portfolio_value = "100000.00"
        mock_account.pattern_day_trader = False
        mock_account.trading_blocked = False
        mock_account.account_blocked = False
        mock_account.trade_suspended_by_user = False
        mock_account.daytrade_count = 0
        mock_account.daytrading_buying_power = "100000.00"
        
        alpaca_adapter.trading_client.get_account.return_value = mock_account
        
        account = await alpaca_adapter.get_account()
        
        assert account["equity"] == 100000.00
        assert account["cash"] == 50000.00
        assert account["pattern_day_trader"] is False

    @pytest.mark.asyncio
    async def test_place_market_order(self, alpaca_adapter, sample_order_intent):
        # Mock order response
        mock_order = Mock()
        mock_order.id = "order_123"
        mock_order.client_order_id = "test_client_id"
        mock_order.symbol = "SPY"
        mock_order.side.value = "buy"
        mock_order.qty = "100"
        mock_order.order_type.value = "market"
        mock_order.status.value = "new"
        mock_order.submitted_at = datetime.now(timezone.utc)
        mock_order.filled_qty = "0"
        mock_order.filled_avg_price = None
        
        alpaca_adapter.trading_client.submit_order.return_value = mock_order
        
        result = await alpaca_adapter.place_order(sample_order_intent)
        
        assert result["id"] == "order_123"
        assert result["symbol"] == "SPY"
        assert result["side"] == "buy"
        assert result["qty"] == 100.0

    @pytest.mark.asyncio
    async def test_get_positions(self, alpaca_adapter):
        # Mock positions data
        mock_position = Mock()
        mock_position.symbol = "SPY"
        mock_position.qty = "100"
        mock_position.avg_entry_price = "420.50"
        mock_position.current_price = "421.00"
        mock_position.unrealized_pl = "50.00"
        mock_position.realized_pl = "0.00"
        
        alpaca_adapter.trading_client.get_all_positions.return_value = [mock_position]
        
        positions = await alpaca_adapter.get_positions()
        
        assert len(positions) == 1
        assert positions[0].symbol == "SPY"
        assert positions[0].qty == 100.0
        assert positions[0].unrealized_pnl == 50.0

    @pytest.mark.asyncio
    async def test_order_idempotency(self, alpaca_adapter, sample_order_intent):
        client_order_id = "test_duplicate_order"
        
        # First order succeeds
        mock_order = Mock()
        mock_order.id = "order_123"
        mock_order.client_order_id = client_order_id
        alpaca_adapter.trading_client.submit_order.return_value = mock_order
        
        result1 = await alpaca_adapter.place_order(sample_order_intent, client_order_id)
        assert result1["id"] == "order_123"
        
        # Second order with same client_order_id should be rejected
        result2 = await alpaca_adapter.place_order(sample_order_intent, client_order_id)
        assert result2["status"] == "duplicate"

    def test_market_hours_subscription(self, alpaca_adapter):
        symbols = ["SPY", "QQQ"]
        callback = Mock()
        
        alpaca_adapter.subscribe_bars(symbols, callback)
        
        assert callback in alpaca_adapter.bar_callbacks
        alpaca_adapter.data_stream.subscribe_bars.assert_called_with(*symbols)

class TestMarketDataHandler:
    def test_subscribe_symbol(self, market_data_handler):
        symbol = "SPY"
        timeframes = ["1m", "5m"]
        
        market_data_handler.subscribe_symbol(symbol, timeframes)
        
        assert symbol in market_data_handler.aggregators
        assert 60 in market_data_handler.aggregators[symbol]  # 1m
        assert 300 in market_data_handler.aggregators[symbol]  # 5m

    @pytest.mark.asyncio
    async def test_handle_trade_creates_bar(self, market_data_handler):
        # Setup
        symbol = "SPY"
        market_data_handler.subscribe_symbol(symbol, ["1m"])
        
        # Add first trade
        trade_data = {
            "symbol": symbol,
            "price": "420.50",
            "size": "100",
            "timestamp": 1640995200  # Fixed timestamp
        }
        
        await market_data_handler.handle_trade(trade_data)
        
        # Check current bar was created
        current_bar = market_data_handler.get_current_bar(symbol, "1m")
        assert current_bar is not None
        assert current_bar.symbol == symbol
        assert current_bar.open == 420.50
        assert current_bar.close == 420.50
        assert current_bar.volume == 100

    @pytest.mark.asyncio
    async def test_handle_trade_completes_bar(self, market_data_handler):
        # Setup
        symbol = "SPY"
        market_data_handler.subscribe_symbol(symbol, ["1m"])
        
        callback_received = []
        
        def bar_callback(bar: MarketBar):
            callback_received.append(bar)
        
        market_data_handler.add_bar_callback(bar_callback)
        
        # Add trade at time 1640995200 (start of minute)
        await market_data_handler.handle_trade({
            "symbol": symbol,
            "price": "420.50",
            "size": "100",
            "timestamp": 1640995200
        })
        
        # Add trade at time 1640995260 (next minute, should complete previous bar)
        await market_data_handler.handle_trade({
            "symbol": symbol,
            "price": "421.00",
            "size": "50", 
            "timestamp": 1640995260
        })
        
        # Should have received completed bar callback
        assert len(callback_received) == 1
        completed_bar = callback_received[0]
        assert completed_bar.symbol == symbol
        assert completed_bar.open == 420.50
        assert completed_bar.close == 420.50
        assert completed_bar.volume == 100

    def test_get_bars(self, market_data_handler):
        symbol = "SPY"
        market_data_handler.subscribe_symbol(symbol, ["1m"])
        
        # Add a completed bar manually
        aggregator = market_data_handler.aggregators[symbol][60]
        test_bar = MarketBar(
            symbol=symbol,
            timestamp=1640995200,
            open=420.50,
            high=421.00,
            low=420.00,
            close=420.75,
            volume=1000
        )
        aggregator.bars.append(test_bar)
        
        bars = market_data_handler.get_bars(symbol, "1m", 10)
        assert len(bars) == 1
        assert bars[0].symbol == symbol

    def test_get_stats(self, market_data_handler):
        market_data_handler.subscribe_symbol("SPY", ["1m", "5m"])
        market_data_handler.subscribe_symbol("QQQ", ["1m"])
        
        stats = market_data_handler.get_stats()
        
        assert stats["total_symbols"] == 2
        assert stats["total_timeframes"] == 3
        assert "SPY" in stats["symbols"]
        assert "QQQ" in stats["symbols"]

class TestPaperTradingIntegration:
    @pytest.mark.asyncio
    async def test_paper_trading_flow(self, alpaca_adapter, sample_order_intent):
        """Test complete paper trading flow"""
        # Setup mocks for paper trading environment
        alpaca_adapter.config.paper = True
        
        # Mock account
        mock_account = Mock()
        mock_account.equity = "100000.00"
        mock_account.cash = "50000.00"
        alpaca_adapter.trading_client.get_account.return_value = mock_account
        
        # Mock order placement
        mock_order = Mock()
        mock_order.id = "paper_order_123"
        mock_order.status.value = "new"
        alpaca_adapter.trading_client.submit_order.return_value = mock_order
        
        # Mock position after fill
        mock_position = Mock()
        mock_position.symbol = "SPY"
        mock_position.qty = "100"
        mock_position.avg_entry_price = "420.50"
        alpaca_adapter.trading_client.get_all_positions.return_value = [mock_position]
        
        # Test flow
        account = await alpaca_adapter.get_account()
        assert account["equity"] == 100000.00
        
        order_result = await alpaca_adapter.place_order(sample_order_intent)
        assert order_result["id"] == "paper_order_123"
        
        positions = await alpaca_adapter.get_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "SPY"

    @pytest.mark.asyncio 
    async def test_market_data_to_strategy_flow(self, market_data_handler):
        """Test market data flowing to strategy execution"""
        received_bars = []
        
        async def strategy_callback(bar: MarketBar):
            received_bars.append(bar)
        
        market_data_handler.add_bar_callback(strategy_callback)
        market_data_handler.subscribe_symbol("SPY", ["1m"])
        
        # Simulate incoming bar
        test_bar = MarketBar(
            symbol="SPY",
            timestamp=int(datetime.now(timezone.utc).timestamp()),
            open=420.50,
            high=421.00,
            low=420.00,
            close=420.75,
            volume=1000
        )
        
        await market_data_handler.handle_bar(test_bar)
        
        assert len(received_bars) == 1
        assert received_bars[0].symbol == "SPY"

    @pytest.mark.asyncio
    async def test_risk_management_integration(self, alpaca_adapter):
        """Test risk limits prevent orders in paper mode"""
        # This would require importing the risk manager and testing integration
        # For now, just test that orders can be placed
        
        order_intent = OrderIntent(
            symbol="SPY",
            side="buy",
            qty=1000000,  # Very large order
            order_type="market",
            strategy_name="test_strategy"
        )
        
        # Mock order rejection due to size
        alpaca_adapter.trading_client.submit_order.side_effect = Exception("Order too large")
        
        with pytest.raises(Exception):
            await alpaca_adapter.place_order(order_intent)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])