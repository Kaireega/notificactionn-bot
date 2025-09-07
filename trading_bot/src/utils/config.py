"""
Configuration management for the Technical Trading Bot.
Pure technical analysis - no AI components.
"""
import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any
from dotenv import load_dotenv

from ..core.models import TimeFrame


@dataclass
class TradingConfig:
    """Trading settings."""
    risk_percentage: float = 2.0
    max_trades_per_day: int = 10
    default_timeframe: TimeFrame = TimeFrame.M5
    pairs: List[str] = field(default_factory=lambda: ['EUR_USD', 'USD_JPY', 'GBP_JPY'])


@dataclass
class MarketConditionsConfig:
    """Market conditions settings."""
    volatility_threshold: float = 0.0015
    trend_strength_threshold: float = 0.7
    breakout_threshold: float = 0.0020
    ranging_threshold: float = 0.0008


@dataclass
class RiskManagementConfig:
    """Risk management settings."""
    max_daily_loss: float = 5.0
    max_position_size: float = 10.0
    correlation_limit: float = 0.7
    max_open_trades: int = 3
    stop_loss_atr_multiplier: float = 0.5
    trailing_stop: bool = True
    trailing_stop_atr_multiplier: float = 0.3


@dataclass
class NotificationConfig:
    """Notification settings."""
    telegram_enabled: bool = True
    send_charts: bool = True
    send_analysis: bool = True
    email_enabled: bool = True
    daily_summary: bool = True
    trade_alerts: bool = True
    notification_cooldown: int = 300
    manual_trade_approval: bool = True
    pre_trade_cooldown_seconds: int = 0
    live_trade_enabled: bool = False


@dataclass
class TechnicalAnalysisConfig:
    """Technical analysis settings."""
    confidence_threshold: float = 0.6
    signal_strength_threshold: float = 0.03
    minimum_confidence: float = 0.6
    risk_reward_ratio_minimum: float = 1.8
    analysis_frequency: int = 300
    include_volume_analysis: bool = True
    include_market_context: bool = True


@dataclass
class DataCollectionConfig:
    """Data collection settings."""
    historical_days: int = 30
    update_frequency: int = 60  # seconds
    store_raw_data: bool = True
    compression: bool = True
    backup_frequency: int = 24  # hours


@dataclass
class PerformanceConfig:
    """Performance tracking settings."""
    track_metrics: bool = True
    save_trades: bool = True
    generate_reports: bool = True
    report_frequency: str = "daily"


@dataclass
class SimulationConfig:
    """Simulation (backtest/forward-test) settings."""
    enabled: bool = False
    data_source: str = "csv"  # csv | oanda | db
    start_date: str = "2024-01-01T00:00:00Z"
    end_date: str = "2024-02-01T00:00:00Z"
    initial_balance: float = 10000.0
    slippage_pips: float = 0.1
    spread_pips: float = 0.1
    commission_rate: float = 0.0001  # 0.01%
    execution_delay_ms: int = 100
    csv_dir: str = "data/historical"


class Config:
    """Main configuration class for the technical trading bot."""
    
    def __init__(self, config_path: str = None):
        print("⚙️ [DEBUG] Initializing technical trading configuration...")
        
        # Load environment variables from the correct path
        print("⚙️ [DEBUG] Loading environment variables...")
        env_path = Path(__file__).parent.parent.parent.parent / "config.env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment from {env_path}")
        else:
            load_dotenv()  # Fallback to default .env
            print("⚠️ config.env not found, using default .env")
        
        # Load YAML configuration
        print("⚙️ [DEBUG] Loading YAML configuration...")
        self._load_yaml_config(config_path)
        
        print("✅ [DEBUG] Configuration initialized successfully")
        
        # Initialize sub-configs
        self.trading = TradingConfig()
        self.market_conditions = MarketConditionsConfig()
        self.risk_management = RiskManagementConfig()
        self.notifications = NotificationConfig()
        self.technical_analysis = TechnicalAnalysisConfig()
        self.data_collection = DataCollectionConfig()
        self.performance = PerformanceConfig()
        self.simulation = SimulationConfig()
        
        # Add backtesting alias for compatibility
        self.backtesting = self.simulation
        
        # Load from YAML if available
        if hasattr(self, '_yaml_config'):
            self._load_from_yaml()
        
        # Override with environment variables
        self._load_from_env()
        
        # Validate configuration
        self._validate_config()
        
        # Safety defaults for production readiness
        self.enable_db = False
        self.enable_news = False
    
    def _load_yaml_config(self, config_path: str = None) -> None:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "trading_config.yaml"
        
        try:
            if Path(config_path).exists():
                with open(config_path, 'r') as f:
                    self._yaml_config = yaml.safe_load(f)
                print(f"Loaded configuration from {config_path}")
            else:
                self._yaml_config = {}
                print(f"Configuration file not found at {config_path}, using defaults")
        except Exception as e:
            print(f"Error loading YAML config: {e}")
            self._yaml_config = {}
    
    def _load_from_yaml(self) -> None:
        """Load configuration values from YAML."""
        try:
            # Trading settings
            if 'trading' in self._yaml_config:
                trading = self._yaml_config['trading']
                self.trading.risk_percentage = trading.get('risk_percentage', 2.0)
                self.trading.max_trades_per_day = trading.get('max_trades_per_day', 10)
                self.trading.default_timeframe = TimeFrame(trading.get('default_timeframe', 'M5'))
                self.trading.pairs = trading.get('pairs', ['EUR_USD', 'USD_JPY', 'GBP_JPY'])
            
            # Market conditions
            if 'market_conditions' in self._yaml_config:
                mc = self._yaml_config['market_conditions']
                self.market_conditions.volatility_threshold = mc.get('volatility_threshold', 0.0015)
                self.market_conditions.trend_strength_threshold = mc.get('trend_strength_threshold', 0.7)
                self.market_conditions.breakout_threshold = mc.get('breakout_threshold', 0.0020)
                self.market_conditions.ranging_threshold = mc.get('ranging_threshold', 0.0008)
            
            # Risk management
            if 'risk_management' in self._yaml_config:
                rm = self._yaml_config['risk_management']
                self.risk_management.max_daily_loss = rm.get('max_daily_loss', 5.0)
                self.risk_management.max_position_size = rm.get('max_position_size', 10.0)
                self.risk_management.correlation_limit = rm.get('correlation_limit', 0.7)
                self.risk_management.max_open_trades = rm.get('max_open_trades', 3)
                self.risk_management.stop_loss_atr_multiplier = rm.get('stop_loss_atr_multiplier', 2.0)
                self.risk_management.trailing_stop = rm.get('trailing_stop', True)
                self.risk_management.trailing_stop_atr_multiplier = rm.get('trailing_stop_atr_multiplier', 1.5)
            
            # Notifications
            if 'notifications' in self._yaml_config:
                notif = self._yaml_config['notifications']
                self.notifications.telegram_enabled = notif.get('telegram', {}).get('enabled', True)
                self.notifications.send_charts = notif.get('telegram', {}).get('send_charts', True)
                self.notifications.send_analysis = notif.get('telegram', {}).get('send_analysis', True)
                self.notifications.email_enabled = notif.get('email', {}).get('enabled', True)
                self.notifications.daily_summary = notif.get('email', {}).get('daily_summary', True)
                self.notifications.trade_alerts = notif.get('email', {}).get('trade_alerts', True)
                self.notifications.notification_cooldown = notif.get('notification_cooldown', 300)
                self.notifications.manual_trade_approval = notif.get('manual_trade_approval', True)
                self.notifications.pre_trade_cooldown_seconds = notif.get('pre_trade_cooldown_seconds', 0)
            
            # Technical analysis
            if 'technical_analysis' in self._yaml_config:
                ta = self._yaml_config['technical_analysis']
                self.technical_analysis.confidence_threshold = ta.get('confidence_threshold', 0.6)
                self.technical_analysis.signal_strength_threshold = ta.get('signal_strength_threshold', 0.03)
                self.technical_analysis.minimum_confidence = ta.get('minimum_confidence', 0.6)
                self.technical_analysis.risk_reward_ratio_minimum = ta.get('risk_reward_ratio_minimum', 1.8)
                self.technical_analysis.analysis_frequency = ta.get('analysis_frequency', 300)
                self.technical_analysis.include_volume_analysis = ta.get('include_volume_analysis', True)
                self.technical_analysis.include_market_context = ta.get('include_market_context', True)
            
            # Data collection
            if 'data_collection' in self._yaml_config:
                dc = self._yaml_config['data_collection']
                self.data_collection.historical_days = dc.get('historical_days', 30)
                self.data_collection.update_frequency = dc.get('update_frequency', 60)
                self.data_collection.store_raw_data = dc.get('store_raw_data', True)
                self.data_collection.compression = dc.get('compression', True)
                self.data_collection.backup_frequency = dc.get('backup_frequency', 24)
            
            # Simulation/Backtesting
            if 'simulation' in self._yaml_config:
                sim = self._yaml_config['simulation']
                self.simulation.enabled = sim.get('enabled', False)
                self.simulation.data_source = sim.get('data_source', 'csv')
                self.simulation.start_date = sim.get('start_date', '2024-01-01T00:00:00Z')
                self.simulation.end_date = sim.get('end_date', '2024-02-01T00:00:00Z')
                self.simulation.initial_balance = sim.get('initial_balance', 10000.0)
                self.simulation.slippage_pips = sim.get('slippage_pips', 0.1)
                self.simulation.spread_pips = sim.get('spread_pips', 0.1)
                self.simulation.commission_rate = sim.get('commission_rate', 0.0001)
                self.simulation.execution_delay_ms = sim.get('execution_delay_ms', 100)
                self.simulation.csv_dir = sim.get('csv_dir', 'data/historical')
            
            # Performance
            if 'performance' in self._yaml_config:
                perf = self._yaml_config['performance']
                self.performance.track_metrics = perf.get('track_metrics', True)
                self.performance.save_trades = perf.get('save_trades', True)
                self.performance.generate_reports = perf.get('generate_reports', True)
                self.performance.report_frequency = perf.get('report_frequency', 'daily')
        
        except Exception as e:
            print(f"Error loading from YAML: {e}")
    
    def _load_from_env(self) -> None:
        """Load configuration values from environment variables."""
        try:
            # API Keys (OANDA only - no AI)
            self.oanda_api_key = os.getenv('OANDA_API_KEY', '')
            self.oanda_account_id = os.getenv('OANDA_ACCOUNT_ID', '')
            self.oanda_url = os.getenv('OANDA_URL', 'https://api-fxpractice.oanda.com/v3')
            
            # Telegram
            self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
            self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
            
            # Email
            self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
            self.email_username = os.getenv('EMAIL_USERNAME', '')
            self.email_password = os.getenv('EMAIL_PASSWORD', '')
            
            # Database
            self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
            self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            
            # Trading
            if os.getenv('RISK_PERCENTAGE'):
                self.trading.risk_percentage = float(os.getenv('RISK_PERCENTAGE'))
            if os.getenv('MAX_TRADES_PER_DAY'):
                self.trading.max_trades_per_day = int(os.getenv('MAX_TRADES_PER_DAY'))
            if os.getenv('DEFAULT_TIMEFRAME'):
                self.trading.default_timeframe = TimeFrame(os.getenv('DEFAULT_TIMEFRAME'))
            
            # Technical Analysis
            if os.getenv('TECHNICAL_CONFIDENCE_THRESHOLD'):
                self.technical_analysis.confidence_threshold = float(os.getenv('TECHNICAL_CONFIDENCE_THRESHOLD'))
            
            # Logging
            self.log_level = os.getenv('LOG_LEVEL', 'INFO')
            self.log_file = os.getenv('LOG_FILE', 'logs/trading_bot.log')
            
            # Development
            self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
            self.environment = os.getenv('ENVIRONMENT', 'production')
            
            # Safety toggles
            if os.getenv('ENABLE_DB'):
                self.enable_db = os.getenv('ENABLE_DB', 'false').lower() == 'true'
            if os.getenv('ENABLE_NEWS'):
                self.enable_news = os.getenv('ENABLE_NEWS', 'false').lower() == 'true'
            if os.getenv('LIVE_TRADE_ENABLED'):
                self.notifications.live_trade_enabled = os.getenv('LIVE_TRADE_ENABLED', 'false').lower() == 'true'
        
        except Exception as e:
            print(f"Error loading from environment: {e}")
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        errors = []
        
        # Check required API keys
        if not self.oanda_api_key:
            errors.append("OANDA_API_KEY is required")
        if not self.oanda_account_id:
            errors.append("OANDA_ACCOUNT_ID is required")
        
        # Check notification settings (optional - disable if not configured)
        if self.notifications.telegram_enabled and (not self.telegram_bot_token or self.telegram_bot_token == 'your_telegram_bot_token_here'):
            print("⚠️  WARNING: TELEGRAM_BOT_TOKEN not set - disabling Telegram")
            self.notifications.telegram_enabled = False
        if self.notifications.email_enabled and (not self.email_username or self.email_username == 'your_email_username_here'):
            print("⚠️  WARNING: EMAIL_USERNAME not set - disabling email")
            self.notifications.email_enabled = False
        
        # Check trading settings
        if self.trading.risk_percentage <= 0 or self.trading.risk_percentage > 100:
            errors.append("RISK_PERCENTAGE must be between 0 and 100")
        if self.trading.max_trades_per_day <= 0:
            errors.append("MAX_TRADES_PER_DAY must be positive")
        
        # Check technical analysis settings
        if self.technical_analysis.confidence_threshold < 0 or self.technical_analysis.confidence_threshold > 1:
            errors.append("TECHNICAL_CONFIDENCE_THRESHOLD must be between 0 and 1")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
    
    @property
    def trading_pairs(self) -> List[str]:
        """Get list of trading pairs."""
        return self.trading.pairs
    
    @property
    def timeframes(self) -> List[TimeFrame]:
        """Get list of timeframes to analyze (from YAML if present)."""
        try:
            yaml_tfs = self._yaml_config.get('multi_timeframe', {}).get('timeframes', None) if hasattr(self, '_yaml_config') else None
            if yaml_tfs:
                return [TimeFrame(tf) for tf in yaml_tfs]
        except Exception:
            pass
        return [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15, TimeFrame.H1]
    
    @property
    def data_update_frequency(self) -> int:
        """Get data update frequency in seconds."""
        return self.data_collection.update_frequency
    
    @property
    def technical_confidence_threshold(self) -> float:
        """Get technical confidence threshold."""
        return self.technical_analysis.confidence_threshold
    
    @property
    def technical_model(self) -> str:
        """Get technical analysis model name."""
        return "technical_analysis"  # No AI model needed
    
    @property
    def technical_analysis_frequency(self) -> int:
        """Get technical analysis frequency in seconds."""
        return self.technical_analysis.analysis_frequency
    
    @property
    def telegram_enabled(self) -> bool:
        """Check if Telegram is enabled."""
        return self.notifications.telegram_enabled
    
    @property
    def email_enabled(self) -> bool:
        """Check if email is enabled."""
        return self.notifications.email_enabled
    
    @property
    def send_charts(self) -> bool:
        """Check if charts should be sent."""
        return self.notifications.send_charts
    
    @property
    def max_trades_per_day(self) -> int:
        """Get maximum trades per day."""
        return self.trading.max_trades_per_day
    
    @property
    def min_decision_interval(self) -> int:
        """Get minimum interval between decisions for same pair (seconds)."""
        return 300  # 5 minutes
    
    @property
    def max_volatility_threshold(self) -> float:
        """Get maximum volatility threshold."""
        return 0.01  # 1%
    
    @property
    def notification_cooldown(self) -> int:
        """Get notification cooldown period."""
        return self.notifications.notification_cooldown
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'trading': {
                'risk_percentage': self.trading.risk_percentage,
                'max_trades_per_day': self.trading.max_trades_per_day,
                'default_timeframe': self.trading.default_timeframe.value,
                'pairs': self.trading.pairs
            },
            'market_conditions': {
                'volatility_threshold': self.market_conditions.volatility_threshold,
                'trend_strength_threshold': self.market_conditions.trend_strength_threshold,
                'breakout_threshold': self.market_conditions.breakout_threshold,
                'ranging_threshold': self.market_conditions.ranging_threshold
            },
            'risk_management': {
                'max_daily_loss': self.risk_management.max_daily_loss,
                'max_position_size': self.risk_management.max_position_size,
                'correlation_limit': self.risk_management.correlation_limit,
                'max_open_trades': self.risk_management.max_open_trades,
                'stop_loss_atr_multiplier': self.risk_management.stop_loss_atr_multiplier,
                'trailing_stop': self.risk_management.trailing_stop,
                'trailing_stop_atr_multiplier': self.risk_management.trailing_stop_atr_multiplier
            },
            'notifications': {
                'telegram_enabled': self.notifications.telegram_enabled,
                'send_charts': self.notifications.send_charts,
                'send_analysis': self.notifications.send_analysis,
                'email_enabled': self.notifications.email_enabled,
                'daily_summary': self.notifications.daily_summary,
                'trade_alerts': self.notifications.trade_alerts,
                'notification_cooldown': self.notifications.notification_cooldown
            },
            'technical_analysis': {
                'confidence_threshold': self.technical_analysis.confidence_threshold,
                'signal_strength_threshold': self.technical_analysis.signal_strength_threshold,
                'minimum_confidence': self.technical_analysis.minimum_confidence,
                'risk_reward_ratio_minimum': self.technical_analysis.risk_reward_ratio_minimum,
                'analysis_frequency': self.technical_analysis.analysis_frequency,
                'include_volume_analysis': self.technical_analysis.include_volume_analysis,
                'include_market_context': self.technical_analysis.include_market_context
            }
        } 