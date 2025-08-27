#!/usr/bin/env python3
"""
Debug script to check configuration loading.
"""

import sys
import os

# Add the trading_bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'trading_bot'))

from trading_bot.src.utils.config import Config

def debug_config():
    """Debug configuration loading."""
    print("🔍 Debugging Configuration Loading...")
    print("=" * 50)
    
    # Load configuration first
    config = Config()
    
    # Check environment variables after config is loaded
    print("Environment Variables (after config load):")
    print(f"RISK_PERCENTAGE: {os.getenv('RISK_PERCENTAGE', 'Not set')}")
    print(f"MAX_TRADES_PER_DAY: {os.getenv('MAX_TRADES_PER_DAY', 'Not set')}")
    
    print("\nConfiguration Values:")
    print(f"Trading Risk Percentage: {config.trading.risk_percentage}")
    print(f"Trading Max Trades Per Day: {config.trading.max_trades_per_day}")
    print(f"AI Confidence Threshold: {config.ai_analysis.confidence_threshold}")
    print(f"AI Analysis Frequency: {config.ai_analysis.analysis_frequency}")
    
    # Check YAML config
    if hasattr(config, '_yaml_config'):
        print("\nYAML Config Trading Section:")
        if 'trading' in config._yaml_config:
            trading = config._yaml_config['trading']
            print(f"YAML Risk Percentage: {trading.get('risk_percentage', 'Not found')}")
            print(f"YAML Max Trades: {trading.get('max_trades_per_day', 'Not found')}")
        else:
            print("No trading section in YAML")
    else:
        print("No YAML config loaded")
    
    # Check if environment variables should override YAML
    print("\nExpected Behavior:")
    print("1. YAML loads: risk_percentage=4.0, max_trades_per_day=15")
    print("2. Environment overrides: risk_percentage=4.0, max_trades_per_day=15")
    print("3. Final result should be: risk_percentage=4.0, max_trades_per_day=15")
    print(f"4. Actual result: risk_percentage={config.trading.risk_percentage}, max_trades_per_day={config.trading.max_trades_per_day}")

if __name__ == "__main__":
    debug_config()
