#!/usr/bin/env python3
"""
Safe runner that avoids all import conflicts.
"""
import sys
import os
import shutil
from pathlib import Path

def main():
    """Run the bot safely."""
    project_root = Path(__file__).parent
    bot_dir = project_root / "market_adaptive_bot"
    temp_dir = project_root / "bot_temp"
    
    if not bot_dir.exists():
        print("❌ market_adaptive_bot directory not found!")
        sys.exit(1)
    
    try:
        # Temporarily rename to avoid conflicts
        print("🔄 Temporarily renaming directory to avoid conflicts...")
        shutil.move(str(bot_dir), str(temp_dir))
        
        # Add to path
        sys.path.insert(0, str(temp_dir))
        sys.path.insert(0, str(temp_dir / "src"))
        
        # Change directory
        os.chdir(temp_dir)
        
        # Import and run
        print("🚀 Starting bot...")
        from main import main
        main()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        # Always restore the directory name
        try:
            if temp_dir.exists():
                print("🔄 Restoring directory name...")
                shutil.move(str(temp_dir), str(bot_dir))
        except Exception as e:
            print(f"⚠️  Warning: Could not restore directory: {e}")

if __name__ == "__main__":
    main()
