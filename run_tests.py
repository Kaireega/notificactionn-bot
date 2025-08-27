#!/usr/bin/env python3
"""
Test Runner Script
Runs all trading bot component tests.
"""

import asyncio
import sys
import os

def main():
    """Run all tests."""
    print("🚀 Starting Trading Bot Tests...")
    print("=" * 50)
    
    # First, validate configuration
    print("\n1️⃣ Validating Configuration...")
    try:
        from validate_config import validate_config
        config_valid = validate_config()
        if not config_valid:
            print("❌ Configuration validation failed. Please fix configuration first.")
            return False
    except Exception as e:
        print(f"❌ Configuration validation error: {e}")
        return False
    
    # Then run component tests
    print("\n2️⃣ Running Component Tests...")
    try:
        from test_bot_components import main as run_component_tests
        asyncio.run(run_component_tests())
        return True
    except Exception as e:
        print(f"❌ Component tests failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
