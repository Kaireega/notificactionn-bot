#!/usr/bin/env python3
"""
Test script to verify all imports work correctly.
"""
import sys
from pathlib import Path

def test_imports():
    """Test all critical imports."""
    print("🧪 Testing imports...")
    
    # Add the project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        # Test technicals imports
        print("  📊 Testing technicals imports...")
        from technicals.indicators import RSI, MACD, BollingerBands, ATR, KeltnerChannels
        from technicals.patterns import apply_candle_props, set_candle_patterns
        print("    ✅ Technicals imports successful")
        
        # Test core models
        print("  🧩 Testing core models...")
        from market_adaptive_bot.src.core.models import CandleData, TechnicalIndicators, TimeFrame
        print("    ✅ Core models imports successful")
        
        # Test AI layer
        print("  🧠 Testing AI layer...")
        from market_adaptive_bot.src.ai.technical_analyzer import TechnicalAnalyzer
        print("    ✅ AI layer imports successful")
        
        # Test data layer
        print("  📈 Testing data layer...")
        from market_adaptive_bot.src.data.data_layer import DataLayer
        print("    ✅ Data layer imports successful")
        
        # Test decision layer
        print("  🎯 Testing decision layer...")
        from market_adaptive_bot.src.decision.decision_layer import DecisionLayer
        print("    ✅ Decision layer imports successful")
        
        # Test notification layer
        print("  📱 Testing notification layer...")
        from market_adaptive_bot.src.notifications.notification_layer import NotificationLayer
        print("    ✅ Notification layer imports successful")
        
        # Test utils
        print("  🔧 Testing utils...")
        from market_adaptive_bot.src.utils.config import Config
        print("    ✅ Utils imports successful")
        
        print("\n✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 