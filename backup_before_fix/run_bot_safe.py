#!/usr/bin/env python3
"""
Safe entry point for the Market Adaptive Trading Bot.
This script temporarily renames the market_adaptive_bot directory to avoid naming conflicts.
"""
import sys
import os
import shutil
from pathlib import Path

def main():
    """Run the bot safely by avoiding naming conflicts."""
    project_root = Path(__file__).parent
    bot_dir = project_root / "market_adaptive_bot"
    temp_dir = project_root / "trading_bot_temp"
    
    if not bot_dir.exists():
        print("❌ market_adaptive_bot directory not found!")
        sys.exit(1)
    
    try:
        # Temporarily rename the directory to avoid conflicts
        print("🔄 Temporarily renaming market_adaptive_bot to avoid naming conflicts...")
        shutil.move(str(bot_dir), str(temp_dir))
        
        # Add the temp directory to Python path
        sys.path.insert(0, str(temp_dir))
        sys.path.insert(0, str(temp_dir / "src"))
        
        # Change to the temp directory
        os.chdir(temp_dir)
        
        # Import and run the main bot
        print("🚀 Starting the trading bot...")
        from main import main
        main()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running this from the project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        sys.exit(1)
    finally:
        # Always restore the original directory name
        try:
            if temp_dir.exists():
                print("🔄 Restoring original directory name...")
                shutil.move(str(temp_dir), str(bot_dir))
        except Exception as e:
            print(f"⚠️  Warning: Could not restore directory name: {e}")

if __name__ == "__main__":
    main() 