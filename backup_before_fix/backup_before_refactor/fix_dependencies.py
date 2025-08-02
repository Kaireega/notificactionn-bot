#!/usr/bin/env python3
"""
Fix dependency compatibility issues for the Forex Trading Bot.
This script resolves numpy/pandas compatibility problems.
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"  ✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ {description} failed: {e}")
        print(f"  Error output: {e.stderr}")
        return False

def main():
    """Main dependency fix function."""
    print("🔧 Fixing dependency compatibility issues...")
    print("=" * 50)
    
    # Step 1: Uninstall problematic packages
    print("📦 Step 1: Removing problematic packages...")
    commands = [
        ("pip uninstall pandas numpy -y", "Uninstalling pandas and numpy"),
        ("pip cache purge", "Clearing pip cache"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"⚠️  Warning: {description} failed, but continuing...")
    
    print()
    
    # Step 2: Install compatible versions
    print("📦 Step 2: Installing compatible versions...")
    install_commands = [
        ("pip install numpy==1.24.3", "Installing numpy 1.24.3"),
        ("pip install pandas==2.0.3", "Installing pandas 2.0.3"),
        ("pip install python-dotenv", "Installing python-dotenv"),
        ("pip install requests", "Installing requests"),
    ]
    
    for command, description in install_commands:
        if not run_command(command, description):
            print(f"❌ {description} failed!")
            return False
    
    print()
    
    # Step 3: Test the installation
    print("🧪 Step 3: Testing the installation...")
    test_script = """
import numpy as np
import pandas as pd
print("✅ NumPy version:", np.__version__)
print("✅ Pandas version:", pd.__version__)
print("✅ All imports successful!")
"""
    
    try:
        result = subprocess.run([sys.executable, "-c", test_script], 
                              capture_output=True, text=True, check=True)
        print("  ✅ Dependency test passed!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("  ❌ Dependency test failed!")
        print("  Error:", e.stderr)
        return False
    
    print()
    print("=" * 50)
    print("✅ Dependency fix completed successfully!")
    print()
    print("📋 Next steps:")
    print("1. Test API credentials: python test_api_credentials.py")
    print("2. Start the bot: cd market_adaptive_bot && python main.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 