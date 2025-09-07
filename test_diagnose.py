#!/usr/bin/env python3
"""
Alpaca API Diagnostic Test
Diagnoses connection issues and provides troubleshooting guidance
"""

import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import base64

# Test credentials
API_KEY_ID = "AKHT4KA9CHH6IPIF24TF"
API_SECRET_KEY = "jEXQa4rgIma8p9umGVSfYb0se7EzRUKKjnUwIzIV"

def test_paper_vs_live():
    """Test both paper and live endpoints to diagnose the issue"""
    print("🔍 DIAGNOSING ALPACA API ACCESS")
    print("=" * 50)
    
    # Test both paper and live URLs
    endpoints = {
        "LIVE": "https://api.alpaca.markets",
        "PAPER": "https://paper-api.alpaca.markets"
    }
    
    for env_name, base_url in endpoints.items():
        print(f"\n[{env_name} ENVIRONMENT]")
        print(f"URL: {base_url}")
        
        # Create auth header
        credentials = f"{API_KEY_ID}:{API_SECRET_KEY}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        auth_header = f"Basic {encoded_credentials}"
        
        # Test account endpoint
        try:
            url = f"{base_url}/v2/account"
            request = Request(url)
            request.add_header("Authorization", auth_header)
            request.add_header("Content-Type", "application/json")
            
            with urlopen(request, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    print(f"✅ SUCCESS: Account access works")
                    print(f"   Account ID: {data.get('id', 'N/A')}")
                    print(f"   Status: {data.get('status', 'N/A')}")
                    print(f"   Equity: ${float(data.get('equity', 0)):,.2f}")
                    print(f"   Trading Blocked: {data.get('trading_blocked', 'N/A')}")
                    return env_name, base_url
                else:
                    print(f"❌ HTTP {response.status}")
                    
        except HTTPError as e:
            print(f"❌ HTTP Error {e.code}")
            if e.code == 403:
                print("   This usually means:")
                print("   - Invalid API credentials")
                print("   - Wrong environment (paper vs live)")
                print("   - Account permissions issue")
            error_body = e.read().decode()
            if error_body:
                try:
                    error_data = json.loads(error_body)
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw error: {error_body[:200]}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return None, None

def test_key_format():
    """Test if the API keys have the correct format"""
    print("\n🔑 API KEY FORMAT CHECK")
    print("=" * 30)
    
    # Check key formats
    if len(API_KEY_ID) == 20 and API_KEY_ID.startswith('AK'):
        print(f"✅ API Key ID format looks correct: {API_KEY_ID[:8]}...")
    else:
        print(f"❌ API Key ID format looks wrong: {API_KEY_ID}")
        print("   Expected: 20 characters starting with 'AK'")
    
    if len(API_SECRET_KEY) == 40:
        print(f"✅ API Secret Key length is correct: {API_SECRET_KEY[:8]}...")
    else:
        print(f"❌ API Secret Key length is wrong: {len(API_SECRET_KEY)} chars")
        print("   Expected: 40 characters")

def main():
    """Run diagnostics"""
    print("ALPACA API DIAGNOSTIC TOOL")
    print("=" * 50)
    
    # Test key format first
    test_key_format()
    
    # Test both environments
    working_env, working_url = test_paper_vs_live()
    
    print("\n" + "=" * 50)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if working_env:
        print(f"✅ SUCCESS: API works with {working_env} environment")
        print(f"   Working URL: {working_url}")
        print("\n📋 NEXT STEPS:")
        print("1. Update your .env file with the working URL")
        print("2. Update AlpacaConfig to use the correct environment")
        print("3. Re-run the full connection test")
    else:
        print("❌ FAILED: Neither LIVE nor PAPER environments work")
        print("\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Verify your API keys are correct")
        print("2. Check if your account has API access enabled")
        print("3. Ensure your account is not blocked")
        print("4. Try regenerating your API keys in Alpaca dashboard")
        print("5. Contact Alpaca support if issues persist")
    
    return working_env is not None

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)