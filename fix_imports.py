#!/usr/bin/env python3
"""
Script to fix import issues and clear Python cache
"""
import os
import sys
import shutil
from pathlib import Path

def clear_python_cache():
    """Clear all Python cache files."""
    print("🧹 Clearing Python cache...")
    
    # Find and remove .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"  Removed: {file_path}")
                except Exception as e:
                    print(f"  Error removing {file_path}: {e}")
        
        # Remove __pycache__ directories
        for dir_name in dirs:
            if dir_name == '__pycache__':
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    print(f"  Removed: {dir_path}")
                except Exception as e:
                    print(f"  Error removing {dir_path}: {e}")
    
    print("✅ Python cache cleared")

def test_imports():
    """Test if the imports work correctly."""
    print("\n🧪 Testing imports...")
    
    # Add trading_bot/src to path
    trading_bot_src = Path('trading_bot/src')
    if trading_bot_src.exists():
        sys.path.insert(0, str(trading_bot_src))
        print(f"  Added to path: {trading_bot_src}")
    
    try:
        # Test core models import
        from core.models import CandleData, TechnicalIndicators, TimeFrame
        print("  ✅ Core models imported successfully")
        
        # Test technical analyzer import
        from ai.technical_analyzer import TechnicalAnalyzer
        print("  ✅ Technical analyzer imported successfully")
        
        # Test other components
        from data.data_layer import DataLayer
        print("  ✅ Data layer imported successfully")
        
        from decision.decision_layer import DecisionLayer
        print("  ✅ Decision layer imported successfully")
        
        from notifications.notification_layer import NotificationLayer
        print("  ✅ Notification layer imported successfully")
        
        from utils.config import Config
        print("  ✅ Utils imported successfully")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

def main():
    """Main function."""
    print("🔧 Fixing import issues...")
    
    # Clear cache
    clear_python_cache()
    
    # Test imports
    success = test_imports()
    
    if success:
        print("\n✅ All issues fixed! You can now run the bot.")
        print("🚀 Try: cd trading_bot && python3 main.py")
    else:
        print("\n❌ Some issues remain. Please check the error messages above.")

if __name__ == "__main__":
    main() 