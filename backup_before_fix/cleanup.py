#!/usr/bin/env python3
"""
Cleanup script for the Forex Trading Bot codebase.
Removes temporary files, organizes directories, and validates the project structure.
"""
import os
import shutil
import glob
from pathlib import Path

def cleanup_temp_files():
    """Remove temporary files and directories."""
    print("🧹 Cleaning up temporary files...")
    
    # Files to remove
    temp_files = [
        ".DS_Store",
        "*.pyc",
        "*.pyo",
        "__pycache__",
        "*.log",
        "*.tmp",
        "*.bak",
        "*.swp",
        "*.swo",
        "*~"
    ]
    
    # Directories to clean
    temp_dirs = [
        "__pycache__",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        ".mypy_cache",
        ".black_cache"
    ]
    
    removed_count = 0
    
    # Remove temp files
    for pattern in temp_files:
        for file_path in glob.glob(pattern, recursive=True):
            try:
                os.remove(file_path)
                print(f"  ✅ Removed: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"  ⚠️  Could not remove {file_path}: {e}")
    
    # Remove temp directories
    for dir_pattern in temp_dirs:
        for dir_path in glob.glob(f"**/{dir_pattern}", recursive=True):
            if os.path.isdir(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    print(f"  ✅ Removed directory: {dir_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"  ⚠️  Could not remove directory {dir_path}: {e}")
    
    print(f"  📊 Cleaned up {removed_count} temporary files/directories")

def validate_project_structure():
    """Validate the project structure and required files."""
    print("🔍 Validating project structure...")
    
    required_files = [
        "requirements.txt",
        "README.md",
        "config.env",
        "market_adaptive_bot/main.py",
        "market_adaptive_bot/src/",
        "technicals/indicators.py",
        "technicals/patterns.py",
        "api/oanda_api.py",
        "data/",
        "tests/"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"  ✅ Found: {file_path}")
    
    if missing_files:
        print("  ⚠️  Missing files:")
        for file_path in missing_files:
            print(f"    - {file_path}")
    else:
        print("  ✅ All required files present")

def create_directories():
    """Create necessary directories if they don't exist."""
    print("📁 Creating necessary directories...")
    
    directories = [
        "market_adaptive_bot/logs",
        "market_adaptive_bot/logs/trades",
        "data/historical",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created/verified: {directory}")

def update_gitignore():
    """Update .gitignore with common patterns."""
    print("📝 Updating .gitignore...")
    
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Configuration
config.env
.env

# Data
data/historical/
*.csv
*.xlsx

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# Documentation
docs/_build/

# Trading Bot Specific
market_adaptive_bot/logs/
market_adaptive_bot/logs/trades/
*.pkl
*.pickle

# Temporary files
*.tmp
*.bak
*.swp
*.swo
*~
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print("  ✅ Updated .gitignore")

def main():
    """Main cleanup function."""
    print("🚀 Starting Forex Trading Bot cleanup...")
    print("=" * 50)
    
    # Clean up temporary files
    cleanup_temp_files()
    print()
    
    # Create necessary directories
    create_directories()
    print()
    
    # Validate project structure
    validate_project_structure()
    print()
    
    # Update .gitignore
    update_gitignore()
    print()
    
    print("=" * 50)
    print("✅ Cleanup completed successfully!")
    print()
    print("📋 Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Configure environment: cp market_adaptive_bot/env_example.txt config.env")
    print("3. Edit config.env with your API keys")
    print("4. Run tests: python test_api_credentials.py")
    print("5. Start the bot: cd market_adaptive_bot && python main.py")

if __name__ == "__main__":
    main() 