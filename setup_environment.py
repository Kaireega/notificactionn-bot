#!/usr/bin/env python3
"""
Comprehensive Environment Setup Script
Fixes all identified issues and prepares the trading bot for production use
"""
import os
import sys
import traceback
from pathlib import Path

def create_production_config():
    """Create a production-ready config.env file."""
    print("🔧 Creating production-ready config.env...")
    
    config_content = """# OANDA API Configuration - PRODUCTION READY
# Replace these placeholder values with your actual OANDA credentials
OANDA_API_KEY=your_actual_oanda_api_key_here
OANDA_ACCOUNT_ID=your_actual_oanda_account_id_here
OANDA_URL=https://api-fxpractice.oanda.com/v3

# Telegram Configuration (Optional - set to false if not using)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Email Configuration (Optional - set to false if not using)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email_username_here
EMAIL_PASSWORD=your_email_password_here

# Database Configuration (Optional - set to false if not using)
MONGODB_URI=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# Trading Configuration - PRODUCTION SETTINGS
RISK_PERCENTAGE=2.0
MAX_TRADES_PER_DAY=10
DEFAULT_TIMEFRAME=M5

# Technical Analysis Configuration
TECHNICAL_CONFIDENCE_THRESHOLD=0.7
TECHNICAL_RISK_REWARD_MINIMUM=2.0

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/trading_bot.log

# Development Configuration - PRODUCTION MODE
DEBUG=False
ENVIRONMENT=production

# Safety Toggles - PRODUCTION SAFE
ENABLE_DB=False
ENABLE_NEWS=False
LIVE_TRADE_ENABLED=False
"""
    
    with open('config.env', 'w') as f:
        f.write(config_content)
    
    print("✅ Production config.env created")
    print("⚠️  IMPORTANT: Replace placeholder values with your actual credentials!")

def create_logs_directory():
    """Create logs directory if it doesn't exist."""
    print("🔧 Creating logs directory...")
    
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create a .gitkeep file to ensure the directory is tracked
    gitkeep_file = logs_dir / ".gitkeep"
    gitkeep_file.touch(exist_ok=True)
    
    print("✅ Logs directory created")

def fix_import_issues():
    """Fix common import issues."""
    print("🔧 Fixing import issues...")
    
    # Create __init__.py files where missing
    init_dirs = [
        "trading_bot/src",
        "trading_bot/src/utils",
        "trading_bot/src/core",
        "trading_bot/src/data",
        "trading_bot/src/ai",
        "trading_bot/src/decision",
        "trading_bot/src/notifications",
        "api",
        "constants",
        "models",
        "infrastructure"
    ]
    
    for init_dir in init_dirs:
        init_file = Path(init_dir) / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"✅ Created {init_file}")

def create_safe_startup_script():
    """Create a safe startup script with proper error handling."""
    print("🔧 Creating safe startup script...")
    
    startup_content = '''#!/usr/bin/env python3
"""
Safe Trading Bot Startup Script
"""
import sys
import os
import traceback
from pathlib import Path

# Add the project root to the path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

def check_environment():
    """Check if environment is properly configured."""
    print("🔍 Checking environment configuration...")
    
    # Check config.env exists
    if not Path("config.env").exists():
        print("❌ config.env file not found!")
        print("Please run: python setup_environment.py")
        return False
    
    # Check required environment variables
    required_vars = ['OANDA_API_KEY', 'OANDA_ACCOUNT_ID']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value == f'your_{var.lower()}_here':
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or placeholder values for: {', '.join(missing_vars)}")
        print("Please update config.env with your actual credentials")
        return False
    
    print("✅ Environment configuration looks good")
    return True

def main():
    """Main startup function."""
    print("🚀 Starting Trading Bot...")
    
    # Check environment first
    if not check_environment():
        print("❌ Environment check failed. Please fix the issues above.")
        sys.exit(1)
    
    try:
        # Import and start the bot
        from trading_bot.main import main as bot_main
        import asyncio
        
        print("✅ All checks passed. Starting bot...")
        asyncio.run(bot_main())
        
    except KeyboardInterrupt:
        print("\\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open('start_bot_safe.py', 'w') as f:
        f.write(startup_content)
    
    # Make it executable
    os.chmod('start_bot_safe.py', 0o755)
    
    print("✅ Safe startup script created: start_bot_safe.py")

def create_readme():
    """Create a comprehensive README for setup."""
    print("🔧 Creating setup README...")
    
    readme_content = """# Trading Bot Setup Guide

## Quick Start

1. **Set up your environment:**
   ```bash
   python setup_environment.py
   ```

2. **Configure your credentials:**
   Edit `config.env` and replace the placeholder values with your actual OANDA API credentials.

3. **Start the bot safely:**
   ```bash
   python start_bot_safe.py
   ```

## Required Credentials

### OANDA API (Required)
- **OANDA_API_KEY**: Your OANDA API key
- **OANDA_ACCOUNT_ID**: Your OANDA account ID

### Optional Services
- **Telegram**: For notifications
- **Email**: For email alerts
- **Database**: For data storage

## Configuration

The bot uses a layered configuration system:

1. **config.env**: Environment variables (API keys, credentials)
2. **trading_bot/config/trading_config.yaml**: Trading parameters
3. **Default values**: Built-in safe defaults

## Safety Features

- **Live trading disabled by default**: Set `LIVE_TRADE_ENABLED=True` to enable
- **Risk management**: Built-in position sizing and stop-loss
- **Error handling**: Comprehensive error catching and logging
- **Graceful shutdown**: Proper cleanup on exit

## Troubleshooting

### Common Issues

1. **"Missing OANDA credentials"**
   - Update `config.env` with your actual API key and account ID

2. **"Import errors"**
   - Run `python setup_environment.py` to fix import issues

3. **"Configuration validation failed"**
   - Check that all required environment variables are set

### Getting Help

1. Check the logs in the `logs/` directory
2. Run `python debug_system.py` for diagnostics
3. Review the configuration files

## Production Deployment

For production use:

1. Set `ENVIRONMENT=production`
2. Set `DEBUG=False`
3. Configure proper logging
4. Set up monitoring and alerts
5. Test thoroughly with paper trading first

## Security Notes

- Never commit your `config.env` file to version control
- Use environment variables for sensitive data
- Regularly rotate your API keys
- Monitor your bot's activity
"""
    
    with open('SETUP_README.md', 'w') as f:
        f.write(readme_content)
    
    print("✅ Setup README created: SETUP_README.md")

def main():
    """Main setup function."""
    print("🔧 Trading Bot Environment Setup")
    print("=" * 50)
    
    try:
        create_production_config()
        create_logs_directory()
        fix_import_issues()
        create_safe_startup_script()
        create_readme()
        
        print("\n" + "=" * 50)
        print("✅ Setup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Edit config.env with your actual OANDA credentials")
        print("2. Run: python start_bot_safe.py")
        print("3. Check SETUP_README.md for detailed instructions")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
