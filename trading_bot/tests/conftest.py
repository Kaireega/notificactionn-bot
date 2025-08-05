"""
Pytest configuration file with common fixtures and setup for all tests.
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.models import (
    MarketCondition, TradeSignal, TimeFrame, CandleData, TechnicalIndicators,
    MarketContext, TradeRecommendation, TradeDecision
)
# from utils.config import Config  # Commented out - will use mock instead


@pytest.fixture(scope="session")
def mock_config():
    """Create a mock configuration for testing."""
    config = Mock()
    
    # API Configuration
    config.oanda_api_key = "test-api-key"
    config.oanda_account_id = "test-account-id"
    config.oanda_url = "https://api-fxtrade.oanda.com"
    
    # OpenAI Configuration
    config.openai_api_key = "test-openai-key"
    config.ai_model = "gpt-4"
    config.ai_max_tokens = 1000
    config.ai_temperature = 0.3
    config.ai_analysis_frequency = 300
    config.ai_confidence_threshold = 0.7
    
    # Trading Configuration
    config.risk_percentage = 2.0
    config.max_trades_per_day = 10
    config.default_timeframe = TimeFrame.M5
    config.pairs = ["EUR_USD", "USD_JPY", "GBP_JPY"]
    config.timeframes = [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15, TimeFrame.H1]
    
    # Technical Analysis Configuration
    config.technical_analysis_enabled = True
    config.rsi_period = 14
    config.macd_fast = 12
    config.macd_slow = 26
    config.macd_signal = 9
    config.bollinger_period = 20
    config.bollinger_std = 2
    config.atr_period = 14
    config.keltner_period = 20
    config.keltner_atr_period = 10
    
    # Hold Time Configuration
    config.hold_time_settings = {
        "min_hold_time_minutes": 30,
        "max_hold_time_minutes": 300,
        "default_hold_time_minutes": 120,
        "market_condition_hold_times": {
            "news_reactionary": [30, 180],
            "reversal": [60, 300],
            "breakout": [120, 300],
            "ranging": [30, 180]
        }
    }
    
    # Notification Configuration
    config.telegram_enabled = True
    config.telegram_bot_token = "test-bot-token"
    config.telegram_chat_id = "test-chat-id"
    config.email_enabled = False
    config.smtp_server = "smtp.gmail.com"
    config.smtp_port = 587
    config.email_username = "test@example.com"
    config.email_password = "test-password"
    
    # Logging Configuration
    config.log_level = "INFO"
    config.log_file = "test.log"
    
    return config


@pytest.fixture
def sample_candles():
    """Create sample candle data for testing."""
    candles = []
    base_price = 1.2345
    for i in range(50):
        timestamp = datetime.utcnow() - timedelta(minutes=i)
        candle = CandleData(
            timestamp=timestamp,
            open=Decimal(str(base_price + i * 0.0001)),
            high=Decimal(str(base_price + i * 0.0001 + 0.0005)),
            low=Decimal(str(base_price + i * 0.0001 - 0.0005)),
            close=Decimal(str(base_price + i * 0.0001 + 0.0002)),
            volume=Decimal("1000"),
            pair="EUR_USD",
            timeframe=TimeFrame.M5
        )
        candles.append(candle)
    return candles


@pytest.fixture
def sample_indicators():
    """Create sample technical indicators for testing."""
    return TechnicalIndicators(
        rsi=50.0,
        rsi_14=50.0,
        macd=0.001,
        macd_line=0.001,
        macd_signal=0.002,
        macd_signal_line=0.002,
        macd_histogram=-0.001,
        macd_histogram_line=-0.001,
        ema_fast=1.2345,
        ema_slow=1.2340,
        bollinger_upper=1.2400,
        bollinger_middle=1.2345,
        bb_ma=1.2345,
        bollinger_lower=1.2290,
        atr=0.005,
        keltner_upper=1.2390,
        keltner_lower=1.2300,
        keltner_middle=1.2345,
        support_level=1.2300,
        resistance_level=1.2400
    )


@pytest.fixture
def sample_market_context():
    """Create sample market context for testing."""
    return MarketContext(
        condition=MarketCondition.BREAKOUT,
        volatility=0.015,
        trend_strength=0.8,
        news_sentiment=0.2,
        economic_events=[{"event": "NFP", "impact": "high"}],
        key_levels={"support": 1.2300, "resistance": 1.2400}
    )


@pytest.fixture
def sample_recommendation():
    """Create sample trade recommendation for testing."""
    return TradeRecommendation(
        pair="EUR_USD",
        signal=TradeSignal.BUY,
        entry_price=Decimal("1.2345"),
        stop_loss=Decimal("1.2300"),
        take_profit=Decimal("1.2400"),
        confidence=0.85,
        market_condition=MarketCondition.BREAKOUT,
        reasoning="Strong breakout signal",
        risk_reward_ratio=2.5,
        estimated_hold_time=timedelta(hours=2)
    )


@pytest.fixture
def sample_trade_decision(sample_recommendation):
    """Create sample trade decision for testing."""
    return TradeDecision(
        recommendation=sample_recommendation,
        approved=True,
        position_size=Decimal("1000.00"),
        risk_amount=Decimal("20.00"),
        modified_stop_loss=Decimal("1.2300"),
        modified_take_profit=Decimal("1.2400"),
        risk_management_notes="Position size adjusted for risk"
    )


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def sample_candles_by_timeframe(sample_candles):
    """Create sample candles by timeframe for testing."""
    return {
        TimeFrame.M1: sample_candles[:20],
        TimeFrame.M5: sample_candles,
        TimeFrame.M15: sample_candles[:30],
        TimeFrame.H1: sample_candles[:40]
    }


@pytest.fixture
def sample_ai_outputs():
    """Create sample AI outputs for testing."""
    return {
        "analysis": "AI market analysis",
        "confidence": 0.85,
        "reasoning": "Strong technical signals",
        "market_condition": "breakout",
        "risk_assessment": "medium"
    }


@pytest.fixture
def sample_multi_timeframe_analysis():
    """Create sample multi-timeframe analysis for testing."""
    return {
        "consensus": "Multi-timeframe consensus",
        "timeframes_analyzed": 4,
        "confidence": 0.8,
        "trend_direction": "bullish",
        "key_levels": {"support": 1.2300, "resistance": 1.2400}
    }


@pytest.fixture
def sample_risk_assessment():
    """Create sample risk assessment for testing."""
    return {
        "risk_level": "medium",
        "volatility": 0.015,
        "correlation_risk": "low",
        "market_conditions": "favorable",
        "position_size_recommendation": "standard"
    }


@pytest.fixture
def sample_raw_data(sample_candles):
    """Create sample raw data for testing."""
    return {
        "candles": sample_candles,
        "market_data": {
            "spread": 0.0002,
            "volume": 1000,
            "timestamp": datetime.utcnow()
        },
        "technical_data": {
            "indicators": "raw indicator values",
            "patterns": "candlestick patterns"
        }
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Add any global test setup here
    pass


@pytest.fixture(autouse=True)
def teardown_test_environment():
    """Cleanup test environment after each test."""
    yield
    # Add any global test cleanup here
    pass


# Custom markers for different test types
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "ai: mark test as AI-related"
    )
    config.addinivalue_line(
        "markers", "risk: mark test as risk management related"
    )
    config.addinivalue_line(
        "markers", "notification: mark test as notification related"
    )


# Test data generators for edge cases
@pytest.fixture
def extreme_price_candles():
    """Create candles with extreme price values for testing."""
    candles = []
    for i in range(50):
        timestamp = datetime.utcnow() - timedelta(minutes=i)
        candle = CandleData(
            timestamp=timestamp,
            open=Decimal("999999.999999"),
            high=Decimal("999999.999999"),
            low=Decimal("0.000001"),
            close=Decimal("999999.999999"),
            volume=Decimal("999999999"),
            pair="EUR_USD",
            timeframe=TimeFrame.M5
        )
        candles.append(candle)
    return candles


@pytest.fixture
def zero_price_candles():
    """Create candles with zero price values for testing."""
    candles = []
    for i in range(50):
        timestamp = datetime.utcnow() - timedelta(minutes=i)
        candle = CandleData(
            timestamp=timestamp,
            open=Decimal("0"),
            high=Decimal("0"),
            low=Decimal("0"),
            close=Decimal("0"),
            volume=Decimal("0"),
            pair="EUR_USD",
            timeframe=TimeFrame.M5
        )
        candles.append(candle)
    return candles


@pytest.fixture
def extreme_indicators():
    """Create technical indicators with extreme values for testing."""
    return TechnicalIndicators(
        rsi=100.0,  # Maximum RSI
        rsi_14=0.0,  # Minimum RSI
        macd=999999.0,  # Very large MACD
        macd_line=999999.0,
        macd_signal=-999999.0,  # Very negative signal
        macd_signal_line=-999999.0,
        macd_histogram=0.0,  # Zero histogram
        macd_histogram_line=0.0,
        ema_fast=999999.0,
        ema_slow=0.0,
        bollinger_upper=999999.0,
        bollinger_middle=1.2345,
        bb_ma=1.2345,
        bollinger_lower=0.0,
        atr=0.0,  # Zero ATR
        keltner_upper=999999.0,
        keltner_lower=0.0,
        keltner_middle=1.2345,
        support_level=0.0,
        resistance_level=999999.0
    )


@pytest.fixture
def high_confidence_recommendation():
    """Create recommendation with maximum confidence for testing."""
    return TradeRecommendation(
        pair="EUR_USD",
        signal=TradeSignal.BUY,
        entry_price=Decimal("1.2345"),
        stop_loss=Decimal("1.2300"),
        take_profit=Decimal("1.2400"),
        confidence=1.0,  # Maximum confidence
        market_condition=MarketCondition.BREAKOUT,
        reasoning="Maximum confidence signal",
        risk_reward_ratio=5.0,
        estimated_hold_time=timedelta(hours=5)
    )


@pytest.fixture
def low_confidence_recommendation():
    """Create recommendation with minimum confidence for testing."""
    return TradeRecommendation(
        pair="EUR_USD",
        signal=TradeSignal.BUY,
        entry_price=Decimal("1.2345"),
        stop_loss=Decimal("1.2300"),
        take_profit=Decimal("1.2400"),
        confidence=0.0,  # Minimum confidence
        market_condition=MarketCondition.UNKNOWN,
        reasoning="No confidence signal",
        risk_reward_ratio=0.0,
        estimated_hold_time=timedelta(minutes=30)
    )


@pytest.fixture
def hold_recommendation():
    """Create HOLD recommendation for testing."""
    return TradeRecommendation(
        pair="EUR_USD",
        signal=TradeSignal.HOLD,
        entry_price=None,
        stop_loss=None,
        take_profit=None,
        confidence=0.5,
        market_condition=MarketCondition.RANGING,
        reasoning="No clear signal - holding",
        risk_reward_ratio=0.0,
        estimated_hold_time=timedelta(minutes=0)
    ) 