#!/usr/bin/env python3
"""
Simple runner for the Market Adaptive Trading Bot.
"""
import sys
import os
from pathlib import Path

def main():
    """Run the bot from the correct directory."""
    project_root = Path(__file__).parent
    bot_dir = project_root / "trading_bot"
    
    if not bot_dir.exists():
        print("❌ trading_bot directory not found!")
        sys.exit(1)
    
    # Change to the bot directory
    os.chdir(bot_dir)
    
    # Add src to path
    sys.path.insert(0, str(bot_dir / "src"))
    
    try:
        from main import main
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
