#!/usr/bin/env python3
"""
Safe bot runner that avoids naming conflicts with the market_adaptive_bot directory.
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path

def run_bot_safely():
    """Run the bot by temporarily renaming the directory to avoid import conflicts."""
    
    # Get the current directory
    current_dir = Path.cwd()
    bot_dir = current_dir / "market_adaptive_bot"
    
    if not bot_dir.exists():
        print("❌ market_adaptive_bot directory not found!")
        return False
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy the bot directory to temp with a different name
        temp_bot_dir = temp_path / "trading_bot"
        print(f"📁 Copying bot to temporary location: {temp_bot_dir}")
        shutil.copytree(bot_dir, temp_bot_dir)
        
        # Change to the temp directory
        os.chdir(temp_bot_dir)
        
        # Add the src directory to Python path
        src_path = temp_bot_dir / "src"
        if src_path.exists():
            sys.path.insert(0, str(src_path))
        
        # Add the project root to Python path for technicals import
        sys.path.insert(0, str(current_dir))
        
        print(f"🔧 Working directory: {os.getcwd()}")
        print(f"🐍 Python path: {sys.path[:3]}...")
        
        try:
            # Import and run the main module
            print("🚀 Starting bot...")
            import main
            return True
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            return False

if __name__ == "__main__":
    print("🤖 Safe Bot Runner")
    print("=" * 50)
    
    success = run_bot_safely()
    
    if success:
        print("✅ Bot started successfully!")
    else:
        print("❌ Failed to start bot")
        sys.exit(1) 