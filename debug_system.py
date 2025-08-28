#!/usr/bin/env python3
"""
Comprehensive System Diagnostic Script
Identifies and fixes all issues in the trading bot system
"""
import sys
import os
import traceback
from pathlib import Path

# Add the project root to the path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

def test_imports():
    """Test all critical imports."""
    print("🔍 Testing critical imports...")
    
    issues = []
    
    try:
        from trading_bot.src.utils.config import Config
        print("✅ Config import successful")
    except Exception as e:
        issues.append(f"Config import failed: {e}")
        print(f"❌ Config import failed: {e}")
    
    try:
        from trading_bot.src.utils.logger import get_logger
        print("✅ Logger import successful")
    except Exception as e:
        issues.append(f"Logger import failed: {e}")
        print(f"❌ Logger import failed: {e}")
    
    try:
        from trading_bot.src.core.models import TimeFrame, CandleData, TradeDecision
        print("✅ Core models import successful")
    except Exception as e:
        issues.append(f"Core models import failed: {e}")
        print(f"❌ Core models import failed: {e}")
    
    try:
        from trading_bot.src.data.data_layer import DataLayer
        print("✅ Data layer import successful")
    except Exception as e:
        issues.append(f"Data layer import failed: {e}")
        print(f"❌ Data layer import failed: {e}")
    
    try:
        from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer
        print("✅ Technical analysis layer import successful")
    except Exception as e:
        issues.append(f"Technical analysis layer import failed: {e}")
        print(f"❌ Technical analysis layer import failed: {e}")
    
    try:
        from trading_bot.src.decision.automated_decision_layer import AutomatedDecisionLayer
        print("✅ Automated decision layer import successful")
    except Exception as e:
        issues.append(f"Automated decision layer import failed: {e}")
        print(f"❌ Automated decision layer import failed: {e}")
    
    try:
        from trading_bot.src.notifications.notification_layer import NotificationLayer
        print("✅ Notification layer import successful")
    except Exception as e:
        issues.append(f"Notification layer import failed: {e}")
        print(f"❌ Notification layer import failed: {e}")
    
    try:
        from api.oanda_api import OandaApi
        print("✅ OANDA API import successful")
    except Exception as e:
        issues.append(f"OANDA API import failed: {e}")
        print(f"❌ OANDA API import failed: {e}")
    
    try:
        from constants.defs import API_KEY, ACCOUNT_ID, OANDA_URL
        print("✅ Constants import successful")
    except Exception as e:
        issues.append(f"Constants import failed: {e}")
        print(f"❌ Constants import failed: {e}")
    
    return issues

def test_configuration():
    """Test configuration loading."""
    print("\n🔍 Testing configuration...")
    
    issues = []
    
    try:
        from trading_bot.src.utils.config import Config
        config = Config()
        print("✅ Configuration loaded successfully")
        
        # Test key attributes
        if hasattr(config, 'trading_pairs'):
            print(f"✅ Trading pairs: {config.trading_pairs}")
        else:
            issues.append("Missing trading_pairs attribute")
        
        if hasattr(config, 'timeframes'):
            print(f"✅ Timeframes: {config.timeframes}")
        else:
            issues.append("Missing timeframes attribute")
            
    except Exception as e:
        issues.append(f"Configuration loading failed: {e}")
        print(f"❌ Configuration loading failed: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
    
    return issues

def test_environment_variables():
    """Test environment variable loading."""
    print("\n🔍 Testing environment variables...")
    
    issues = []
    
    # Check if config.env exists
    config_env_path = Path("config.env")
    if not config_env_path.exists():
        issues.append("config.env file not found")
        print("❌ config.env file not found")
    else:
        print("✅ config.env file found")
    
    # Check required environment variables
    required_vars = ['OANDA_API_KEY', 'OANDA_ACCOUNT_ID']
    for var in required_vars:
        value = os.getenv(var)
        if not value or value == f'your_{var.lower()}_here':
            issues.append(f"Missing or placeholder value for {var}")
            print(f"❌ {var}: {value}")
        else:
            print(f"✅ {var}: {'*' * len(value)}")
    
    return issues

def test_file_structure():
    """Test critical file structure."""
    print("\n🔍 Testing file structure...")
    
    issues = []
    
    critical_files = [
        "trading_bot/config/trading_config.yaml",
        "trading_bot/src/utils/config.py",
        "trading_bot/src/utils/logger.py",
        "trading_bot/src/core/models.py",
        "api/oanda_api.py",
        "constants/defs.py"
    ]
    
    for file_path in critical_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            issues.append(f"Missing file: {file_path}")
            print(f"❌ {file_path}")
    
    return issues

def test_yaml_config():
    """Test YAML configuration loading."""
    print("\n🔍 Testing YAML configuration...")
    
    issues = []
    
    try:
        import yaml
        yaml_path = Path("trading_bot/config/trading_config.yaml")
        if yaml_path.exists():
            with open(yaml_path, 'r') as f:
                config = yaml.safe_load(f)
            print("✅ YAML configuration loaded successfully")
            
            # Test key sections
            required_sections = ['trading', 'risk_management', 'technical_analysis']
            for section in required_sections:
                if section in config:
                    print(f"✅ {section} section found")
                else:
                    issues.append(f"Missing {section} section in YAML")
                    print(f"❌ Missing {section} section")
        else:
            issues.append("YAML configuration file not found")
            print("❌ YAML configuration file not found")
    except Exception as e:
        issues.append(f"YAML configuration loading failed: {e}")
        print(f"❌ YAML configuration loading failed: {e}")
    
    return issues

def main():
    """Run comprehensive system diagnostics."""
    print("🤖 Trading Bot System Diagnostics")
    print("=" * 50)
    
    all_issues = []
    
    # Run all tests
    all_issues.extend(test_imports())
    all_issues.extend(test_configuration())
    all_issues.extend(test_environment_variables())
    all_issues.extend(test_file_structure())
    all_issues.extend(test_yaml_config())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if all_issues:
        print(f"❌ Found {len(all_issues)} issues:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        
        print("\n🔧 RECOMMENDED FIXES:")
        print("1. Set up proper environment variables in config.env")
        print("2. Ensure all required API credentials are configured")
        print("3. Check file permissions and paths")
        print("4. Verify all dependencies are installed")
        
        return False
    else:
        print("✅ All tests passed! System is ready to run.")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
