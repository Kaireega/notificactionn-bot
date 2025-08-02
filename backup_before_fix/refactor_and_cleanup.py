#!/usr/bin/env python3
"""
Comprehensive Refactoring and Cleanup Script for Market Adaptive Trading Bot

This script performs the following cleanup operations:
1. Consolidates duplicate files and directories
2. Removes obsolete/unused code
3. Standardizes naming conventions
4. Organizes project structure
5. Cleans up imports and dependencies
"""

import os
import shutil
import glob
from pathlib import Path
from typing import List, Dict, Set
import re


class ProjectRefactorer:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.backup_dir = self.project_root / "backup_before_refactor"
        self.removed_files: List[str] = []
        self.consolidated_files: List[str] = []
        
    def create_backup(self):
        """Create a backup of the current project state."""
        print("🔒 Creating backup...")
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        shutil.copytree(self.project_root, self.backup_dir, 
                       ignore=shutil.ignore_patterns('backup_before_refactor', '.git', '.venv', '__pycache__', '*.pyc'))
        print(f"✅ Backup created at: {self.backup_dir}")
    
    def remove_duplicate_requirements(self):
        """Consolidate requirements files."""
        print("📦 Consolidating requirements files...")
        
        # Find all requirements files
        req_files = list(self.project_root.glob("**/requirements*.txt"))
        req_files.extend(list(self.project_root.glob("**/bot_req.txt")))
        req_files.extend(list(self.project_root.glob("**/main_req.txt")))
        req_files.extend(list(self.project_root.glob("**/test_requirements.txt")))
        
        # Keep only the main requirements.txt and test_requirements.txt in market_adaptive_bot
        main_req = self.project_root / "requirements.txt"
        test_req = self.project_root / "market_adaptive_bot" / "test_requirements.txt"
        
        for req_file in req_files:
            if req_file != main_req and req_file != test_req:
                print(f"🗑️  Removing duplicate: {req_file}")
                req_file.unlink()
                self.removed_files.append(str(req_file))
    
    def remove_duplicate_readmes(self):
        """Consolidate README files."""
        print("📚 Consolidating README files...")
        
        # Keep only the main README.md and market_adaptive_bot/README.md
        main_readme = self.project_root / "README.md"
        bot_readme = self.project_root / "market_adaptive_bot" / "README.md"
        
        readme_files = list(self.project_root.glob("**/README*.md"))
        for readme_file in readme_files:
            if readme_file != main_readme and readme_file != bot_readme:
                print(f"🗑️  Removing duplicate README: {readme_file}")
                readme_file.unlink()
                self.removed_files.append(str(readme_file))
    
    def consolidate_config_files(self):
        """Consolidate configuration files."""
        print("⚙️  Consolidating configuration files...")
        
        # Keep config.env in root and env_example.txt in market_adaptive_bot
        main_config = self.project_root / "config.env"
        bot_env_example = self.project_root / "market_adaptive_bot" / "env_example.txt"
        
        config_files = list(self.project_root.glob("**/config*.env"))
        config_files.extend(list(self.project_root.glob("**/env_example*.txt")))
        
        for config_file in config_files:
            if config_file != main_config and config_file != bot_env_example:
                print(f"🗑️  Removing duplicate config: {config_file}")
                config_file.unlink()
                self.removed_files.append(str(config_file))
    
    def remove_obsolete_directories(self):
        """Remove obsolete or unused directories."""
        print("🗂️  Removing obsolete directories...")
        
        obsolete_dirs = [
            "stream_example",  # Replaced by stream_bot
            "docs",  # Empty or unused
        ]
        
        for dir_name in obsolete_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                print(f"🗑️  Removing obsolete directory: {dir_path}")
                shutil.rmtree(dir_path)
                self.removed_files.append(str(dir_path))
    
    def remove_obsolete_files(self):
        """Remove obsolete or unused files."""
        print("📄 Removing obsolete files...")
        
        obsolete_files = [
            "test_imports.py",  # Replaced by test_bot_startup.py
            "run_comprehensive_tests.py",  # Replaced by market_adaptive_bot/run_tests.py
            "config_migrator.py",  # One-time migration script
            "unified_api.py",  # Consolidated into api/
            "integration_analysis.md",  # Outdated documentation
            "run_api_tests.py",  # Consolidated into tests/
            "run_scraping.py",  # Consolidated into scraping/
            "server.py",  # Not used in main bot
            "supervisor-bot.conf",  # Not used
            "setup.sh",  # Replaced by setup_and_start.py
        ]
        
        for file_name in obsolete_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                print(f"🗑️  Removing obsolete file: {file_path}")
                file_path.unlink()
                self.removed_files.append(str(file_path))
    
    def consolidate_test_files(self):
        """Consolidate test files into the main test directory."""
        print("🧪 Consolidating test files...")
        
        # Move test files to market_adaptive_bot/tests/
        test_files_to_move = [
            "test_api_credentials.py",
            "test_bot_startup.py",
        ]
        
        tests_dir = self.project_root / "market_adaptive_bot" / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        for file_name in test_files_to_move:
            src_path = self.project_root / file_name
            dst_path = tests_dir / file_name
            
            if src_path.exists():
                print(f"📁 Moving test file: {src_path} -> {dst_path}")
                shutil.move(str(src_path), str(dst_path))
                self.consolidated_files.append(f"{src_path} -> {dst_path}")
    
    def consolidate_api_files(self):
        """Consolidate API-related files."""
        print("🔌 Consolidating API files...")
        
        # Move API files to api/ directory
        api_files_to_move = [
            "unified_api.py",
        ]
        
        api_dir = self.project_root / "api"
        api_dir.mkdir(exist_ok=True)
        
        for file_name in api_files_to_move:
            src_path = self.project_root / file_name
            if src_path.exists():
                dst_path = api_dir / file_name
                print(f"📁 Moving API file: {src_path} -> {dst_path}")
                shutil.move(str(src_path), str(dst_path))
                self.consolidated_files.append(f"{src_path} -> {dst_path}")
    
    def consolidate_scraping_files(self):
        """Consolidate scraping-related files."""
        print("🕷️  Consolidating scraping files...")
        
        # Move scraping files to scraping/ directory
        scraping_files_to_move = [
            "run_scraping.py",
        ]
        
        scraping_dir = self.project_root / "scraping"
        scraping_dir.mkdir(exist_ok=True)
        
        for file_name in scraping_files_to_move:
            src_path = self.project_root / file_name
            if src_path.exists():
                dst_path = scraping_dir / file_name
                print(f"📁 Moving scraping file: {src_path} -> {dst_path}")
                shutil.move(str(src_path), str(dst_path))
                self.consolidated_files.append(f"{src_path} -> {dst_path}")
    
    def clean_python_cache(self):
        """Remove Python cache files."""
        print("🧹 Cleaning Python cache files...")
        
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
    
    def standardize_file_names(self):
        """Standardize file naming conventions."""
        print("📝 Standardizing file names...")
        
        # Convert to snake_case
        name_mappings = {
            "run_bot.py": "run_bot.py",  # Already correct
            "test_bot_startup.py": "test_bot_startup.py",  # Already correct
            "fix_dependencies.py": "fix_dependencies.py",  # Already correct
        }
        
        for old_name, new_name in name_mappings.items():
            old_path = self.project_root / old_name
            new_path = self.project_root / new_name
            
            if old_path.exists() and old_path != new_path:
                print(f"🔄 Renaming: {old_path} -> {new_path}")
                old_path.rename(new_path)
    
    def update_imports_in_files(self):
        """Update import statements in Python files."""
        print("🔗 Updating import statements...")
        
        python_files = list(self.project_root.glob("**/*.py"))
        
        for py_file in python_files:
            if py_file.is_file():
                self._update_imports_in_file(py_file)
    
    def _update_imports_in_file(self, file_path: Path):
        """Update imports in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Update import paths for moved files
            import_updates = {
                "from tests.test_api_credentials import": "from tests.test_api_credentials import",
                "from tests.test_bot_startup import": "from tests.test_bot_startup import",
                "from api.unified_api import": "from api.unified_api import",
                "from scraping.run_scraping import": "from scraping.run_scraping import",
            }
            
            for old_import, new_import in import_updates.items():
                content = content.replace(old_import, new_import)
            
            # Update relative imports
            content = re.sub(
                r'from \.\.(.*?) import',
                r'from market_adaptive_bot.src.\1 import',
                content
            )
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"🔗 Updated imports in: {file_path}")
                
        except Exception as e:
            print(f"⚠️  Warning: Could not update imports in {file_path}: {e}")
    
    def create_cleanup_report(self):
        """Create a report of all cleanup operations."""
        print("📊 Creating cleanup report...")
        
        report_path = self.project_root / "REFACTOR_REPORT.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Project Refactoring Report\n\n")
            f.write(f"Generated on: {Path().cwd()}\n\n")
            
            f.write("## Removed Files\n\n")
            for file_path in self.removed_files:
                f.write(f"- `{file_path}`\n")
            
            f.write("\n## Consolidated Files\n\n")
            for consolidation in self.consolidated_files:
                f.write(f"- `{consolidation}`\n")
            
            f.write("\n## Summary\n\n")
            f.write(f"- Total files removed: {len(self.removed_files)}\n")
            f.write(f"- Total files consolidated: {len(self.consolidated_files)}\n")
        
        print(f"✅ Cleanup report created: {report_path}")
    
    def run_full_refactor(self):
        """Run the complete refactoring process."""
        print("🚀 Starting comprehensive refactoring...")
        
        # Create backup first
        self.create_backup()
        
        # Perform cleanup operations
        self.remove_duplicate_requirements()
        self.remove_duplicate_readmes()
        self.consolidate_config_files()
        self.remove_obsolete_directories()
        self.remove_obsolete_files()
        self.consolidate_test_files()
        self.consolidate_api_files()
        self.consolidate_scraping_files()
        self.clean_python_cache()
        self.standardize_file_names()
        self.update_imports_in_files()
        
        # Create report
        self.create_cleanup_report()
        
        print("✅ Refactoring completed successfully!")
        print(f"📊 Removed {len(self.removed_files)} files")
        print(f"📁 Consolidated {len(self.consolidated_files)} files")
        print(f"🔒 Backup available at: {self.backup_dir}")


def main():
    """Main function to run the refactoring."""
    refactorer = ProjectRefactorer()
    refactorer.run_full_refactor()


if __name__ == "__main__":
    main() 