#!/usr/bin/env python3
"""
Comprehensive Cleanup and Fix Script for Market Adaptive Trading Bot

This script fixes the naming conflicts and project structure issues.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

class ProjectFixer:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.backup_dir = self.project_root / "backup_before_fix"
        
    def create_backup(self):
        """Create a backup of the current project state."""
        print("🔒 Creating backup...")
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        shutil.copytree(self.project_root, self.backup_dir, 
                       ignore=shutil.ignore_patterns('backup_before_fix', '.git', '.venv', '__pycache__', '*.pyc'))
        print(f"✅ Backup created at: {self.backup_dir}")
    
    def fix_openai_package(self):
        """Fix the OpenAI package import issue."""
        print("🔧 Fixing OpenAI package...")
        
        try:
            # Uninstall openai
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "openai", "-y"], 
                         capture_output=True, text=True)
            
            # Clear cache
            subprocess.run([sys.executable, "-m", "pip", "cache", "purge"], 
                         capture_output=True, text=True)
            
            # Reinstall openai
            result = subprocess.run([sys.executable, "-m", "pip", "install", "openai==1.3.0"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ OpenAI package fixed!")
            else:
                print("⚠️  OpenAI package installation had issues, but continuing...")
                
        except Exception as e:
            print(f"⚠️  Warning: Could not fix OpenAI package: {e}")
    
    def remove_conflicting_files(self):
        """Remove files that might cause naming conflicts."""
        print("🗑️  Removing conflicting files...")
        
        conflicting_files = [
            "fix_openai_issue.py",
            "run_bot_safe.py",
            "comprehensive_cleanup.py",
        ]
        
        for file_name in conflicting_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                print(f"🗑️  Removing: {file_path}")
                file_path.unlink()
    
    def fix_import_paths(self):
        """Fix import paths in Python files."""
        print("🔗 Fixing import paths...")
        
        # Update main.py imports
        main_py = self.project_root / "market_adaptive_bot" / "main.py"
        if main_py.exists():
            with open(main_py, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix the sys.path.append line
            old_path = 'sys.path.append(str(Path(__file__).parent / "src"))'
            new_path = 'sys.path.insert(0, str(Path(__file__).parent / "src"))'
            
            if old_path in content:
                content = content.replace(old_path, new_path)
                with open(main_py, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("✅ Fixed import paths in main.py")
    
    def create_simple_runner(self):
        """Create a simple runner script that avoids naming conflicts."""
        print("🏃 Creating simple runner...")
        
        runner_content = '''#!/usr/bin/env python3
"""
Simple runner for the Market Adaptive Trading Bot.
"""
import sys
import os
from pathlib import Path

def main():
    """Run the bot from the correct directory."""
    project_root = Path(__file__).parent
    bot_dir = project_root / "market_adaptive_bot"
    
    if not bot_dir.exists():
        print("❌ market_adaptive_bot directory not found!")
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
'''
        
        runner_path = self.project_root / "start_bot.py"
        with open(runner_path, 'w', encoding='utf-8') as f:
            f.write(runner_content)
        
        # Make it executable
        os.chmod(runner_path, 0o755)
        print("✅ Created start_bot.py")
    
    def clean_python_cache(self):
        """Remove Python cache files."""
        print("🧹 Cleaning Python cache...")
        
        cache_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            "**/.pytest_cache",
        ]
        
        for pattern in cache_patterns:
            for cache_path in self.project_root.glob(pattern):
                if cache_path.is_dir():
                    shutil.rmtree(cache_path)
                else:
                    cache_path.unlink()
                print(f"🗑️  Removed cache: {cache_path}")
    
    def test_imports(self):
        """Test that imports work correctly."""
        print("🧪 Testing imports...")
        
        try:
            # Test basic imports
            import sys
            import os
            print("✅ Basic imports work")
            
            # Test openai import
            import openai
            print(f"✅ OpenAI import works (version: {openai.__version__})")
            
            # Test project imports
            bot_dir = self.project_root / "market_adaptive_bot"
            sys.path.insert(0, str(bot_dir / "src"))
            
            from core.models import MarketCondition
            print("✅ Project imports work")
            
        except Exception as e:
            print(f"❌ Import test failed: {e}")
            return False
        
        return True
    
    def run_full_fix(self):
        """Run the complete fix process."""
        print("🚀 Starting comprehensive fix...")
        
        # Create backup
        self.create_backup()
        
        # Fix issues
        self.fix_openai_package()
        self.remove_conflicting_files()
        self.fix_import_paths()
        self.create_simple_runner()
        self.clean_python_cache()
        
        # Test imports
        if self.test_imports():
            print("✅ All fixes applied successfully!")
            print("🎯 You can now run the bot with: python start_bot.py")
        else:
            print("⚠️  Some issues remain. Check the error messages above.")
        
        print(f"🔒 Backup available at: {self.backup_dir}")


def main():
    """Main function."""
    fixer = ProjectFixer()
    fixer.run_full_fix()


if __name__ == "__main__":
    main() 