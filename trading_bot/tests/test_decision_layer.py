"""
Comprehensive tests for decision layer with edge cases and proper mocking.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from decision.decision_layer import DecisionLayer
from core.models import (
    MarketCondition, TradeSignal, TimeFrame, CandleData, TechnicalIndicators,
    MarketContext, TradeRecommendation, TradeDecision
)
from utils.config import Config


class TestDecisionLayer:
    """Test DecisionLayer class functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock(spec=Config)
        config.risk_percentage = 2.0
        config.max_trades_per_day = 10
        config.default_timeframe = TimeFrame.M5
        config.pairs = ["EUR_USD", "USD_JPY", "GBP_JPY"]
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
        return config
    
    @pytest.fixture
    def sample_recommendation(self):
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
    def sample_market_context(self):
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
    def sample_indicators(self):
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
    def decision_layer(self, mock_config):
        """Create DecisionLayer instance for testing."""
        with patch('decision.decision_layer.RiskManager') as mock_risk_manager, \
             patch('decision.decision_layer.PerformanceTracker') as mock_performance_tracker, \
             patch('decision.decision_layer.EnhancedExcelTradeRecorder') as mock_recorder:
            
            layer = DecisionLayer(mock_config)
            layer.logger = Mock()
            layer.risk_manager = Mock()
            layer.performance_tracker = Mock()
            layer.trade_recorder = Mock()
            return layer
    
    def test_decision_layer_initialization(self, mock_config):
        """Test DecisionLayer initialization."""
        with patch('decision.decision_layer.RiskManager') as mock_risk_manager, \
             patch('decision.decision_layer.PerformanceTracker') as mock_performance_tracker, \
             patch('decision.decision_layer.EnhancedExcelTradeRecorder') as mock_recorder:
            
            layer = DecisionLayer(mock_config)
            
            assert layer.config == mock_config
            assert layer.logger is not None
            assert layer.risk_manager is not None
            assert layer.performance_tracker is not None
            assert layer.trade_recorder is not None
            assert layer._daily_trades == 0
            assert layer._last_reset_date == datetime.utcnow().date()
            
            # Verify components were initialized
            mock_risk_manager.assert_called_once_with(mock_config)
            mock_performance_tracker.assert_called_once_with(mock_config)
            mock_recorder.assert_called_once_with(mock_config)
    
    def test_reset_daily_counters_new_day(self, decision_layer):
        """Test _reset_daily_counters when it's a new day."""
        # Set last reset date to yesterday
        decision_layer._last_reset_date = datetime.utcnow().date() - timedelta(days=1)
        decision_layer._daily_trades = 5
        
        decision_layer._reset_daily_counters()
        
        assert decision_layer._daily_trades == 0
        assert decision_layer._last_reset_date == datetime.utcnow().date()
        decision_layer.logger.info.assert_called_with("Daily trade counters reset")
    
    def test_reset_daily_counters_same_day(self, decision_layer):
        """Test _reset_daily_counters when it's the same day."""
        # Set last reset date to today
        decision_layer._last_reset_date = datetime.utcnow().date()
        decision_layer._daily_trades = 5
        
        decision_layer._reset_daily_counters()
        
        # Should not reset counters
        assert decision_layer._daily_trades == 5
        assert decision_layer._last_reset_date == datetime.utcnow().date()
        decision_layer.logger.info.assert_not_called()
    
    def test_can_place_trade_below_limit(self, decision_layer):
        """Test _can_place_trade when below daily limit."""
        decision_layer._daily_trades = 5
        decision_layer.config.max_trades_per_day = 10
        
        assert decision_layer._can_place_trade() is True
    
    def test_can_place_trade_at_limit(self, decision_layer):
        """Test _can_place_trade when at daily limit."""
        decision_layer._daily_trades = 10
        decision_layer.config.max_trades_per_day = 10
        
        assert decision_layer._can_place_trade() is False
    
    def test_can_place_trade_above_limit(self, decision_layer):
        """Test _can_place_trade when above daily limit."""
        decision_layer._daily_trades = 15
        decision_layer.config.max_trades_per_day = 10
        
        assert decision_layer._can_place_trade() is False
    
    @pytest.mark.asyncio
    async def test_process_recommendation_approved(self, decision_layer, sample_recommendation, sample_market_context, sample_indicators):
        """Test successful recommendation processing with approval."""
        # Mock risk manager to approve trade
        decision_layer.risk_manager.evaluate_trade = AsyncMock(return_value=True)
        decision_layer.risk_manager.calculate_position_size = AsyncMock(return_value=Decimal("1000.00"))
        decision_layer.risk_manager.calculate_risk_amount = AsyncMock(return_value=Decimal("20.00"))
        
        # Mock performance tracker
        decision_layer.performance_tracker.get_daily_performance = AsyncMock(return_value={"total_trades": 5})
        
        # Mock trade recorder
        decision_layer.trade_recorder.record_complete_trade_decision = AsyncMock()
        
        # Set up for trade approval
        decision_layer._daily_trades = 5
        decision_layer.config.max_trades_per_day = 10
        
        current_price = Decimal("1.2345")
        candles_by_timeframe = {TimeFrame.M5: [Mock()]}
        ai_outputs = {"analysis": "AI analysis"}
        multi_timeframe_analysis = {"consensus": "Multi-timeframe consensus"}
        risk_assessment = {"risk_level": "medium"}
        raw_data = {"candles": [Mock()]}
        
        decision = await decision_layer.process_recommendation(
            sample_recommendation, current_price, sample_market_context,
            technical_indicators=sample_indicators,
            candles_by_timeframe=candles_by_timeframe,
            ai_outputs=ai_outputs,
            multi_timeframe_analysis=multi_timeframe_analysis,
            risk_assessment=risk_assessment,
            raw_data=raw_data
        )
        
        assert decision is not None
        assert decision.approved is True
        assert decision.recommendation == sample_recommendation
        assert decision.position_size == Decimal("1000.00")
        assert decision.risk_amount == Decimal("20.00")
        assert decision.modified_stop_loss == sample_recommendation.stop_loss
        assert decision.modified_take_profit == sample_recommendation.take_profit
        assert "Position size adjusted for risk" in decision.risk_management_notes
        
        # Verify trade recorder was called
        decision_layer.trade_recorder.record_complete_trade_decision.assert_called_once()
        
        # Verify daily trade count was incremented
        assert decision_layer._daily_trades == 6
        
        # Verify risk manager was called
        decision_layer.risk_manager.evaluate_trade.assert_called_once()
        decision_layer.risk_manager.calculate_position_size.assert_called_once()
        decision_layer.risk_manager.calculate_risk_amount.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_recommendation_rejected_by_risk_manager(self, decision_layer, sample_recommendation, sample_market_context, sample_indicators):
        """Test recommendation processing when rejected by risk manager."""
        # Mock risk manager to reject trade
        decision_layer.risk_manager.evaluate_trade = AsyncMock(return_value=False)
        
        current_price = Decimal("1.2345")
        
        decision = await decision_layer.process_recommendation(
            sample_recommendation, current_price, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is not None
        assert decision.approved is False
        assert decision.recommendation == sample_recommendation
        assert "Trade rejected by risk manager" in decision.risk_management_notes
        
        # Daily trade count should not be incremented
        assert decision_layer._daily_trades == 0
    
    @pytest.mark.asyncio
    async def test_process_recommendation_daily_limit_reached(self, decision_layer, sample_recommendation, sample_market_context, sample_indicators):
        """Test recommendation processing when daily limit is reached."""
        # Set daily trades to limit
        decision_layer._daily_trades = 10
        decision_layer.config.max_trades_per_day = 10
        
        current_price = Decimal("1.2345")
        
        decision = await decision_layer.process_recommendation(
            sample_recommendation, current_price, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is not None
        assert decision.approved is False
        assert decision.recommendation == sample_recommendation
        assert "Daily trade limit reached" in decision.risk_management_notes
        
        # Daily trade count should not be incremented
        assert decision_layer._daily_trades == 10
    
    @pytest.mark.asyncio
    async def test_process_recommendation_low_confidence(self, decision_layer, sample_market_context, sample_indicators):
        """Test recommendation processing with low confidence."""
        # Create recommendation with low confidence
        low_confidence_recommendation = TradeRecommendation(
            pair="EUR_USD",
            signal=TradeSignal.BUY,
            confidence=0.3,  # Low confidence
            market_condition=MarketCondition.BREAKOUT,
            reasoning="Weak signal"
        )
        
        current_price = Decimal("1.2345")
        
        decision = await decision_layer.process_recommendation(
            low_confidence_recommendation, current_price, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is not None
        assert decision.approved is False
        assert decision.recommendation == low_confidence_recommendation
        assert "Low confidence signal" in decision.risk_management_notes
    
    @pytest.mark.asyncio
    async def test_process_recommendation_hold_signal(self, decision_layer, sample_market_context, sample_indicators):
        """Test recommendation processing with HOLD signal."""
        # Create recommendation with HOLD signal
        hold_recommendation = TradeRecommendation(
            pair="EUR_USD",
            signal=TradeSignal.HOLD,
            confidence=0.85,
            market_condition=MarketCondition.RANGING,
            reasoning="No clear signal"
        )
        
        current_price = Decimal("1.2345")
        
        decision = await decision_layer.process_recommendation(
            hold_recommendation, current_price, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is not None
        assert decision.approved is False
        assert decision.recommendation == hold_recommendation
        assert "HOLD signal - no trade" in decision.risk_management_notes
    
    @pytest.mark.asyncio
    async def test_process_recommendation_with_modified_levels(self, decision_layer, sample_recommendation, sample_market_context, sample_indicators):
        """Test recommendation processing with modified stop loss and take profit."""
        # Mock risk manager to approve trade and modify levels
        decision_layer.risk_manager.evaluate_trade = AsyncMock(return_value=True)
        decision_layer.risk_manager.calculate_position_size = AsyncMock(return_value=Decimal("1000.00"))
        decision_layer.risk_manager.calculate_risk_amount = AsyncMock(return_value=Decimal("20.00"))
        decision_layer.risk_manager.adjust_risk_levels = AsyncMock(return_value=(
            Decimal("1.2290"),  # Modified stop loss
            Decimal("1.2410")   # Modified take profit
        ))
        
        decision_layer._daily_trades = 5
        decision_layer.config.max_trades_per_day = 10
        
        current_price = Decimal("1.2345")
        
        decision = await decision_layer.process_recommendation(
            sample_recommendation, current_price, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is not None
        assert decision.approved is True
        assert decision.modified_stop_loss == Decimal("1.2290")
        assert decision.modified_take_profit == Decimal("1.2410")
        assert "Risk levels adjusted" in decision.risk_management_notes
        
        # Verify risk manager was called to adjust levels
        decision_layer.risk_manager.adjust_risk_levels.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_recommendation_exception_handling(self, decision_layer, sample_recommendation, sample_market_context, sample_indicators):
        """Test recommendation processing with exception."""
        # Mock risk manager to raise exception
        decision_layer.risk_manager.evaluate_trade = AsyncMock(side_effect=Exception("Risk evaluation error"))
        
        current_price = Decimal("1.2345")
        
        decision = await decision_layer.process_recommendation(
            sample_recommendation, current_price, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is not None
        assert decision.approved is False
        assert decision.recommendation == sample_recommendation
        assert "Error during risk evaluation" in decision.risk_management_notes
        
        # Should log the error
        decision_layer.logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_daily_performance(self, decision_layer):
        """Test get_daily_performance method."""
        # Mock performance tracker
        mock_performance = {
            "total_trades": 5,
            "winning_trades": 3,
            "losing_trades": 2,
            "win_rate": 0.6,
            "total_profit": Decimal("500.00"),
            "total_loss": Decimal("200.00"),
            "net_profit": Decimal("300.00")
        }
        decision_layer.performance_tracker.get_daily_performance = AsyncMock(return_value=mock_performance)
        
        performance = await decision_layer.get_daily_performance()
        
        assert performance == mock_performance
        decision_layer.performance_tracker.get_daily_performance.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_daily_performance_exception(self, decision_layer):
        """Test get_daily_performance with exception."""
        decision_layer.performance_tracker.get_daily_performance = AsyncMock(side_effect=Exception("Performance error"))
        
        performance = await decision_layer.get_daily_performance()
        
        assert performance == {}
        decision_layer.logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_start(self, decision_layer):
        """Test start method."""
        # Mock component start methods
        decision_layer.risk_manager.start = AsyncMock()
        decision_layer.performance_tracker.start = AsyncMock()
        decision_layer.trade_recorder.start = AsyncMock()
        
        await decision_layer.start()
        
        decision_layer.risk_manager.start.assert_called_once()
        decision_layer.performance_tracker.start.assert_called_once()
        decision_layer.trade_recorder.start.assert_called_once()
        decision_layer.logger.info.assert_called_with("Decision layer started successfully")
    
    @pytest.mark.asyncio
    async def test_start_with_exception(self, decision_layer):
        """Test start method with exception."""
        decision_layer.risk_manager.start = AsyncMock(side_effect=Exception("Start error"))
        
        with pytest.raises(Exception):
            await decision_layer.start()
    
    @pytest.mark.asyncio
    async def test_close(self, decision_layer):
        """Test close method."""
        # Mock component close methods
        decision_layer.risk_manager.close = AsyncMock()
        decision_layer.performance_tracker.close = AsyncMock()
        decision_layer.trade_recorder.stop = AsyncMock()
        
        await decision_layer.close()
        
        decision_layer.risk_manager.close.assert_called_once()
        decision_layer.performance_tracker.close.assert_called_once()
        decision_layer.trade_recorder.stop.assert_called_once()
        decision_layer.logger.info.assert_called_with("Decision layer closed")
    
    @pytest.mark.asyncio
    async def test_close_with_exception(self, decision_layer):
        """Test close method with exception."""
        decision_layer.risk_manager.close = AsyncMock(side_effect=Exception("Close error"))
        
        await decision_layer.close()
        
        decision_layer.logger.error.assert_called_with("Error closing decision layer: Close error")


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def decision_layer_edge(self):
        """Create DecisionLayer instance for edge case testing."""
        config = Mock(spec=Config)
        config.risk_percentage = 2.0
        config.max_trades_per_day = 10
        config.default_timeframe = TimeFrame.M5
        config.pairs = ["EUR_USD", "USD_JPY", "GBP_JPY"]
        config.hold_time_settings = {
            "min_hold_time_minutes": 30,
            "max_hold_time_minutes": 300,
            "default_hold_time_minutes": 120
        }
        
        with patch('decision.decision_layer.RiskManager'), \
             patch('decision.decision_layer.PerformanceTracker'), \
             patch('decision.decision_layer.EnhancedExcelTradeRecorder'):
            
            layer = DecisionLayer(config)
            layer.logger = Mock()
            layer.risk_manager = Mock()
            layer.performance_tracker = Mock()
            layer.trade_recorder = Mock()
            return layer
    
    @pytest.mark.asyncio
    async def test_process_recommendation_with_none_recommendation(self, decision_layer_edge, sample_market_context, sample_indicators):
        """Test process_recommendation with None recommendation."""
        current_price = Decimal("1.2345")
        
        decision = await decision_layer_edge.process_recommendation(
            None, current_price, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is None
    
    @pytest.mark.asyncio
    async def test_process_recommendation_with_none_current_price(self, decision_layer_edge, sample_recommendation, sample_market_context, sample_indicators):
        """Test process_recommendation with None current price."""
        decision = await decision_layer_edge.process_recommendation(
            sample_recommendation, None, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is not None
        assert decision.approved is False
        assert "No current price available" in decision.risk_management_notes
    
    @pytest.mark.asyncio
    async def test_process_recommendation_with_extreme_confidence(self, decision_layer_edge, sample_market_context, sample_indicators):
        """Test process_recommendation with extreme confidence values."""
        # Test with maximum confidence
        max_confidence_recommendation = TradeRecommendation(
            pair="EUR_USD",
            signal=TradeSignal.BUY,
            confidence=1.0,  # Maximum confidence
            market_condition=MarketCondition.BREAKOUT,
            reasoning="Maximum confidence signal"
        )
        
        decision_layer_edge.risk_manager.evaluate_trade = AsyncMock(return_value=True)
        decision_layer_edge.risk_manager.calculate_position_size = AsyncMock(return_value=Decimal("1000.00"))
        decision_layer_edge.risk_manager.calculate_risk_amount = AsyncMock(return_value=Decimal("20.00"))
        
        decision_layer_edge._daily_trades = 5
        decision_layer_edge.config.max_trades_per_day = 10
        
        current_price = Decimal("1.2345")
        
        decision = await decision_layer_edge.process_recommendation(
            max_confidence_recommendation, current_price, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is not None
        assert decision.approved is True
        
        # Test with zero confidence
        zero_confidence_recommendation = TradeRecommendation(
            pair="EUR_USD",
            signal=TradeSignal.BUY,
            confidence=0.0,  # Zero confidence
            market_condition=MarketCondition.BREAKOUT,
            reasoning="Zero confidence signal"
        )
        
        decision = await decision_layer_edge.process_recommendation(
            zero_confidence_recommendation, current_price, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is not None
        assert decision.approved is False
        assert "Low confidence signal" in decision.risk_management_notes
    
    @pytest.mark.asyncio
    async def test_process_recommendation_with_extreme_prices(self, decision_layer_edge, sample_recommendation, sample_market_context, sample_indicators):
        """Test process_recommendation with extreme price values."""
        decision_layer_edge.risk_manager.evaluate_trade = AsyncMock(return_value=True)
        decision_layer_edge.risk_manager.calculate_position_size = AsyncMock(return_value=Decimal("1000.00"))
        decision_layer_edge.risk_manager.calculate_risk_amount = AsyncMock(return_value=Decimal("20.00"))
        
        decision_layer_edge._daily_trades = 5
        decision_layer_edge.config.max_trades_per_day = 10
        
        # Test with very high price
        high_price = Decimal("999999.999999")
        decision = await decision_layer_edge.process_recommendation(
            sample_recommendation, high_price, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is not None
        assert decision.approved is True
        
        # Test with very low price
        low_price = Decimal("0.000001")
        decision = await decision_layer_edge.process_recommendation(
            sample_recommendation, low_price, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is not None
        assert decision.approved is True
    
    @pytest.mark.asyncio
    async def test_process_recommendation_with_zero_risk_percentage(self, decision_layer_edge, sample_recommendation, sample_market_context, sample_indicators):
        """Test process_recommendation with zero risk percentage."""
        decision_layer_edge.config.risk_percentage = 0.0
        
        decision_layer_edge.risk_manager.evaluate_trade = AsyncMock(return_value=True)
        decision_layer_edge.risk_manager.calculate_position_size = AsyncMock(return_value=Decimal("0.00"))
        decision_layer_edge.risk_manager.calculate_risk_amount = AsyncMock(return_value=Decimal("0.00"))
        
        decision_layer_edge._daily_trades = 5
        decision_layer_edge.config.max_trades_per_day = 10
        
        current_price = Decimal("1.2345")
        
        decision = await decision_layer_edge.process_recommendation(
            sample_recommendation, current_price, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is not None
        assert decision.approved is True
        assert decision.position_size == Decimal("0.00")
        assert decision.risk_amount == Decimal("0.00")
    
    @pytest.mark.asyncio
    async def test_process_recommendation_with_max_risk_percentage(self, decision_layer_edge, sample_recommendation, sample_market_context, sample_indicators):
        """Test process_recommendation with maximum risk percentage."""
        decision_layer_edge.config.risk_percentage = 100.0  # Maximum risk
        
        decision_layer_edge.risk_manager.evaluate_trade = AsyncMock(return_value=True)
        decision_layer_edge.risk_manager.calculate_position_size = AsyncMock(return_value=Decimal("100000.00"))
        decision_layer_edge.risk_manager.calculate_risk_amount = AsyncMock(return_value=Decimal("100000.00"))
        
        decision_layer_edge._daily_trades = 5
        decision_layer_edge.config.max_trades_per_day = 10
        
        current_price = Decimal("1.2345")
        
        decision = await decision_layer_edge.process_recommendation(
            sample_recommendation, current_price, sample_market_context,
            technical_indicators=sample_indicators
        )
        
        assert decision is not None
        assert decision.approved is True
        assert decision.position_size == Decimal("100000.00")
        assert decision.risk_amount == Decimal("100000.00")
    
    @pytest.mark.asyncio
    async def test_process_recommendation_with_none_technical_indicators(self, decision_layer_edge, sample_recommendation, sample_market_context):
        """Test process_recommendation with None technical indicators."""
        decision_layer_edge.risk_manager.evaluate_trade = AsyncMock(return_value=True)
        decision_layer_edge.risk_manager.calculate_position_size = AsyncMock(return_value=Decimal("1000.00"))
        decision_layer_edge.risk_manager.calculate_risk_amount = AsyncMock(return_value=Decimal("20.00"))
        
        decision_layer_edge._daily_trades = 5
        decision_layer_edge.config.max_trades_per_day = 10
        
        current_price = Decimal("1.2345")
        
        decision = await decision_layer_edge.process_recommendation(
            sample_recommendation, current_price, sample_market_context,
            technical_indicators=None
        )
        
        assert decision is not None
        assert decision.approved is True
        # Should still work with None technical indicators
    
    @pytest.mark.asyncio
    async def test_process_recommendation_with_empty_candles_by_timeframe(self, decision_layer_edge, sample_recommendation, sample_market_context, sample_indicators):
        """Test process_recommendation with empty candles by timeframe."""
        decision_layer_edge.risk_manager.evaluate_trade = AsyncMock(return_value=True)
        decision_layer_edge.risk_manager.calculate_position_size = AsyncMock(return_value=Decimal("1000.00"))
        decision_layer_edge.risk_manager.calculate_risk_amount = AsyncMock(return_value=Decimal("20.00"))
        
        decision_layer_edge._daily_trades = 5
        decision_layer_edge.config.max_trades_per_day = 10
        
        current_price = Decimal("1.2345")
        empty_candles_by_timeframe = {}
        
        decision = await decision_layer_edge.process_recommendation(
            sample_recommendation, current_price, sample_market_context,
            technical_indicators=sample_indicators,
            candles_by_timeframe=empty_candles_by_timeframe
        )
        
        assert decision is not None
        assert decision.approved is True
        # Should still work with empty candles by timeframe
    
    def test_reset_daily_counters_with_future_date(self, decision_layer_edge):
        """Test _reset_daily_counters with future date (edge case)."""
        # Set last reset date to future (shouldn't happen in practice)
        decision_layer_edge._last_reset_date = datetime.utcnow().date() + timedelta(days=1)
        decision_layer_edge._daily_trades = 5
        
        decision_layer_edge._reset_daily_counters()
        
        # Should not reset counters for future date
        assert decision_layer_edge._daily_trades == 5
        assert decision_layer_edge._last_reset_date == datetime.utcnow().date() + timedelta(days=1)
    
    def test_can_place_trade_with_zero_limit(self, decision_layer_edge):
        """Test _can_place_trade with zero daily limit."""
        decision_layer_edge.config.max_trades_per_day = 0
        decision_layer_edge._daily_trades = 0
        
        assert decision_layer_edge._can_place_trade() is False
    
    def test_can_place_trade_with_negative_limit(self, decision_layer_edge):
        """Test _can_place_trade with negative daily limit."""
        decision_layer_edge.config.max_trades_per_day = -5
        decision_layer_edge._daily_trades = 0
        
        assert decision_layer_edge._can_place_trade() is False
    
    def test_can_place_trade_with_negative_trades(self, decision_layer_edge):
        """Test _can_place_trade with negative daily trades count."""
        decision_layer_edge.config.max_trades_per_day = 10
        decision_layer_edge._daily_trades = -5  # Shouldn't happen in practice
        
        assert decision_layer_edge._can_place_trade() is True  # Should still allow trades 