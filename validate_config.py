#!/usr/bin/env python3
"""
Configuration Validation Script
Quick check to ensure balanced settings are properly applied.
"""

import sys
import os

# Add the trading_bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'trading_bot'))

from trading_bot.src.utils.config import Config


def validate_config():
    """Validate that balanced settings are properly applied."""
    print("🔍 Validating Trading Bot Configuration...")
    print("=" * 50)
    
    try:
        config = Config()
        
        # Test key balanced settings using correct attribute paths
        tests = [
            ("AI Confidence Threshold", config.ai_analysis.confidence_threshold, 0.6, "Should be 0.6 for balanced approach"),
            ("AI Analysis Frequency", config.ai_analysis.analysis_frequency, 90, "Should be 90 seconds for faster analysis"),
            ("Max Trades Per Day", config.trading.max_trades_per_day, 15, "Should be 15 for more opportunities"),
            ("Risk Percentage", config.trading.risk_percentage, 4.0, "Should be 4.0 for balanced risk"),
            ("Max Daily Loss", config.risk_management.max_daily_loss, 7.0, "Should be 7.0 for more flexibility"),
            ("Max Position Size", config.risk_management.max_position_size, 75000.0, "Should be 75000.0"),
            ("Max Open Trades", config.risk_management.max_open_trades, 4, "Should be 4"),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, actual, expected, description in tests:
            if abs(actual - expected) < 0.01:  # Allow small floating point differences
                print(f"✅ {test_name}: {actual} (Expected: {expected})")
                passed += 1
            else:
                print(f"❌ {test_name}: {actual} (Expected: {expected}) - {description}")
                failed += 1
        
        # Test multi-timeframe settings if available
        if hasattr(config, '_yaml_config') and 'multi_timeframe' in config._yaml_config:
            mtf_config = config._yaml_config['multi_timeframe']
            min_timeframes = mtf_config.get('minimum_timeframes', 3)
            consensus_threshold = mtf_config.get('consensus_threshold', 0.75)
            
            if min_timeframes == 2:
                print(f"✅ Multi-Timeframe Min Timeframes: {min_timeframes} (Expected: 2)")
                passed += 1
            else:
                print(f"❌ Multi-Timeframe Min Timeframes: {min_timeframes} (Expected: 2)")
                failed += 1
                
            if consensus_threshold == 0.65:
                print(f"✅ Multi-Timeframe Consensus Threshold: {consensus_threshold} (Expected: 0.65)")
                passed += 1
            else:
                print(f"❌ Multi-Timeframe Consensus Threshold: {consensus_threshold} (Expected: 0.65)")
                failed += 1
        else:
            print("⚠️ Multi-timeframe settings not found in YAML config")
        
        # Test AI analysis settings if available
        if hasattr(config, '_yaml_config') and 'ai_analysis' in config._yaml_config:
            ai_config = config._yaml_config['ai_analysis']
            risk_reward_min = ai_config.get('risk_reward_ratio_minimum', 2.0)
            
            if risk_reward_min == 1.8:
                print(f"✅ AI Risk/Reward Minimum: {risk_reward_min} (Expected: 1.8)")
                passed += 1
            else:
                print(f"❌ AI Risk/Reward Minimum: {risk_reward_min} (Expected: 1.8)")
                failed += 1
        else:
            print("⚠️ AI analysis settings not found in YAML config")
        
        print("\n" + "=" * 50)
        print(f"Configuration Validation Results:")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if failed == 0:
            print("🎉 All configuration settings are correct!")
            print("Your bot is configured with balanced settings for optimal performance.")
        else:
            print("⚠️ Some configuration settings need adjustment.")
            print("Please update the configuration file with the balanced settings.")
            print("\n💡 To fix, update trading_bot/config/trading_config.yaml with:")
            print("  - confidence_threshold: 0.6")
            print("  - risk_reward_ratio_minimum: 1.8")
            print("  - max_trades_per_day: 15")
            print("  - risk_percentage: 4.0")
            print("  - minimum_timeframes: 2")
            print("  - consensus_threshold: 0.65")
        
        return failed == 0
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = validate_config()
    sys.exit(0 if success else 1)
