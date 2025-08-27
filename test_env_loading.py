#!/usr/bin/env python3
"""
Test environment variable loading from .env file.
"""

import os
from dotenv import load_dotenv

def test_env_loading():
    """Test if environment variables are loaded from .env file."""
    print("🔍 Testing Environment Variable Loading...")
    print("=" * 50)
    
    # Check before loading
    print("Before load_dotenv():")
    print(f"RISK_PERCENTAGE: {os.getenv('RISK_PERCENTAGE', 'Not set')}")
    print(f"MAX_TRADES_PER_DAY: {os.getenv('MAX_TRADES_PER_DAY', 'Not set')}")
    
    # Load .env file
    print("\nLoading .env file...")
    result = load_dotenv()
    print(f"load_dotenv() result: {result}")
    
    # Check after loading
    print("\nAfter load_dotenv():")
    print(f"RISK_PERCENTAGE: {os.getenv('RISK_PERCENTAGE', 'Not set')}")
    print(f"MAX_TRADES_PER_DAY: {os.getenv('MAX_TRADES_PER_DAY', 'Not set')}")
    
    # Check if .env file exists
    print(f"\n.env file exists: {os.path.exists('.env')}")
    if os.path.exists('.env'):
        print("First few lines of .env file:")
        with open('.env', 'r') as f:
            lines = f.readlines()[:5]
            for line in lines:
                print(f"  {line.strip()}")

if __name__ == "__main__":
    test_env_loading()
