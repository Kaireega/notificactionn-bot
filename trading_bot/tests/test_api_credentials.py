#!/usr/bin/env python3
"""
Simple script to test OANDA API credentials
"""

from api.oanda_api import OandaApi
import constants.defs as defs

def test_api_credentials():
    print("🔍 Testing OANDA API credentials...")
    print(f"API URL: {defs.OANDA_URL}")
    print(f"Account ID: {defs.ACCOUNT_ID}")
    print(f"API Key: {defs.API_KEY[:10]}...{defs.API_KEY[-10:]}")
    print("-" * 50)
    
    api = OandaApi()
    
    # Test basic account access
    print("Testing account access...")
    if api.validate_credentials():
        print("✅ Account access successful!")
        
        # Test getting account summary
        print("\nTesting account summary...")
        summary = api.get_account_summary()
        if summary:
            print("✅ Account summary retrieved successfully!")
            print(f"Account Name: {summary.get('name', 'N/A')}")
            print(f"Account Currency: {summary.get('currency', 'N/A')}")
            print(f"Balance: {summary.get('balance', 'N/A')}")
        else:
            print("❌ Failed to get account summary")
            
        # Test getting instruments
        print("\nTesting instruments access...")
        instruments = api.get_account_instruments()
        if instruments:
            print(f"✅ Retrieved {len(instruments)} instruments")
        else:
            print("❌ Failed to get instruments")
            
    else:
        print("❌ Account access failed!")
        print("\nPossible solutions:")
        print("1. Check if your API key is correct")
        print("2. Check if your account ID is correct")
        print("3. Make sure your OANDA account is active")
        print("4. Verify you have API access enabled in your OANDA account")
        print("5. Check if you're using the correct API URL (practice vs live)")

if __name__ == "__main__":
    test_api_credentials() 