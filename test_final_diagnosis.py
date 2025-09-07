#!/usr/bin/env python3
"""
Final Alpaca API Diagnosis
Comprehensive testing and troubleshooting guide
"""

import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import base64
from datetime import datetime

# Test credentials from the prompt
API_KEY_ID = "AKHT4KA9CHH6IPIF24TF"
API_SECRET_KEY = "jEXQa4rgIma8p9umGVSfYb0se7EzRUKKjnUwIzIV"

def test_with_different_auth_methods():
    """Test different authentication methods"""
    print("🔐 TESTING AUTHENTICATION METHODS")
    print("=" * 50)
    
    endpoints = {
        "LIVE": "https://api.alpaca.markets",
        "PAPER": "https://paper-api.alpaca.markets"
    }
    
    auth_methods = {
        "Basic Auth": lambda: f"Basic {base64.b64encode(f'{API_KEY_ID}:{API_SECRET_KEY}'.encode()).decode()}",
        "Key Headers": lambda: None  # Will use headers instead
    }
    
    for env_name, base_url in endpoints.items():
        print(f"\n[{env_name}] {base_url}")
        
        for auth_name, auth_func in auth_methods.items():
            print(f"  Testing {auth_name}...")
            
            try:
                url = f"{base_url}/v2/account"
                request = Request(url)
                
                if auth_name == "Basic Auth":
                    request.add_header("Authorization", auth_func())
                else:
                    # Use key headers
                    request.add_header("APCA-API-KEY-ID", API_KEY_ID)
                    request.add_header("APCA-API-SECRET-KEY", API_SECRET_KEY)
                
                with urlopen(request, timeout=5) as response:
                    print(f"    ✅ {auth_name}: HTTP {response.status}")
                    if response.status == 200:
                        return env_name, base_url, auth_name
                        
            except HTTPError as e:
                print(f"    ❌ {auth_name}: HTTP {e.code}")
                if e.code == 403:
                    try:
                        error_data = json.loads(e.read().decode())
                        print(f"      Error: {error_data}")
                    except:
                        pass
            except Exception as e:
                print(f"    ❌ {auth_name}: {e}")
    
    return None, None, None

def show_troubleshooting_guide():
    """Show comprehensive troubleshooting guide"""
    print("\n" + "🚨" * 20)
    print("TROUBLESHOOTING GUIDE")
    print("🚨" * 20)
    
    print("\n1. 📋 VERIFY YOUR ALPACA ACCOUNT:")
    print("   - Log into https://alpaca.markets")
    print("   - Go to 'Paper Trading' or 'Live Trading' section")
    print("   - Check that API access is enabled")
    print("   - Verify your account status is 'ACTIVE'")
    
    print("\n2. 🔑 CHECK YOUR API KEYS:")
    print("   - Go to alpaca.markets → Account → API Keys")
    print("   - Make sure the keys are for the right environment (Live vs Paper)")
    print("   - Try regenerating new API keys")
    print("   - Ensure keys have trading permissions enabled")
    
    print("\n3. 🌐 TEST NETWORK ACCESS:")
    print("   - Can you access https://api.alpaca.markets in browser?")
    print("   - Are you behind a corporate firewall?")
    print("   - Try from a different network")
    
    print("\n4. 💼 ACCOUNT REQUIREMENTS:")
    print("   - Is your account funded?")
    print("   - Has your account been approved for trading?")
    print("   - Are there any restrictions on your account?")
    
    print("\n5. 🔄 ALTERNATIVE TEST:")
    print("   Try this curl command to test directly:")
    print(f"   curl -X GET https://api.alpaca.markets/v2/account \\")
    print(f"        -H 'APCA-API-KEY-ID: {API_KEY_ID}' \\")
    print(f"        -H 'APCA-API-SECRET-KEY: {API_SECRET_KEY}'")

def main():
    """Run comprehensive diagnosis"""
    print("ALPACA API COMPREHENSIVE DIAGNOSIS")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print(f"Python Version: {sys.version}")
    print("-" * 60)
    
    # Test different authentication methods
    working_env, working_url, working_auth = test_with_different_auth_methods()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS RESULTS")
    print("=" * 60)
    
    if working_env:
        print(f"✅ SUCCESS: Found working configuration!")
        print(f"   Environment: {working_env}")
        print(f"   URL: {working_url}")
        print(f"   Auth Method: {working_auth}")
        
        print(f"\n📝 UPDATE YOUR .env FILE:")
        print(f"   APCA_API_BASE_URL={working_url}")
        
        return True
    else:
        print("❌ FAILED: No working configuration found")
        print(f"   API Key ID: {API_KEY_ID}")
        print(f"   Key Length: {len(API_SECRET_KEY)} characters")
        
        show_troubleshooting_guide()
        
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)