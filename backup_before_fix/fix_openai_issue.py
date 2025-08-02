#!/usr/bin/env python3
"""
Fix OpenAI package import issue.
"""
import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Return code: {result.returncode}")
    if result.stdout:
        print(f"STDOUT: {result.stdout}")
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    return result

def main():
    """Fix the OpenAI package issue."""
    print("🔧 Fixing OpenAI package import issue...")
    
    # First, let's try to fix pip itself
    print("\n1. Upgrading pip...")
    run_command(f"{sys.executable} -m pip install --upgrade pip")
    
    # Uninstall openai completely
    print("\n2. Uninstalling openai...")
    run_command(f"{sys.executable} -m pip uninstall openai -y")
    
    # Clear pip cache
    print("\n3. Clearing pip cache...")
    run_command(f"{sys.executable} -m pip cache purge")
    
    # Reinstall openai with a specific version
    print("\n4. Installing openai==1.3.0...")
    result = run_command(f"{sys.executable} -m pip install openai==1.3.0")
    
    if result.returncode == 0:
        print("✅ OpenAI package installed successfully!")
    else:
        print("❌ Failed to install openai. Trying alternative approach...")
        
        # Try installing without version constraint
        print("\n5. Trying to install latest openai...")
        run_command(f"{sys.executable} -m pip install openai")
    
    # Test the import
    print("\n6. Testing openai import...")
    try:
        import openai
        print(f"✅ OpenAI import successful! Version: {openai.__version__}")
    except Exception as e:
        print(f"❌ OpenAI import failed: {e}")
        
        # Try to find what's causing the issue
        print("\n7. Checking for conflicting packages...")
        run_command(f"{sys.executable} -m pip list | grep -i openai")
        
        # Check if there are any market_adaptive_bot references in site-packages
        import site
        for site_dir in site.getsitepackages():
            print(f"\nChecking {site_dir} for market_adaptive_bot references...")
            run_command(f"find {site_dir} -name '*.py' -exec grep -l 'market_adaptive_bot' {{}} \\; 2>/dev/null | head -5")

if __name__ == "__main__":
    main() 