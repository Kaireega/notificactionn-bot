#!/usr/bin/env python3
"""
Main entry point for the Market Adaptive Trading Bot.
This script should be run from the project root directory.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change to the market_adaptive_bot directory
bot_dir = project_root / "market_adaptive_bot"
os.chdir(bot_dir)

# Add the src directory to the path
sys.path.insert(0, str(bot_dir / "src"))

# Import and run the main bot
if __name__ == "__main__":
    try:
        from main import main
        main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running this from the project root directory")
        print(f"📁 Current working directory: {os.getcwd()}")
        print(f"🐍 Python path: {sys.path[:3]}...")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        sys.exit(1)