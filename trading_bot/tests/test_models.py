"""
Comprehensive tests for core models with edge cases and proper mocking.
"""
import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.models import (
    MarketCondition, TradeSignal, TimeFrame, CandleData, TechnicalIndicators,
    MarketContext, TradeRecommendation, TradeDecision, NotificationMessage,
    UserResponse, TradeExecution, PerformanceMetrics
)


class TestMarketCondition:
    """Test MarketCondition enum functionality."""
    
    def test_market_condition_values(self):
        """Test that all market conditions have correct values."""
        assert MarketCondition.NEWS_REACTIONARY.value == "news_reactionary"
        assert MarketCondition.REVERSAL.value == "reversal"
        assert MarketCondition.BREAKOUT.value == "breakout"
        assert MarketCondition.RANGING.value == "ranging"
        assert MarketCondition.UNKNOWN.value == "unknown"
    
    def test_market_condition_from_string(self):
        """Test creating market conditions from string values."""
        assert MarketCondition("news_reactionary") == MarketCondition.NEWS_REACTIONARY
        assert MarketCondition("reversal") == MarketCondition.REVERSAL
        assert MarketCondition("breakout") == MarketCondition.BREAKOUT
        assert MarketCondition("ranging") == MarketCondition.RANGING
        assert MarketCondition("unknown") == MarketCondition.UNKNOWN
    
    def test_invalid_market_condition(self):
        """Test handling of invalid market condition strings."""
        with pytest.raises(ValueError):
            MarketCondition("invalid_condition")


class TestTradeSignal:
    """Test TradeSignal enum functionality."""
    
    def test_trade_signal_values(self):
        """Test that all trade signals have correct values."""
        assert TradeSignal.BUY.value == "buy"
        assert TradeSignal.SELL.value == "sell"
        assert TradeSignal.HOLD.value == "hold"
    
    def test_trade_signal_from_string(self):
        """Test creating trade signals from string values."""
        assert TradeSignal("buy") == TradeSignal.BUY
        assert TradeSignal("sell") == TradeSignal.SELL
        assert TradeSignal("hold") == TradeSignal.HOLD
    
    def test_invalid_trade_signal(self):
        """Test handling of invalid trade signal strings."""
        with pytest.raises(ValueError):
            TradeSignal("invalid_signal")


class TestTimeFrame:
    """Test TimeFrame enum functionality."""
    
    def test_timeframe_values(self):
        """Test that all timeframes have correct values."""
        assert TimeFrame.M1.value == "M1"
        assert TimeFrame.M5.value == "M5"
        assert TimeFrame.M15.value == "M15"
        assert TimeFrame.M30.value == "M30"
        assert TimeFrame.H1.value == "H1"
        assert TimeFrame.H4.value == "H4"
        assert TimeFrame.D1.value == "D1"
    
    def test_timeframe_from_string(self):
        """Test creating timeframes from string values."""
        assert TimeFrame("M1") == TimeFrame.M1
        assert TimeFrame("M5") == TimeFrame.M5
        assert TimeFrame("M15") == TimeFrame.M15
        assert TimeFrame("H1") == TimeFrame.H1
        assert TimeFrame("D1") == TimeFrame.D1


class TestCandleData:
    """Test CandleData class functionality."""
    
    def test_candle_data_creation_with_decimals(self):
        """Test creating CandleData with Decimal values."""
        timestamp = datetime.utcnow()
        candle = CandleData(
            timestamp=timestamp,
            open=Decimal("1.23456"),
            high=Decimal("1.23500"),
            low=Decimal("1.23400"),
            close=Decimal("1.23480"),
            volume=Decimal("1000.50"),
            pair="EUR_USD",
            timeframe=TimeFrame.M5
        )
        
        assert candle.timestamp == timestamp
        assert candle.open == Decimal("1.23456")
        assert candle.high == Decimal("1.23500")
        assert candle.low == Decimal("1.23400")
        assert candle.close == Decimal("1.23480")
        assert candle.volume == Decimal("1000.50")
        assert candle.pair == "EUR_USD"
        assert candle.timeframe == TimeFrame.M5
    
    def test_candle_data_creation_with_floats(self):
        """Test creating CandleData with float values (auto-conversion to Decimal)."""
        timestamp = datetime.utcnow()
        candle = CandleData(
            timestamp=timestamp,
            open=1.23456,
            high=1.23500,
            low=1.23400,
            close=1.23480,
            volume=1000.50,
            pair="EUR_USD",
            timeframe=TimeFrame.M5
        )
        
        assert isinstance(candle.open, Decimal)
        assert isinstance(candle.high, Decimal)
        assert isinstance(candle.low, Decimal)
        assert isinstance(candle.close, Decimal)
        assert isinstance(candle.volume, Decimal)
        assert float(candle.open) == 1.23456
        assert float(candle.high) == 1.23500
    
    def test_candle_data_creation_with_integers(self):
        """Test creating CandleData with integer values (auto-conversion to Decimal)."""
        timestamp = datetime.utcnow()
        candle = CandleData(
            timestamp=timestamp,
            open=1,
            high=2,
            low=0,
            close=1,
            volume=1000,
            pair="EUR_USD",
            timeframe=TimeFrame.M5
        )
        
        assert isinstance(candle.open, Decimal)
        assert isinstance(candle.high, Decimal)
        assert isinstance(candle.low, Decimal)
        assert isinstance(candle.close, Decimal)
        assert isinstance(candle.volume, Decimal)
        assert int(candle.open) == 1
        assert int(candle.high) == 2
    
    def test_candle_data_without_volume(self):
        """Test creating CandleData without volume."""
        timestamp = datetime.utcnow()
        candle = CandleData(
            timestamp=timestamp,
            open=Decimal("1.23456"),
            high=Decimal("1.23500"),
            low=Decimal("1.23400"),
            close=Decimal("1.23480"),
            pair="EUR_USD",
            timeframe=TimeFrame.M5
        )
        
        assert candle.volume is None
    
    def test_candle_data_defaults(self):
        """Test CandleData default values."""
        timestamp = datetime.utcnow()
        candle = CandleData(
            timestamp=timestamp,
            open=Decimal("1.23456"),
            high=Decimal("1.23500"),
            low=Decimal("1.23400"),
            close=Decimal("1.23480")
        )
        
        assert candle.pair == ""
        assert candle.timeframe == TimeFrame.M5
        assert candle.volume is None


class TestTechnicalIndicators:
    """Test TechnicalIndicators class functionality."""
    
    def test_technical_indicators_creation(self):
        """Test creating TechnicalIndicators with all fields."""
        indicators = TechnicalIndicators(
            rsi=50.0,
            macd=0.001,
            macd_signal=0.002,
            macd_histogram=-0.001,
            ema_fast=1.2345,
            ema_slow=1.2340,
            bollinger_upper=1.2400,
            bollinger_middle=1.2345,
            bollinger_lower=1.2290,
            atr=0.005,
            stoch_k=45.0,
            stoch_d=50.0,
            support_level=1.2300,
            resistance_level=1.2400,
            keltner_upper=1.2390,
            keltner_lower=1.2300,
            keltner_middle=1.2345,
            bb_ma=1.2345,
            rsi_14=50.0,
            macd_line=0.001,
            macd_signal_line=0.002,
            macd_histogram_line=-0.001
        )
        
        assert indicators.rsi == 50.0
        assert indicators.macd == 0.001
        assert indicators.macd_signal == 0.002
        assert indicators.macd_histogram == -0.001
        assert indicators.ema_fast == 1.2345
        assert indicators.ema_slow == 1.2340
        assert indicators.bollinger_upper == 1.2400
        assert indicators.bollinger_middle == 1.2345
        assert indicators.bollinger_lower == 1.2290
        assert indicators.atr == 0.005
        assert indicators.stoch_k == 45.0
        assert indicators.stoch_d == 50.0
        assert indicators.support_level == 1.2300
        assert indicators.resistance_level == 1.2400
        assert indicators.keltner_upper == 1.2390
        assert indicators.keltner_lower == 1.2300
        assert indicators.keltner_middle == 1.2345
        assert indicators.bb_ma == 1.2345
        assert indicators.rsi_14 == 50.0
        assert indicators.macd_line == 0.001
        assert indicators.macd_signal_line == 0.002
        assert indicators.macd_histogram_line == -0.001
    
    def test_technical_indicators_defaults(self):
        """Test TechnicalIndicators default values."""
        indicators = TechnicalIndicators()
        
        assert indicators.rsi is None
        assert indicators.macd is None
        assert indicators.macd_signal is None
        assert indicators.macd_histogram is None
        assert indicators.ema_fast is None
        assert indicators.ema_slow is None
        assert indicators.bollinger_upper is None
        assert indicators.bollinger_middle is None
        assert indicators.bollinger_lower is None
        assert indicators.atr is None
        assert indicators.stoch_k is None
        assert indicators.stoch_d is None
        assert indicators.support_level is None
        assert indicators.resistance_level is None
        assert indicators.keltner_upper is None
        assert indicators.keltner_lower is None
        assert indicators.keltner_middle is None
        assert indicators.bb_ma is None
        assert indicators.rsi_14 is None
        assert indicators.macd_line is None
        assert indicators.macd_signal_line is None
        assert indicators.macd_histogram_line is None


class TestMarketContext:
    """Test MarketContext class functionality."""
    
    def test_market_context_creation(self):
        """Test creating MarketContext with all fields."""
        timestamp = datetime.utcnow()
        context = MarketContext(
            condition=MarketCondition.BREAKOUT,
            volatility=0.015,
            trend_strength=0.8,
            news_sentiment=0.2,
            economic_events=[{"event": "NFP", "impact": "high"}],
            key_levels={"support": 1.2300, "resistance": 1.2400},
            timestamp=timestamp
        )
        
        assert context.condition == MarketCondition.BREAKOUT
        assert context.volatility == 0.015
        assert context.trend_strength == 0.8
        assert context.news_sentiment == 0.2
        assert context.economic_events == [{"event": "NFP", "impact": "high"}]
        assert context.key_levels == {"support": 1.2300, "resistance": 1.2400}
        assert context.timestamp == timestamp
    
    def test_market_context_defaults(self):
        """Test MarketContext default values."""
        context = MarketContext()
        
        assert context.condition == MarketCondition.UNKNOWN
        assert context.volatility == 0.0
        assert context.trend_strength == 0.0
        assert context.news_sentiment == 0.0
        assert context.economic_events == []
        assert context.key_levels == {}
        assert isinstance(context.timestamp, datetime)


class TestTradeRecommendation:
    """Test TradeRecommendation class functionality."""
    
    def test_trade_recommendation_creation(self):
        """Test creating TradeRecommendation with all fields."""
        timestamp = datetime.utcnow()
        recommendation = TradeRecommendation(
            pair="EUR_USD",
            signal=TradeSignal.BUY,
            entry_price=Decimal("1.2345"),
            stop_loss=Decimal("1.2300"),
            take_profit=Decimal("1.2400"),
            confidence=0.85,
            market_condition=MarketCondition.BREAKOUT,
            reasoning="Strong breakout with volume confirmation",
            risk_reward_ratio=2.5,
            estimated_hold_time=timedelta(hours=2),
            timestamp=timestamp,
            technical_analysis=TechnicalIndicators(rsi=50.0),
            market_context=MarketContext(condition=MarketCondition.BREAKOUT)
        )
        
        assert recommendation.pair == "EUR_USD"
        assert recommendation.signal == TradeSignal.BUY
        assert recommendation.entry_price == Decimal("1.2345")
        assert recommendation.stop_loss == Decimal("1.2300")
        assert recommendation.take_profit == Decimal("1.2400")
        assert recommendation.confidence == 0.85
        assert recommendation.market_condition == MarketCondition.BREAKOUT
        assert recommendation.reasoning == "Strong breakout with volume confirmation"
        assert recommendation.risk_reward_ratio == 2.5
        assert recommendation.estimated_hold_time == timedelta(hours=2)
        assert recommendation.timestamp == timestamp
        assert recommendation.technical_analysis is not None
        assert recommendation.market_context is not None
    
    def test_trade_recommendation_with_float_prices(self):
        """Test creating TradeRecommendation with float prices (auto-conversion)."""
        recommendation = TradeRecommendation(
            pair="EUR_USD",
            signal=TradeSignal.BUY,
            entry_price=1.2345,
            stop_loss=1.2300,
            take_profit=1.2400,
            confidence=0.85,
            market_condition=MarketCondition.BREAKOUT,
            reasoning="Test recommendation"
        )
        
        assert isinstance(recommendation.entry_price, Decimal)
        assert isinstance(recommendation.stop_loss, Decimal)
        assert isinstance(recommendation.take_profit, Decimal)
        assert float(recommendation.entry_price) == 1.2345
        assert float(recommendation.stop_loss) == 1.2300
        assert float(recommendation.take_profit) == 1.2400
    
    def test_trade_recommendation_defaults(self):
        """Test TradeRecommendation default values."""
        recommendation = TradeRecommendation()
        
        assert recommendation.pair == ""
        assert recommendation.signal == TradeSignal.HOLD
        assert recommendation.entry_price is None
        assert recommendation.stop_loss is None
        assert recommendation.take_profit is None
        assert recommendation.confidence == 0.0
        assert recommendation.market_condition == MarketCondition.UNKNOWN
        assert recommendation.reasoning == ""
        assert recommendation.risk_reward_ratio == 0.0
        assert recommendation.estimated_hold_time == timedelta(minutes=30)
        assert isinstance(recommendation.timestamp, datetime)
        assert recommendation.technical_analysis is None
        assert recommendation.market_context is None


class TestTradeDecision:
    """Test TradeDecision class functionality."""
    
    def test_trade_decision_creation(self):
        """Test creating TradeDecision with all fields."""
        timestamp = datetime.utcnow()
        recommendation = TradeRecommendation(
            pair="EUR_USD",
            signal=TradeSignal.BUY,
            entry_price=Decimal("1.2345"),
            confidence=0.85
        )
        
        decision = TradeDecision(
            recommendation=recommendation,
            approved=True,
            position_size=Decimal("1000.00"),
            risk_amount=Decimal("20.00"),
            modified_stop_loss=Decimal("1.2300"),
            modified_take_profit=Decimal("1.2400"),
            risk_management_notes="Position size adjusted for risk",
            timestamp=timestamp
        )
        
        assert decision.recommendation == recommendation
        assert decision.approved is True
        assert decision.position_size == Decimal("1000.00")
        assert decision.risk_amount == Decimal("20.00")
        assert decision.modified_stop_loss == Decimal("1.2300")
        assert decision.modified_take_profit == Decimal("1.2400")
        assert decision.risk_management_notes == "Position size adjusted for risk"
        assert decision.timestamp == timestamp
    
    def test_trade_decision_defaults(self):
        """Test TradeDecision default values."""
        recommendation = TradeRecommendation(pair="EUR_USD", signal=TradeSignal.BUY)
        decision = TradeDecision(recommendation=recommendation)
        
        assert decision.recommendation == recommendation
        assert decision.approved is False
        assert decision.position_size is None
        assert decision.risk_amount is None
        assert decision.modified_stop_loss is None
        assert decision.modified_take_profit is None
        assert decision.risk_management_notes == ""
        assert isinstance(decision.timestamp, datetime)


class TestNotificationMessage:
    """Test NotificationMessage class functionality."""
    
    def test_notification_message_creation(self):
        """Test creating NotificationMessage with all fields."""
        timestamp = datetime.utcnow()
        decision = TradeDecision(recommendation=TradeRecommendation(pair="EUR_USD", signal=TradeSignal.BUY))
        
        message = NotificationMessage(
            title="Trade Alert",
            message="New BUY signal for EUR_USD",
            trade_decision=decision,
            chart_data={"type": "candlestick", "data": []},
            buttons=[{"text": "Accept", "callback": "accept_trade"}],
            priority="high",
            timestamp=timestamp
        )
        
        assert message.title == "Trade Alert"
        assert message.message == "New BUY signal for EUR_USD"
        assert message.trade_decision == decision
        assert message.chart_data == {"type": "candlestick", "data": []}
        assert message.buttons == [{"text": "Accept", "callback": "accept_trade"}]
        assert message.priority == "high"
        assert message.timestamp == timestamp
    
    def test_notification_message_defaults(self):
        """Test NotificationMessage default values."""
        message = NotificationMessage()
        
        assert message.title == ""
        assert message.message == ""
        assert message.trade_decision is None
        assert message.chart_data is None
        assert message.buttons == []
        assert message.priority == "normal"
        assert isinstance(message.timestamp, datetime)


class TestUserResponse:
    """Test UserResponse class functionality."""
    
    def test_user_response_creation(self):
        """Test creating UserResponse with all fields."""
        timestamp = datetime.utcnow()
        response = UserResponse(
            notification_id="12345",
            action="accept",
            user_id="user123",
            timestamp=timestamp,
            modified_params={"stop_loss": 1.2300, "take_profit": 1.2400},
            notes="Adjusted levels based on market conditions"
        )
        
        assert response.notification_id == "12345"
        assert response.action == "accept"
        assert response.user_id == "user123"
        assert response.timestamp == timestamp
        assert response.modified_params == {"stop_loss": 1.2300, "take_profit": 1.2400}
        assert response.notes == "Adjusted levels based on market conditions"
    
    def test_user_response_defaults(self):
        """Test UserResponse default values."""
        response = UserResponse(notification_id="12345", action="accept", user_id="user123")
        
        assert response.notification_id == "12345"
        assert response.action == "accept"
        assert response.user_id == "user123"
        assert isinstance(response.timestamp, datetime)
        assert response.modified_params is None
        assert response.notes == ""


class TestTradeExecution:
    """Test TradeExecution class functionality."""
    
    def test_trade_execution_creation(self):
        """Test creating TradeExecution with all fields."""
        timestamp = datetime.utcnow()
        decision = TradeDecision(recommendation=TradeRecommendation(pair="EUR_USD", signal=TradeSignal.BUY))
        
        execution = TradeExecution(
            trade_decision=decision,
            execution_price=Decimal("1.2345"),
            execution_time=timestamp,
            trade_id="TRADE_12345",
            broker_response={"status": "filled", "order_id": "ORDER_123"},
            status="filled"
        )
        
        assert execution.trade_decision == decision
        assert execution.execution_price == Decimal("1.2345")
        assert execution.execution_time == timestamp
        assert execution.trade_id == "TRADE_12345"
        assert execution.broker_response == {"status": "filled", "order_id": "ORDER_123"}
        assert execution.status == "filled"
    
    def test_trade_execution_with_float_price(self):
        """Test creating TradeExecution with float price (auto-conversion)."""
        decision = TradeDecision(recommendation=TradeRecommendation(pair="EUR_USD", signal=TradeSignal.BUY))
        execution = TradeExecution(
            trade_decision=decision,
            execution_price=1.2345,
            execution_time=datetime.utcnow()
        )
        
        assert isinstance(execution.execution_price, Decimal)
        assert float(execution.execution_price) == 1.2345
    
    def test_trade_execution_defaults(self):
        """Test TradeExecution default values."""
        decision = TradeDecision(recommendation=TradeRecommendation(pair="EUR_USD", signal=TradeSignal.BUY))
        execution = TradeExecution(
            trade_decision=decision,
            execution_price=Decimal("1.2345"),
            execution_time=datetime.utcnow()
        )
        
        assert execution.trade_decision == decision
        assert execution.execution_price == Decimal("1.2345")
        assert isinstance(execution.execution_time, datetime)
        assert execution.trade_id is None
        assert execution.broker_response is None
        assert execution.status == "pending"


class TestPerformanceMetrics:
    """Test PerformanceMetrics class functionality."""
    
    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics with all fields."""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(days=7)
        
        metrics = PerformanceMetrics(
            total_trades=100,
            winning_trades=65,
            losing_trades=35,
            win_rate=0.65,
            total_profit=Decimal("5000.00"),
            total_loss=Decimal("2000.00"),
            net_profit=Decimal("3000.00"),
            max_drawdown=Decimal("500.00"),
            sharpe_ratio=1.5,
            average_win=Decimal("76.92"),
            average_loss=Decimal("57.14"),
            profit_factor=2.5,
            period_start=start_time,
            period_end=end_time
        )
        
        assert metrics.total_trades == 100
        assert metrics.winning_trades == 65
        assert metrics.losing_trades == 35
        assert metrics.win_rate == 0.65
        assert metrics.total_profit == Decimal("5000.00")
        assert metrics.total_loss == Decimal("2000.00")
        assert metrics.net_profit == Decimal("3000.00")
        assert metrics.max_drawdown == Decimal("500.00")
        assert metrics.sharpe_ratio == 1.5
        assert metrics.average_win == Decimal("76.92")
        assert metrics.average_loss == Decimal("57.14")
        assert metrics.profit_factor == 2.5
        assert metrics.period_start == start_time
        assert metrics.period_end == end_time
    
    def test_performance_metrics_with_float_values(self):
        """Test creating PerformanceMetrics with float values (auto-conversion)."""
        metrics = PerformanceMetrics(
            total_trades=100,
            winning_trades=65,
            losing_trades=35,
            win_rate=0.65,
            total_profit=5000.00,
            total_loss=2000.00,
            net_profit=3000.00,
            max_drawdown=500.00,
            sharpe_ratio=1.5,
            average_win=76.92,
            average_loss=57.14,
            profit_factor=2.5
        )
        
        assert isinstance(metrics.total_profit, Decimal)
        assert isinstance(metrics.total_loss, Decimal)
        assert isinstance(metrics.net_profit, Decimal)
        assert isinstance(metrics.max_drawdown, Decimal)
        assert isinstance(metrics.average_win, Decimal)
        assert isinstance(metrics.average_loss, Decimal)
        assert float(metrics.total_profit) == 5000.00
        assert float(metrics.net_profit) == 3000.00
    
    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics default values."""
        metrics = PerformanceMetrics()
        
        assert metrics.total_trades == 0
        assert metrics.winning_trades == 0
        assert metrics.losing_trades == 0
        assert metrics.win_rate == 0.0
        assert metrics.total_profit == Decimal('0')
        assert metrics.total_loss == Decimal('0')
        assert metrics.net_profit == Decimal('0')
        assert metrics.max_drawdown == Decimal('0')
        assert metrics.sharpe_ratio == 0.0
        assert metrics.average_win == Decimal('0')
        assert metrics.average_loss == Decimal('0')
        assert metrics.profit_factor == 0.0
        assert isinstance(metrics.period_start, datetime)
        assert isinstance(metrics.period_end, datetime)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_candle_data_invalid_price_relationships(self):
        """Test CandleData with invalid price relationships (high < low)."""
        timestamp = datetime.utcnow()
        # This should still create the object, but the data would be invalid
        candle = CandleData(
            timestamp=timestamp,
            open=Decimal("1.2350"),
            high=Decimal("1.2300"),  # High is lower than low
            low=Decimal("1.2400"),   # Low is higher than high
            close=Decimal("1.2345")
        )
        
        # The object should still be created, but the data is logically invalid
        assert candle.high == Decimal("1.2300")
        assert candle.low == Decimal("1.2400")
    
    def test_technical_indicators_extreme_values(self):
        """Test TechnicalIndicators with extreme values."""
        indicators = TechnicalIndicators(
            rsi=100.0,  # Maximum RSI
            rsi_14=0.0,  # Minimum RSI
            macd=999999.0,  # Very large MACD
            macd_signal=-999999.0,  # Very negative signal
            atr=0.0,  # Zero ATR
            stoch_k=100.0,  # Maximum stochastic
            stoch_d=0.0  # Minimum stochastic
        )
        
        assert indicators.rsi == 100.0
        assert indicators.rsi_14 == 0.0
        assert indicators.macd == 999999.0
        assert indicators.macd_signal == -999999.0
        assert indicators.atr == 0.0
        assert indicators.stoch_k == 100.0
        assert indicators.stoch_d == 0.0
    
    def test_trade_recommendation_zero_confidence(self):
        """Test TradeRecommendation with zero confidence."""
        recommendation = TradeRecommendation(
            pair="EUR_USD",
            signal=TradeSignal.BUY,
            confidence=0.0,
            market_condition=MarketCondition.UNKNOWN,
            reasoning="No confidence in this trade"
        )
        
        assert recommendation.confidence == 0.0
        assert recommendation.signal == TradeSignal.BUY  # Signal can still be set even with 0 confidence
    
    def test_performance_metrics_zero_trades(self):
        """Test PerformanceMetrics with zero trades."""
        metrics = PerformanceMetrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_profit=Decimal('0'),
            total_loss=Decimal('0'),
            net_profit=Decimal('0'),
            max_drawdown=Decimal('0'),
            sharpe_ratio=0.0,
            average_win=Decimal('0'),
            average_loss=Decimal('0'),
            profit_factor=0.0
        )
        
        assert metrics.total_trades == 0
        assert metrics.win_rate == 0.0
        assert metrics.net_profit == Decimal('0')
    
    def test_market_context_extreme_values(self):
        """Test MarketContext with extreme values."""
        context = MarketContext(
            volatility=1.0,  # Maximum volatility
            trend_strength=1.0,  # Maximum trend strength
            news_sentiment=1.0,  # Maximum positive sentiment
            economic_events=[],  # Empty events list
            key_levels={}  # Empty key levels
        )
        
        assert context.volatility == 1.0
        assert context.trend_strength == 1.0
        assert context.news_sentiment == 1.0
        assert context.economic_events == []
        assert context.key_levels == {}
    
    def test_trade_decision_rejected_trade(self):
        """Test TradeDecision with rejected trade."""
        recommendation = TradeRecommendation(
            pair="EUR_USD",
            signal=TradeSignal.BUY,
            confidence=0.9
        )
        
        decision = TradeDecision(
            recommendation=recommendation,
            approved=False,
            risk_management_notes="Trade rejected due to insufficient funds"
        )
        
        assert decision.approved is False
        assert decision.recommendation == recommendation
        assert "insufficient funds" in decision.risk_management_notes
    
    def test_notification_message_empty_content(self):
        """Test NotificationMessage with empty content."""
        message = NotificationMessage(
            title="",
            message="",
            priority="low",
            buttons=[]
        )
        
        assert message.title == ""
        assert message.message == ""
        assert message.priority == "low"
        assert message.buttons == []
        assert message.trade_decision is None
        assert message.chart_data is None 