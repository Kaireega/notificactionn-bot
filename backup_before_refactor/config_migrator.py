"""
Configuration Migrator - Migrates legacy JSON configs to new YAML format
"""
import json
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import argparse


class ConfigMigrator:
    """Handles migration of configuration files between formats."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.legacy_configs = {
            "bot": self.project_root / "bot" / "settings.json",
            "stream_bot": self.project_root / "stream_bot" / "settings.json"
        }
        self.new_config_path = self.project_root / "market_adaptive_bot" / "config" / "trading_config.yaml"
    
    def load_legacy_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        """Load legacy JSON configuration."""
        config_path = self.legacy_configs.get(config_type)
        if not config_path or not config_path.exists():
            print(f"Warning: {config_type} config not found at {config_path}")
            return None
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {config_type} config: {e}")
            return None
    
    def convert_bot_config(self, legacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy bot config to new format."""
        new_config = {
            "trading_pairs": list(legacy_config.get("pairs", {}).keys()),
            "strategies": {},
            "risk_management": {
                "max_risk_per_trade": legacy_config.get("trade_risk", 0.02),
                "max_open_trades": 5,
                "max_daily_loss": 0.05
            },
            "data_collection": {
                "granularity": "M1",
                "candle_count": 100,
                "update_interval": 10
            },
            "notifications": {
                "enabled": True,
                "telegram": {
                    "enabled": False,
                    "bot_token": "",
                    "chat_id": ""
                },
                "email": {
                    "enabled": False,
                    "smtp_server": "",
                    "smtp_port": 587,
                    "username": "",
                    "password": ""
                }
            },
            "logging": {
                "level": "INFO",
                "file": "trading_bot.log",
                "max_size": "10MB",
                "backup_count": 5
            }
        }
        
        # Convert pair-specific settings
        for pair, settings in legacy_config.get("pairs", {}).items():
            new_config["strategies"][pair] = {
                "type": "technical_analysis",
                "parameters": {
                    "ema_short": settings.get("ema_short", 12),
                    "ema_long": settings.get("ema_long", 26),
                    "rsi_period": settings.get("rsi_period", 14),
                    "rsi_overbought": settings.get("rsi_overbought", 70),
                    "rsi_oversold": settings.get("rsi_oversold", 30)
                },
                "timeframes": ["M1", "M5", "M15"],
                "enabled": True
            }
        
        return new_config
    
    def convert_stream_bot_config(self, legacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy stream bot config to new format."""
        new_config = {
            "streaming": {
                "enabled": True,
                "pairs": legacy_config.get("pairs", []),
                "granularity": legacy_config.get("granularity", "M1"),
                "price_type": "MBA"
            },
            "processing": {
                "workers": legacy_config.get("workers", 4),
                "queue_size": 1000,
                "batch_size": 100
            },
            "risk_management": {
                "max_risk_per_trade": legacy_config.get("trade_risk", 0.02),
                "max_open_trades": legacy_config.get("max_open_trades", 5)
            }
        }
        
        return new_config
    
    def merge_configs(self, bot_config: Dict[str, Any], stream_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge bot and stream bot configs into unified format."""
        merged_config = {
            "version": "2.0.0",
            "environment": "production",
            "trading_pairs": bot_config.get("trading_pairs", []),
            "strategies": bot_config.get("strategies", {}),
            "risk_management": bot_config.get("risk_management", {}),
            "data_collection": {
                **bot_config.get("data_collection", {}),
                **stream_config.get("streaming", {})
            },
            "processing": stream_config.get("processing", {}),
            "notifications": bot_config.get("notifications", {}),
            "logging": bot_config.get("logging", {}),
            "integrations": {
                "legacy_system": {
                    "enabled": True,
                    "fallback": True
                },
                "new_system": {
                    "enabled": True,
                    "primary": True
                }
            }
        }
        
        return merged_config
    
    def save_new_config(self, config: Dict[str, Any], output_path: Optional[Path] = None) -> bool:
        """Save new configuration to YAML file."""
        if output_path is None:
            output_path = self.new_config_path
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            print(f"New configuration saved to: {output_path}")
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate the new configuration."""
        required_sections = [
            "trading_pairs", "strategies", "risk_management", 
            "data_collection", "notifications", "logging"
        ]
        
        for section in required_sections:
            if section not in config:
                print(f"Error: Missing required section '{section}'")
                return False
        
        # Validate trading pairs
        if not config["trading_pairs"]:
            print("Warning: No trading pairs configured")
        
        # Validate risk management
        risk_config = config["risk_management"]
        if not (0 < risk_config.get("max_risk_per_trade", 0) <= 1):
            print("Error: max_risk_per_trade must be between 0 and 1")
            return False
        
        return True
    
    def create_backup(self, config_path: Path) -> bool:
        """Create backup of existing configuration."""
        if not config_path.exists():
            return True
        
        backup_path = config_path.with_suffix(f"{config_path.suffix}.backup")
        try:
            import shutil
            shutil.copy2(config_path, backup_path)
            print(f"Backup created: {backup_path}")
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def migrate(self, create_backup: bool = True, validate: bool = True) -> bool:
        """Perform complete configuration migration."""
        print("Starting configuration migration...")
        
        # Load legacy configs
        bot_config = self.load_legacy_config("bot")
        stream_config = self.load_legacy_config("stream_bot")
        
        if not bot_config and not stream_config:
            print("Error: No legacy configurations found")
            return False
        
        # Convert configs
        new_bot_config = self.convert_bot_config(bot_config) if bot_config else {}
        new_stream_config = self.convert_stream_bot_config(stream_config) if stream_config else {}
        
        # Merge configs
        merged_config = self.merge_configs(new_bot_config, new_stream_config)
        
        # Validate if requested
        if validate and not self.validate_config(merged_config):
            print("Configuration validation failed")
            return False
        
        # Create backup if requested
        if create_backup and self.new_config_path.exists():
            if not self.create_backup(self.new_config_path):
                print("Warning: Could not create backup")
        
        # Save new config
        return self.save_new_config(merged_config)


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description='Migrate legacy JSON configs to new YAML format')
    parser.add_argument('--project-root', default='.', 
                       help='Project root directory (default: current directory)')
    parser.add_argument('--output', '-o', 
                       help='Output path for new configuration')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip creating backup of existing config')
    parser.add_argument('--no-validate', action='store_true',
                       help='Skip configuration validation')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be migrated without making changes')
    
    args = parser.parse_args()
    
    migrator = ConfigMigrator(args.project_root)
    
    if args.dry_run:
        print("DRY RUN - No changes will be made")
        bot_config = migrator.load_legacy_config("bot")
        stream_config = migrator.load_legacy_config("stream_bot")
        
        if bot_config:
            print(f"Bot config found: {len(bot_config.get('pairs', {}))} pairs")
        if stream_config:
            print(f"Stream bot config found: {len(stream_config.get('pairs', []))} pairs")
        
        return
    
    # Perform migration
    success = migrator.migrate(
        create_backup=not args.no_backup,
        validate=not args.no_validate
    )
    
    if success:
        print("✅ Configuration migration completed successfully")
    else:
        print("❌ Configuration migration failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 