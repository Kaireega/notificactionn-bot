#!/usr/bin/env python3
"""
Trading Bot Setup and Startup Script
Comprehensive setup, dependency installation, and startup with error handling.
"""

import os
import sys
import subprocess
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingBotSetup:
    """Comprehensive setup and startup for the trading bot."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.src_path = self.project_root / "src"
        self.config_path = self.project_root / "config"
        self.logs_path = self.project_root / "logs"
        
        # Create necessary directories
        self.logs_path.mkdir(exist_ok=True)
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        try:
            version = sys.version_info
            if version.major < 3 or (version.major == 3 and version.minor < 8):
                logger.error(f"Python 3.8+ required, found {version.major}.{version.minor}")
                return False
            logger.info(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
            return True
        except Exception as e:
            logger.error(f"Error checking Python version: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install required dependencies."""
        try:
            logger.info("📦 Installing dependencies...")
            
            # Upgrade pip first
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Install core dependencies first
            core_deps = [
                "pandas>=2.0.0",
                "numpy>=1.24.0", 
                "requests>=2.31.0",
                "python-dotenv>=1.0.0",
                "pyyaml>=6.0.0"
            ]
            
            for dep in core_deps:
                logger.info(f"Installing {dep}...")
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
            
            # Install technical analysis (enhanced)
            ta_deps = [
                "pandas-ta>=0.3.14b0",
                "ta>=0.10.2"
            ]
            
            for dep in ta_deps:
                logger.info(f"Installing {dep}...")
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
            
            # Install trading frameworks
            trading_deps = [
                "backtrader>=1.9.76.123",
                "ccxt>=4.4.0",
                "oandapyV20>=0.7.0"
            ]
            
            for dep in trading_deps:
                logger.info(f"Installing {dep}...")
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
            
            # Install visualization
            viz_deps = [
                "plotly>=5.0.0",
                "kaleido>=0.2.1",
                "mplfinance>=0.12.10b0"
            ]
            
            for dep in viz_deps:
                logger.info(f"Installing {dep}...")
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
            
            # Install notifications and monitoring
            other_deps = [
                "python-telegram-bot>=20.7",
                "fastapi>=0.104.0",
                "uvicorn>=0.24.0",
                "websockets>=12.0",
                "psutil>=5.9.0",
                "openai>=1.3.0",
                "scikit-learn>=1.3.0"
            ]
            
            for dep in other_deps:
                logger.info(f"Installing {dep}...")
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
            
            logger.info("✅ All dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error installing dependencies: {e}")
            return False
    
    def check_environment(self) -> bool:
        """Check environment variables and configuration."""
        try:
            logger.info("🔧 Checking environment...")
            
            # Check if .env file exists
            env_file = self.project_root / ".env"
            if not env_file.exists():
                logger.warning("⚠️  .env file not found. Creating from example...")
                example_file = self.project_root / "env_example.txt"
                if example_file.exists():
                    import shutil
                    shutil.copy(example_file, env_file)
                    logger.info("✅ Created .env file from env_example.txt")
                else:
                    logger.error("❌ env_example.txt not found")
                    return False
            
            # Check required environment variables
            required_vars = [
                "OPENAI_API_KEY",
                "OANDA_API_KEY", 
                "OANDA_ACCOUNT_ID"
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                logger.warning(f"⚠️  Missing environment variables: {missing_vars}")
                logger.info("Please add these to your .env file")
                return False
            
            logger.info("✅ Environment check passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking environment: {e}")
            return False
    
    def check_imports(self) -> bool:
        """Check if all imports work correctly."""
        try:
            logger.info("🔍 Checking imports...")
            
            # Add src to path
            sys.path.insert(0, str(self.src_path))
            
            # Test core imports
            test_imports = [
                "core.models",
                "utils.config", 
                "utils.logger",
                "data.data_layer",
                "ai.ai_analysis_layer",
                "ai.technical_analyzer",
                "ai.multi_timeframe_analyzer",
                "decision.decision_layer",
                "decision.risk_manager",
                "decision.performance_tracker",
                "notifications.notification_layer",
                "notifications.chart_generator"
            ]
            
            for module in test_imports:
                try:
                    __import__(module)
                    logger.info(f"✅ {module}")
                except ImportError as e:
                    logger.error(f"❌ {module}: {e}")
                    return False
            
            logger.info("✅ All imports working correctly")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking imports: {e}")
            return False
    
    def run_startup_checks(self) -> bool:
        """Run comprehensive startup checks."""
        try:
            logger.info("🚀 Running startup checks...")
            
            checks = [
                ("Python Version", self.check_python_version),
                ("Environment", self.check_environment),
                ("Imports", self.check_imports)
            ]
            
            for check_name, check_func in checks:
                logger.info(f"Running {check_name} check...")
                if not check_func():
                    logger.error(f"❌ {check_name} check failed")
                    return False
                logger.info(f"✅ {check_name} check passed")
            
            logger.info("✅ All startup checks passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in startup checks: {e}")
            return False
    
    async def start_trading_bot(self) -> bool:
        """Start the trading bot."""
        try:
            logger.info("🤖 Starting trading bot...")
            
            # Import main after all checks
            sys.path.insert(0, str(self.project_root))
            from main import main
            
            # Run the main function
            await main()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("🛑 Trading bot stopped by user")
            return True
        except Exception as e:
            logger.error(f"❌ Error starting trading bot: {e}")
            return False
    
    def run(self) -> bool:
        """Run the complete setup and startup process."""
        try:
            logger.info("🎯 Trading Bot Setup and Startup")
            logger.info("=" * 50)
            
            # Step 1: Install dependencies
            if not self.install_dependencies():
                logger.error("❌ Failed to install dependencies")
                return False
            
            # Step 2: Run startup checks
            if not self.run_startup_checks():
                logger.error("❌ Startup checks failed")
                return False
            
            # Step 3: Start the trading bot
            logger.info("🚀 Starting trading bot...")
            asyncio.run(self.start_trading_bot())
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False

def main():
    """Main entry point."""
    setup = TradingBotSetup()
    success = setup.run()
    
    if success:
        logger.info("🎉 Trading bot setup and startup completed successfully!")
    else:
        logger.error("❌ Trading bot setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 