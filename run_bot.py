#!/usr/bin/env python3
"""
Main entry point for the Forex Trading Bot.
This script should be run from the project root directory.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change to the market_adaptive_bot directory
os.chdir(project_root / "market_adaptive_bot")

# Import and run the main bot
if __name__ == "__main__":
    try:
        from main import main
        main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running this from the project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        sys.exit(1)