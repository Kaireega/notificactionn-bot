#!/usr/bin/env python3
"""
Test script to verify the bot can start without import errors.
"""
import sys
import os
from pathlib import Path

def test_bot_startup():
    """Test if the bot can be imported and started."""
    print("🧪 Testing bot startup...")
    
    # Add the project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))
    
    try:
        # Test importing the main bot components
        print("  📦 Testing imports...")
        
        # Test technicals
        from technicals.indicators import RSI, MACD, BollingerBands, ATR, KeltnerChannels
        print("    ✅ Technicals imported")
        
        # Test core models
        from core.models import CandleData, TechnicalIndicators, TimeFrame
        print("    ✅ Core models imported")
        
        # Test AI layer
        from ai.technical_analyzer import TechnicalAnalyzer
        print("    ✅ Technical analyzer imported")
        
        # Test data layer
        from data.data_layer import DataLayer
        print("    ✅ Data layer imported")
        
        # Test decision layer
        from decision.decision_layer import DecisionLayer
        print("    ✅ Decision layer imported")
        
        # Test notification layer
        from notifications.notification_layer import NotificationLayer
        print("    ✅ Notification layer imported")
        
        # Test utils
        from utils.config import Config
        print("    ✅ Utils imported")
        
        print("\n✅ All imports successful!")
        print("🚀 Bot should be ready to start!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Check that all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_bot_startup()
    sys.exit(0 if success else 1) 