#!/usr/bin/env python3
"""
Simple Alpaca API Connection Test
Uses basic HTTP requests to test connectivity without complex dependencies
"""

import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import base64

# Test credentials
API_KEY_ID = "AKHT4KA9CHH6IPIF24TF"
API_SECRET_KEY = "jEXQa4rgIma8p9umGVSfYb0se7EzRUKKjnUwIzIV"
BASE_URL = "https://api.alpaca.markets"

def create_auth_header():
    """Create authentication header for Alpaca API"""
    credentials = f"{API_KEY_ID}:{API_SECRET_KEY}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded_credentials}"

def test_api_call(endpoint, description):
    """Make a test API call to Alpaca"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        request = Request(url)
        request.add_header("Authorization", create_auth_header())
        request.add_header("Content-Type", "application/json")
        
        with urlopen(request, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print(f"✅ {description}: SUCCESS")
                return data
            else:
                print(f"❌ {description}: HTTP {response.status}")
                return None
                
    except HTTPError as e:
        print(f"❌ {description}: HTTP Error {e.code}")
        print(f"   Response: {e.read().decode()}")
        return None
    except URLError as e:
        print(f"❌ {description}: Network Error - {e.reason}")
        return None
    except Exception as e:
        print(f"❌ {description}: {e}")
        return None

def main():
    """Run simple connection tests"""
    print("=" * 60)
    print("SIMPLE ALPACA API CONNECTION TEST")
    print("=" * 60)
    print(f"API URL: {BASE_URL}")
    print(f"API Key: {API_KEY_ID[:8]}..." + "*" * 8)
    print("-" * 60)
    
    # Test 1: Account endpoint
    print("\n[TEST 1] Testing Account Access...")
    account = test_api_call("/v2/account", "Account Info")
    
    if account:
        print(f"   Account ID: {account.get('id', 'N/A')}")
        print(f"   Status: {account.get('status', 'N/A')}")
        print(f"   Equity: ${float(account.get('equity', 0)):,.2f}")
        print(f"   Cash: ${float(account.get('cash', 0)):,.2f}")
        print(f"   Buying Power: ${float(account.get('buying_power', 0)):,.2f}")
        print(f"   Pattern Day Trader: {account.get('pattern_day_trader', False)}")
        
        # Check for restrictions
        if account.get('trading_blocked'):
            print("   ⚠️  WARNING: Trading is blocked!")
        if account.get('account_blocked'):
            print("   ⚠️  WARNING: Account is blocked!")
    
    # Test 2: Positions endpoint
    print("\n[TEST 2] Testing Positions Access...")
    positions = test_api_call("/v2/positions", "Positions")
    
    if positions is not None:
        print(f"   Found {len(positions)} positions")
        for i, pos in enumerate(positions[:5], 1):  # Show max 5
            print(f"   {i}. {pos['symbol']}: {pos['qty']} shares @ ${float(pos['avg_entry_price']):.2f}")
    
    # Test 3: Orders endpoint
    print("\n[TEST 3] Testing Orders Access...")
    orders = test_api_call("/v2/orders?status=open", "Open Orders")
    
    if orders is not None:
        print(f"   Found {len(orders)} open orders")
        for i, order in enumerate(orders[:5], 1):  # Show max 5
            print(f"   {i}. {order['symbol']}: {order['side']} {order['qty']} @ {order['order_type']}")
    
    # Test 4: Clock endpoint
    print("\n[TEST 4] Testing Market Clock...")
    clock = test_api_call("/v2/clock", "Market Clock")
    
    if clock:
        is_open = clock.get('is_open', False)
        status_emoji = "🟢" if is_open else "🔴"
        print(f"   Market Status: {status_emoji} {'OPEN' if is_open else 'CLOSED'}")
        print(f"   Current Time: {clock.get('timestamp', 'N/A')}")
        print(f"   Next Open: {clock.get('next_open', 'N/A')}")
        print(f"   Next Close: {clock.get('next_close', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("SIMPLE CONNECTION TEST COMPLETE")
    print("=" * 60)
    
    # Check if all basic tests passed
    success_count = sum([
        account is not None,
        positions is not None, 
        orders is not None,
        clock is not None
    ])
    
    if success_count == 4:
        print("🎉 ALL BASIC TESTS PASSED!")
        print("✅ Alpaca API connection is working correctly")
        print("✅ Ready to test with full trading system")
    else:
        print(f"⚠️  {success_count}/4 tests passed")
        print("❌ Fix connection issues before proceeding")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)