import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.core.broker.alpaca_adapter import AlpacaAdapter, AlpacaConfig

async def test_connection():
    print("=" * 50)
    print("Testing Alpaca LIVE Connection")
    print("=" * 50)
    
    # Initialize adapter with your credentials
    config = AlpacaConfig(
        api_key_id="AKHT4KA9CHH6IPIF24TF",
        api_secret_key="jEXQa4rgIma8p9umGVSfYb0se7EzRUKKjnUwIzIV",
        base_url="https://api.alpaca.markets"
    )
    
    adapter = AlpacaAdapter(config)
    
    # Test 1: Connect to Alpaca
    print("\n1. Testing connection...")
    connected = await adapter.connect()
    if connected:
        print("✅ Successfully connected to Alpaca LIVE")
    else:
        print("❌ Failed to connect")
        return
    
    # Test 2: Get account info
    print("\n2. Getting account information...")
    try:
        account = await adapter.get_account()
        print(f"✅ Account Status: Active")
        print(f"   Equity: ${account['equity']:,.2f}")
        print(f"   Cash: ${account['cash']:,.2f}")
        print(f"   Buying Power: ${account['buying_power']:,.2f}")
        print(f"   Pattern Day Trader: {account['pattern_day_trader']}")
        print(f"   Account Blocked: {account['account_blocked']}")
        print(f"   Trading Blocked: {account['trading_blocked']}")
    except Exception as e:
        print(f"❌ Failed to get account: {e}")
        return
    
    # Test 3: Get positions
    print("\n3. Getting current positions...")
    try:
        positions = await adapter.get_positions()
        print(f"✅ Found {len(positions)} positions")
        for pos in positions[:5]:  # Show first 5
            print(f"   {pos.symbol}: {pos.qty} shares @ ${pos.avg_entry_price:.2f}")
    except Exception as e:
        print(f"❌ Failed to get positions: {e}")
    
    # Test 4: Get open orders
    print("\n4. Getting open orders...")
    try:
        orders = await adapter.get_orders("open")
        print(f"✅ Found {len(orders)} open orders")
        for order in orders[:5]:  # Show first 5
            print(f"   {order['symbol']}: {order['side']} {order['qty']} @ {order['order_type']}")
    except Exception as e:
        print(f"❌ Failed to get orders: {e}")
    
    # Test 5: Check market status
    print("\n5. Checking market status...")
    try:
        is_open = adapter.is_market_open()
        print(f"✅ Market is {'OPEN' if is_open else 'CLOSED'}")
        
        market_hours = await adapter.get_market_hours()
        print(f"   Market hours: {market_hours['open']} - {market_hours['close']}")
    except Exception as e:
        print(f"❌ Failed to check market status: {e}")
    
    print("\n" + "=" * 50)
    print("Connection test complete!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_connection())