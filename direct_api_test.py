#!/usr/bin/env python3
"""
Direct API test to debug OANDA API issues
"""
import requests
import json
import constants.defs as defs

def test_direct_api():
    """Test OANDA API directly with different approaches."""
    
    print("🔍 Direct OANDA API Test")
    print("=" * 50)
    print(f"API URL: {defs.OANDA_URL}")
    print(f"Account ID: {defs.ACCOUNT_ID}")
    print(f"API Key: {defs.API_KEY[:10]}...{defs.API_KEY[-10:] if defs.API_KEY else 'None'}")
    print()
    
    # Test different header formats
    headers_to_test = [
        {
            "Authorization": f"Bearer {defs.API_KEY}",
            "Content-Type": "application/json"
        },
        {
            "Authorization": f"Bearer {defs.API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        {
            "Authorization": f"Bearer {defs.API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Datetime-Format": "UNIX"
        }
    ]
    
    endpoints_to_test = [
        "accounts",
        f"accounts/{defs.ACCOUNT_ID}",
        f"accounts/{defs.ACCOUNT_ID}/summary",
        "instruments"
    ]
    
    for i, headers in enumerate(headers_to_test, 1):
        print(f"\n🔍 Test {i}: Headers = {headers}")
        print("-" * 40)
        
        for endpoint in endpoints_to_test:
            url = f"{defs.OANDA_URL}/{endpoint}"
            print(f"Testing: {endpoint}")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                print(f"  Status: {response.status_code}")
                print(f"  Response: {response.text[:200]}...")
                
                if response.status_code == 200:
                    print(f"  ✅ SUCCESS for {endpoint}!")
                    data = response.json()
                    if endpoint == "accounts":
                        print(f"  Accounts found: {len(data.get('accounts', []))}")
                    elif "summary" in endpoint:
                        print(f"  Account balance: {data.get('account', {}).get('balance', 'N/A')}")
                    elif endpoint == "instruments":
                        print(f"  Instruments found: {len(data.get('instruments', []))}")
                else:
                    print(f"  ❌ Failed: {response.text}")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            print()
    
    # Test with different API key format (without Bearer)
    print("\n🔍 Test without Bearer prefix:")
    print("-" * 40)
    
    headers_no_bearer = {
        "Authorization": defs.API_KEY,
        "Content-Type": "application/json"
    }
    
    url = f"{defs.OANDA_URL}/accounts"
    try:
        response = requests.get(url, headers=headers_no_bearer, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_direct_api()




