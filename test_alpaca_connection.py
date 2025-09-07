#!/usr/bin/env python3
"""
Alpaca Live Trading Connection Test Suite
Tests connection, account access, and market data without placing any orders
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import with error handling
try:
    from packages.core.broker.alpaca_adapter import AlpacaAdapter, AlpacaConfig
    from packages.core.types import MarketBar
    print("✅ Successfully imported Alpaca modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the alpaca-trader directory")
    sys.exit(1)

# Configuration
TEST_CREDENTIALS = {
    "api_key_id": "AKHT4KA9CHH6IPIF24TF",
    "api_secret_key": "jEXQa4rgIma8p9umGVSfYb0se7EzRUKKjnUwIzIV",
    "base_url": "https://api.alpaca.markets"
}

async def test_connection():
    """Test basic connection to Alpaca"""
    print("\n" + "="*60)
    print("ALPACA LIVE TRADING CONNECTION TEST")
    print("="*60)
    print(f"Timestamp: {datetime.now()}")
    print(f"API URL: {TEST_CREDENTIALS['base_url']}")
    print("-"*60)
    
    # Initialize adapter
    config = AlpacaConfig(
        api_key_id=TEST_CREDENTIALS["api_key_id"],
        api_secret_key=TEST_CREDENTIALS["api_secret_key"],
        base_url=TEST_CREDENTIALS["base_url"]
    )
    
    adapter = AlpacaAdapter(config)
    
    # Track test results
    test_results = {
        "connection": False,
        "account": False,
        "positions": False,
        "orders": False,
        "market_status": False
    }
    
    try:
        # Test 1: Basic Connection
        print("\n[TEST 1] Testing API Connection...")
        connected = await adapter.connect()
        if connected:
            print("✅ SUCCESS: Connected to Alpaca Live Trading API")
            test_results["connection"] = True
        else:
            print("❌ FAILED: Could not connect to Alpaca")
            print("Check your API keys and network connection")
            return test_results
    except Exception as e:
        print(f"❌ ERROR: Connection failed - {e}")
        return test_results
    
    try:
        # Test 2: Account Information
        print("\n[TEST 2] Fetching Account Information...")
        account = await adapter.get_account()
        
        print("✅ SUCCESS: Account data retrieved")
        print(f"   Account Equity: ${account['equity']:,.2f}")
        print(f"   Cash Balance: ${account['cash']:,.2f}")
        print(f"   Buying Power: ${account['buying_power']:,.2f}")
        print(f"   Portfolio Value: ${account['portfolio_value']:,.2f}")
        print(f"   Pattern Day Trader: {account['pattern_day_trader']}")
        print(f"   Account Blocked: {account['account_blocked']}")
        print(f"   Trading Blocked: {account['trading_blocked']}")
        
        test_results["account"] = True
        
        # Warnings
        if account['trading_blocked']:
            print("⚠️  WARNING: Trading is blocked on this account!")
        if account['account_blocked']:
            print("⚠️  WARNING: Account is blocked!")
            
    except Exception as e:
        print(f"❌ ERROR: Failed to get account - {e}")
    
    try:
        # Test 3: Current Positions
        print("\n[TEST 3] Fetching Current Positions...")
        positions = await adapter.get_positions()
        
        print(f"✅ SUCCESS: Retrieved {len(positions)} positions")
        if positions:
            print("   Current positions:")
            for i, pos in enumerate(positions[:10], 1):  # Show max 10
                pnl_symbol = "🟢" if pos.unrealized_pnl >= 0 else "🔴"
                print(f"   {i}. {pos.symbol}: {pos.qty} shares @ ${pos.avg_entry_price:.2f}")
                print(f"      Current: ${pos.current_price:.2f} | P&L: {pnl_symbol} ${pos.unrealized_pnl:.2f}")
        else:
            print("   No open positions")
            
        test_results["positions"] = True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to get positions - {e}")
    
    try:
        # Test 4: Open Orders
        print("\n[TEST 4] Fetching Open Orders...")
        orders = await adapter.get_orders("open")
        
        print(f"✅ SUCCESS: Retrieved {len(orders)} open orders")
        if orders:
            print("   Open orders:")
            for i, order in enumerate(orders[:10], 1):  # Show max 10
                print(f"   {i}. {order['symbol']}: {order['side'].upper()} {order['qty']} @ {order['order_type']}")
                print(f"      Status: {order['status']} | ID: {order['id'][:8]}...")
        else:
            print("   No open orders")
            
        test_results["orders"] = True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to get orders - {e}")
    
    try:
        # Test 5: Market Status
        print("\n[TEST 5] Checking Market Status...")
        is_open = adapter.is_market_open()
        market_hours = await adapter.get_market_hours()
        
        status_emoji = "🟢" if is_open else "🔴"
        print(f"✅ SUCCESS: Market status retrieved")
        print(f"   Market Status: {status_emoji} {'OPEN' if is_open else 'CLOSED'}")
        print(f"   Market Date: {market_hours['date']}")
        print(f"   Market Hours: {market_hours['open']} - {market_hours['close']} ET")
        
        test_results["market_status"] = True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to check market status - {e}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():20} {status}")
    
    print("-"*60)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Alpaca connection is working correctly.")
        print("✅ You can now proceed with running the trading engine in SHADOW mode.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("❌ Do not proceed with live trading until all tests pass.")
    
    return test_results

async def test_market_data_stream():
    """Test real-time market data streaming"""
    print("\n" + "="*60)
    print("TESTING MARKET DATA STREAM")
    print("="*60)
    
    config = AlpacaConfig(
        api_key_id=TEST_CREDENTIALS["api_key_id"],
        api_secret_key=TEST_CREDENTIALS["api_secret_key"],
        base_url=TEST_CREDENTIALS["base_url"]
    )
    
    adapter = AlpacaAdapter(config)
    
    print("Connecting to market data stream...")
    connected = await adapter.connect()
    
    if not connected:
        print("❌ Failed to connect to market data stream")
        return
    
    print("✅ Connected to market data stream")
    print("Subscribing to SPY bars for 10 seconds...")
    
    # Track received data
    bars_received = []
    
    async def on_bar(bar: MarketBar):
        bars_received.append(bar)
        print(f"   📊 Bar: {bar.symbol} @ ${bar.close:.2f} | Volume: {bar.volume:,.0f}")
    
    # Subscribe to SPY
    adapter.subscribe_bars(["SPY"], on_bar)
    
    # Wait for 10 seconds
    await asyncio.sleep(10)
    
    print(f"\n✅ Received {len(bars_received)} bars in 10 seconds")
    
    if bars_received:
        print("Market data streaming is working!")
    else:
        print("⚠️  No bars received. Market might be closed.")

async def main():
    """Run all tests"""
    try:
        # Run connection tests
        results = await test_connection()
        
        # If basic tests pass, optionally test streaming
        if results.get("connection", False):
            print("\n" + "="*60)
            response = input("Do you want to test market data streaming? (y/n): ")
            if response.lower() == 'y':
                await test_market_data_stream()
        
        print("\n" + "="*60)
        print("TESTING COMPLETE")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting Alpaca Live Trading Connection Tests...")
    asyncio.run(main())