"""
Comprehensive tests for AI analysis layer with edge cases and proper mocking.
"""
import pytest
import json
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai.ai_analysis_layer import AIAnalysisLayer
from core.models import (
    MarketCondition, TradeSignal, TimeFrame, CandleData, TechnicalIndicators,
    MarketContext, TradeRecommendation
)
from utils.config import Config


class TestAIAnalysisLayer:
    """Test AIAnalysisLayer class functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock(spec=Config)
        config.openai_api_key = "test-api-key"
        config.ai_model = "gpt-4"
        config.ai_max_tokens = 1000
        config.ai_temperature = 0.3
        config.ai_analysis_frequency = 300
        config.ai_confidence_threshold = 0.7
        return config
    
    @pytest.fixture
    def sample_candles(self):
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
    def ai_layer(self, mock_config):
        """Create AIAnalysisLayer instance for testing."""
        with patch('ai.ai_analysis_layer.AsyncOpenAI'):
            layer = AIAnalysisLayer(mock_config)
            layer.logger = Mock()
            return layer
    
    def test_ai_analysis_layer_initialization(self, mock_config):
        """Test AIAnalysisLayer initialization."""
        with patch('ai.ai_analysis_layer.AsyncOpenAI') as mock_openai:
            layer = AIAnalysisLayer(mock_config)
            
            assert layer.config == mock_config
            assert layer.logger is not None
            assert layer.technical_analyzer is not None
            assert layer.multi_timeframe_analyzer is not None
            assert layer._last_analysis_time == {}
            assert layer._analysis_cache == {}
            assert hasattr(layer, 'prompts')
            mock_openai.assert_called_once_with(api_key="test-api-key")
    
    def test_ai_analysis_layer_initialization_without_api_key(self):
        """Test AIAnalysisLayer initialization without API key."""
        config = Mock(spec=Config)
        config.openai_api_key = None
        
        with patch('ai.ai_analysis_layer.AsyncOpenAI') as mock_openai:
            layer = AIAnalysisLayer(config)
            
            # Should still initialize even without API key
            assert layer.config == config
            mock_openai.assert_called_once_with(api_key=None)
    
    def test_load_analysis_prompts(self, ai_layer):
        """Test that analysis prompts are loaded correctly."""
        assert hasattr(ai_layer, 'prompts')
        assert MarketCondition.NEWS_REACTIONARY in ai_layer.prompts
        assert MarketCondition.REVERSAL in ai_layer.prompts
        assert MarketCondition.BREAKOUT in ai_layer.prompts
        assert MarketCondition.RANGING in ai_layer.prompts
        
        # Check that prompts contain expected content
        for condition, prompt in ai_layer.prompts.items():
            assert "You are an expert forex trader" in prompt
            assert "Current market data:" in prompt
            assert "Provide your analysis in JSON format:" in prompt
    
    def test_can_analyze_first_time(self, ai_layer):
        """Test _can_analyze when pair has never been analyzed."""
        assert ai_layer._can_analyze("EUR_USD") is True
    
    def test_can_analyze_rate_limited(self, ai_layer):
        """Test _can_analyze when pair is rate limited."""
        # Set last analysis time to recent
        ai_layer._last_analysis_time["EUR_USD"] = datetime.utcnow()
        ai_layer.config.ai_analysis_frequency = 300  # 5 minutes
        
        assert ai_layer._can_analyze("EUR_USD") is False
    
    def test_can_analyze_after_cooldown(self, ai_layer):
        """Test _can_analyze after cooldown period."""
        # Set last analysis time to old
        ai_layer._last_analysis_time["EUR_USD"] = datetime.utcnow() - timedelta(minutes=10)
        ai_layer.config.ai_analysis_frequency = 300  # 5 minutes
        
        assert ai_layer._can_analyze("EUR_USD") is True
    
    def test_prepare_market_data_with_all_indicators(self, ai_layer, sample_candles, sample_indicators, sample_market_context):
        """Test _prepare_market_data with all technical indicators."""
        market_data = ai_layer._prepare_market_data("EUR_USD", sample_candles, sample_market_context, sample_indicators)
        
        assert market_data["pair"] == "EUR_USD"
        assert market_data["current_price"] == float(sample_candles[-1].close)
        assert market_data["volatility"] == sample_market_context.volatility
        assert market_data["trend_strength"] == sample_market_context.trend_strength
        
        # Check technical indicators
        tech_data = market_data["technical_indicators"]
        assert tech_data["rsi"] == 50.0
        assert tech_data["rsi_14"] == 50.0
        assert tech_data["macd"] == 0.001
        assert tech_data["macd_line"] == 0.001
        assert tech_data["macd_signal"] == 0.002
        assert tech_data["macd_signal_line"] == 0.002
        assert tech_data["macd_histogram"] == -0.001
        assert tech_data["macd_histogram_line"] == -0.001
        assert tech_data["bollinger_upper"] == 1.2400
        assert tech_data["bollinger_middle"] == 1.2345
        assert tech_data["bb_ma"] == 1.2345
        assert tech_data["bollinger_lower"] == 1.2290
        assert tech_data["atr"] == 0.005
        assert tech_data["atr_14"] == 0.005
        assert tech_data["keltner_upper"] == 1.2390
        assert tech_data["keltner_lower"] == 1.2300
        assert tech_data["keltner_middle"] == 1.2345
        assert tech_data["ema_fast"] == 1.2345
        assert tech_data["ema_slow"] == 1.2340
        assert tech_data["support"] == 1.2300
        assert tech_data["resistance"] == 1.2400
        
        # Check market context
        context_data = market_data["market_context"]
        assert context_data["condition"] == "breakout"
        assert context_data["key_levels"] == {"support": 1.2300, "resistance": 1.2400}
        assert context_data["news_sentiment"] == 0.2
        
        # Check recent prices
        assert len(market_data["recent_prices"]) == 10
        assert all(isinstance(price, float) for price in market_data["recent_prices"])
    
    def test_prepare_market_data_with_empty_candles(self, ai_layer, sample_indicators, sample_market_context):
        """Test _prepare_market_data with empty candles list."""
        market_data = ai_layer._prepare_market_data("EUR_USD", [], sample_market_context, sample_indicators)
        
        assert market_data == {}
    
    def test_prepare_market_data_with_insufficient_candles(self, ai_layer, sample_indicators, sample_market_context):
        """Test _prepare_market_data with insufficient candles for momentum calculation."""
        # Create only 3 candles (less than 5 needed for momentum)
        candles = []
        for i in range(3):
            candle = CandleData(
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                open=Decimal("1.2345"),
                high=Decimal("1.2350"),
                low=Decimal("1.2340"),
                close=Decimal("1.2348"),
                pair="EUR_USD"
            )
            candles.append(candle)
        
        market_data = ai_layer._prepare_market_data("EUR_USD", candles, sample_market_context, sample_indicators)
        
        assert market_data["price_change_5_periods"] == 0.0
    
    def test_get_analysis_prompt_valid_condition(self, ai_layer):
        """Test _get_analysis_prompt with valid market condition."""
        market_data = {
            "pair": "EUR_USD",
            "current_price": 1.2345,
            "volatility": 0.015,
            "technical_indicators": {"rsi": 50.0},
            "market_context": {"condition": "breakout"}
        }
        
        prompt = ai_layer._get_analysis_prompt(MarketCondition.BREAKOUT, market_data)
        
        assert "You are an expert forex trader analyzing a BREAKOUT market condition" in prompt
        assert "EUR_USD" in prompt
        assert "1.2345" in prompt
        assert "0.015" in prompt
        assert "50.0" in prompt
    
    def test_get_analysis_prompt_invalid_condition(self, ai_layer):
        """Test _get_analysis_prompt with invalid market condition (should fallback to RANGING)."""
        market_data = {
            "pair": "EUR_USD",
            "current_price": 1.2345,
            "volatility": 0.015,
            "technical_indicators": {"rsi": 50.0},
            "market_context": {"condition": "invalid"}
        }
        
        # Create an invalid market condition
        invalid_condition = Mock()
        invalid_condition.value = "invalid_condition"
        
        prompt = ai_layer._get_analysis_prompt(invalid_condition, market_data)
        
        # Should fallback to RANGING condition
        assert "You are an expert forex trader analyzing a RANGING market condition" in prompt
    
    @pytest.mark.asyncio
    async def test_call_openai_api_success(self, ai_layer):
        """Test successful OpenAI API call."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "signal": "buy",
            "confidence": 0.85,
            "entry_price": 1.2345,
            "stop_loss": 1.2300,
            "take_profit": 1.2400,
            "reasoning": "Strong breakout signal",
            "risk_reward_ratio": 2.5,
            "estimated_hold_time_minutes": 120,
            "market_condition": "breakout"
        })
        
        ai_layer.openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        prompt = "Test prompt"
        recommendation = await ai_layer._call_openai_api(prompt, "EUR_USD")
        
        assert recommendation is not None
        assert recommendation.pair == "EUR_USD"
        assert recommendation.signal == TradeSignal.BUY
        assert recommendation.confidence == 0.85
        assert recommendation.entry_price == Decimal("1.2345")
        assert recommendation.stop_loss == Decimal("1.2300")
        assert recommendation.take_profit == Decimal("1.2400")
        assert recommendation.reasoning == "Strong breakout signal"
        assert recommendation.risk_reward_ratio == 2.5
        assert recommendation.estimated_hold_time == timedelta(minutes=120)
        assert recommendation.market_condition == MarketCondition.BREAKOUT
        
        # Verify API was called correctly
        ai_layer.openai_client.chat.completions.create.assert_called_once()
        call_args = ai_layer.openai_client.chat.completions.create.call_args
        assert call_args[1]["model"] == "gpt-4"
        assert call_args[1]["max_tokens"] == 1000
        assert call_args[1]["temperature"] == 0.3
        assert call_args[1]["response_format"] == {"type": "json_object"}
    
    @pytest.mark.asyncio
    async def test_call_openai_api_invalid_json(self, ai_layer):
        """Test OpenAI API call with invalid JSON response."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        
        ai_layer.openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        prompt = "Test prompt"
        recommendation = await ai_layer._call_openai_api(prompt, "EUR_USD")
        
        assert recommendation is None
        ai_layer.logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_call_openai_api_missing_required_fields(self, ai_layer):
        """Test OpenAI API call with missing required fields."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "signal": "buy",
            # Missing confidence and reasoning
            "entry_price": 1.2345
        })
        
        ai_layer.openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        prompt = "Test prompt"
        recommendation = await ai_layer._call_openai_api(prompt, "EUR_USD")
        
        assert recommendation is None
        ai_layer.logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_call_openai_api_invalid_signal(self, ai_layer):
        """Test OpenAI API call with invalid signal."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "signal": "invalid_signal",
            "confidence": 0.85,
            "reasoning": "Test reasoning"
        })
        
        ai_layer.openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        prompt = "Test prompt"
        recommendation = await ai_layer._call_openai_api(prompt, "EUR_USD")
        
        assert recommendation is None
        ai_layer.logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_call_openai_api_exception(self, ai_layer):
        """Test OpenAI API call with exception."""
        ai_layer.openai_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        prompt = "Test prompt"
        recommendation = await ai_layer._call_openai_api(prompt, "EUR_USD")
        
        assert recommendation is None
        ai_layer.logger.error.assert_called()
    
    def test_parse_ai_response_valid_data(self, ai_layer):
        """Test _parse_ai_response with valid data."""
        data = {
            "signal": "buy",
            "confidence": 0.85,
            "entry_price": 1.2345,
            "stop_loss": 1.2300,
            "take_profit": 1.2400,
            "reasoning": "Strong breakout signal",
            "risk_reward_ratio": 2.5,
            "estimated_hold_time_minutes": 120,
            "market_condition": "breakout"
        }
        
        recommendation = ai_layer._parse_ai_response(data, "EUR_USD")
        
        assert recommendation is not None
        assert recommendation.pair == "EUR_USD"
        assert recommendation.signal == TradeSignal.BUY
        assert recommendation.confidence == 0.85
        assert recommendation.entry_price == Decimal("1.2345")
        assert recommendation.stop_loss == Decimal("1.2300")
        assert recommendation.take_profit == Decimal("1.2400")
        assert recommendation.reasoning == "Strong breakout signal"
        assert recommendation.risk_reward_ratio == 2.5
        assert recommendation.estimated_hold_time == timedelta(minutes=120)
        assert recommendation.market_condition == MarketCondition.BREAKOUT
    
    def test_parse_ai_response_missing_required_fields(self, ai_layer):
        """Test _parse_ai_response with missing required fields."""
        data = {
            "signal": "buy",
            # Missing confidence and reasoning
            "entry_price": 1.2345
        }
        
        recommendation = ai_layer._parse_ai_response(data, "EUR_USD")
        
        assert recommendation is None
        ai_layer.logger.error.assert_called()
    
    def test_parse_ai_response_invalid_signal(self, ai_layer):
        """Test _parse_ai_response with invalid signal."""
        data = {
            "signal": "invalid_signal",
            "confidence": 0.85,
            "reasoning": "Test reasoning"
        }
        
        recommendation = ai_layer._parse_ai_response(data, "EUR_USD")
        
        assert recommendation is None
        ai_layer.logger.error.assert_called()
    
    def test_parse_ai_response_hold_time_validation(self, ai_layer):
        """Test _parse_ai_response with hold time validation."""
        # Test minimum hold time
        data = {
            "signal": "buy",
            "confidence": 0.85,
            "reasoning": "Test reasoning",
            "estimated_hold_time_minutes": 10  # Below minimum
        }
        
        recommendation = ai_layer._parse_ai_response(data, "EUR_USD")
        assert recommendation.estimated_hold_time == timedelta(minutes=30)  # Should be clamped to minimum
        
        # Test maximum hold time
        data["estimated_hold_time_minutes"] = 400  # Above maximum
        recommendation = ai_layer._parse_ai_response(data, "EUR_USD")
        assert recommendation.estimated_hold_time == timedelta(minutes=300)  # Should be clamped to maximum
        
        # Test valid hold time
        data["estimated_hold_time_minutes"] = 120  # Valid range
        recommendation = ai_layer._parse_ai_response(data, "EUR_USD")
        assert recommendation.estimated_hold_time == timedelta(minutes=120)
    
    def test_parse_ai_response_unknown_market_condition(self, ai_layer):
        """Test _parse_ai_response with unknown market condition."""
        data = {
            "signal": "buy",
            "confidence": 0.85,
            "reasoning": "Test reasoning",
            "market_condition": "unknown_condition"
        }
        
        recommendation = ai_layer._parse_ai_response(data, "EUR_USD")
        
        assert recommendation is not None
        assert recommendation.market_condition == MarketCondition.UNKNOWN
    
    @pytest.mark.asyncio
    async def test_analyze_market_success(self, ai_layer, sample_candles, sample_market_context):
        """Test successful market analysis."""
        # Mock technical analyzer
        ai_layer.technical_analyzer.calculate_indicators = Mock(return_value=sample_indicators)
        
        # Mock OpenAI API call
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "signal": "buy",
            "confidence": 0.85,
            "reasoning": "Strong breakout signal",
            "estimated_hold_time_minutes": 120
        })
        ai_layer.openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        recommendation = await ai_layer.analyze_market(
            "EUR_USD", sample_candles, sample_market_context, TimeFrame.M5
        )
        
        assert recommendation is not None
        assert recommendation.pair == "EUR_USD"
        assert recommendation.signal == TradeSignal.BUY
        assert recommendation.confidence == 0.85
        
        # Check that cache was updated
        cache_key = "EUR_USD_M5"
        assert cache_key in ai_layer._analysis_cache
        assert ai_layer._analysis_cache[cache_key] == recommendation
        assert "EUR_USD" in ai_layer._last_analysis_time
    
    @pytest.mark.asyncio
    async def test_analyze_market_rate_limited(self, ai_layer, sample_candles, sample_market_context):
        """Test market analysis when rate limited."""
        # Set up rate limiting
        ai_layer._last_analysis_time["EUR_USD"] = datetime.utcnow()
        ai_layer.config.ai_analysis_frequency = 300
        
        # Add cached recommendation
        cached_recommendation = TradeRecommendation(
            pair="EUR_USD",
            signal=TradeSignal.BUY,
            confidence=0.8,
            reasoning="Cached recommendation"
        )
        ai_layer._analysis_cache["EUR_USD_M5"] = cached_recommendation
        
        recommendation = await ai_layer.analyze_market(
            "EUR_USD", sample_candles, sample_market_context, TimeFrame.M5
        )
        
        assert recommendation == cached_recommendation
        ai_layer.logger.info.assert_called_with("Rate limited for EUR_USD, using cached analysis")
    
    @pytest.mark.asyncio
    async def test_analyze_market_below_confidence_threshold(self, ai_layer, sample_candles, sample_market_context):
        """Test market analysis with confidence below threshold."""
        ai_layer.technical_analyzer.calculate_indicators = Mock(return_value=sample_indicators)
        
        # Mock OpenAI API call with low confidence
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "signal": "buy",
            "confidence": 0.5,  # Below threshold of 0.7
            "reasoning": "Weak signal",
            "estimated_hold_time_minutes": 120
        })
        ai_layer.openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        recommendation = await ai_layer.analyze_market(
            "EUR_USD", sample_candles, sample_market_context, TimeFrame.M5
        )
        
        assert recommendation is None
        ai_layer.logger.info.assert_called_with("AI recommendation below confidence threshold for EUR_USD")
    
    @pytest.mark.asyncio
    async def test_analyze_market_exception(self, ai_layer, sample_candles, sample_market_context):
        """Test market analysis with exception."""
        ai_layer.technical_analyzer.calculate_indicators = Mock(side_effect=Exception("Technical analysis error"))
        
        recommendation = await ai_layer.analyze_market(
            "EUR_USD", sample_candles, sample_market_context, TimeFrame.M5
        )
        
        assert recommendation is None
        ai_layer.logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_analyze_multiple_timeframes_success(self, ai_layer, sample_candles, sample_market_context):
        """Test successful multi-timeframe analysis."""
        # Mock multi-timeframe analyzer
        mock_recommendation = TradeRecommendation(
            pair="EUR_USD",
            signal=TradeSignal.BUY,
            confidence=0.85,
            reasoning="Multi-timeframe consensus"
        )
        ai_layer.multi_timeframe_analyzer.analyze_all_timeframes = AsyncMock(
            return_value=mock_recommendation
        )
        
        # Mock technical analyzer
        ai_layer.technical_analyzer.calculate_indicators = Mock(return_value=sample_indicators)
        
        candles_by_timeframe = {
            TimeFrame.M5: sample_candles,
            TimeFrame.M15: sample_candles
        }
        
        recommendation, technical_indicators = await ai_layer.analyze_multiple_timeframes(
            "EUR_USD", candles_by_timeframe, sample_market_context
        )
        
        assert recommendation == mock_recommendation
        assert TimeFrame.M5 in technical_indicators
        assert TimeFrame.M15 in technical_indicators
        assert technical_indicators[TimeFrame.M5] == sample_indicators
        assert technical_indicators[TimeFrame.M15] == sample_indicators
        
        # Check that cache was updated
        cache_key = "EUR_USD_multi_timeframe"
        assert cache_key in ai_layer._analysis_cache
        assert ai_layer._analysis_cache[cache_key] == mock_recommendation
        assert "EUR_USD" in ai_layer._last_analysis_time
    
    @pytest.mark.asyncio
    async def test_analyze_multiple_timeframes_insufficient_candles(self, ai_layer, sample_market_context):
        """Test multi-timeframe analysis with insufficient candles."""
        # Create candles with insufficient data
        insufficient_candles = sample_candles[:10]  # Less than 20 candles
        
        candles_by_timeframe = {
            TimeFrame.M5: insufficient_candles,
            TimeFrame.M15: insufficient_candles
        }
        
        recommendation, technical_indicators = await ai_layer.analyze_multiple_timeframes(
            "EUR_USD", candles_by_timeframe, sample_market_context
        )
        
        assert recommendation is None
        assert technical_indicators == {}
    
    @pytest.mark.asyncio
    async def test_analyze_multiple_timeframes_exception(self, ai_layer, sample_candles, sample_market_context):
        """Test multi-timeframe analysis with exception."""
        ai_layer.multi_timeframe_analyzer.analyze_all_timeframes = AsyncMock(
            side_effect=Exception("Multi-timeframe analysis error")
        )
        
        candles_by_timeframe = {
            TimeFrame.M5: sample_candles,
            TimeFrame.M15: sample_candles
        }
        
        recommendation, technical_indicators = await ai_layer.analyze_multiple_timeframes(
            "EUR_USD", candles_by_timeframe, sample_market_context
        )
        
        assert recommendation is None
        assert technical_indicators == {}
        ai_layer.logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_market_sentiment(self, ai_layer):
        """Test get_market_sentiment method."""
        sentiment = await ai_layer.get_market_sentiment("EUR_USD")
        
        assert sentiment == 0.0  # Default neutral sentiment
    
    def test_clear_cache(self, ai_layer):
        """Test clear_cache method."""
        # Add some data to cache
        ai_layer._analysis_cache["test_key"] = "test_value"
        ai_layer._last_analysis_time["EUR_USD"] = datetime.utcnow()
        
        ai_layer.clear_cache()
        
        assert ai_layer._analysis_cache == {}
        assert ai_layer._last_analysis_time == {}
        ai_layer.logger.info.assert_called_with("AI analysis cache cleared")
    
    @pytest.mark.asyncio
    async def test_start(self, ai_layer):
        """Test start method."""
        await ai_layer.start()
        
        ai_layer.logger.info.assert_called_with("AI analysis layer started successfully")
    
    @pytest.mark.asyncio
    async def test_start_without_api_key(self, ai_layer):
        """Test start method without API key."""
        ai_layer.config.openai_api_key = None
        
        await ai_layer.start()
        
        ai_layer.logger.warning.assert_called_with("OpenAI API key not configured - AI analysis will be limited")
        ai_layer.logger.info.assert_called_with("AI analysis layer started successfully")
    
    @pytest.mark.asyncio
    async def test_start_with_exception(self, ai_layer):
        """Test start method with exception."""
        ai_layer.logger.info.side_effect = Exception("Start error")
        
        with pytest.raises(Exception):
            await ai_layer.start()
    
    @pytest.mark.asyncio
    async def test_close(self, ai_layer):
        """Test close method."""
        await ai_layer.close()
        
        ai_layer.logger.info.assert_called_with("AI analysis layer closed")
    
    @pytest.mark.asyncio
    async def test_close_with_exception(self, ai_layer):
        """Test close method with exception."""
        ai_layer.logger.info.side_effect = Exception("Close error")
        
        await ai_layer.close()
        
        ai_layer.logger.error.assert_called_with("Error closing AI analysis layer: Close error")


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def ai_layer_edge(self):
        """Create AIAnalysisLayer instance for edge case testing."""
        config = Mock(spec=Config)
        config.openai_api_key = "test-api-key"
        config.ai_model = "gpt-4"
        config.ai_max_tokens = 1000
        config.ai_temperature = 0.3
        config.ai_analysis_frequency = 300
        config.ai_confidence_threshold = 0.7
        
        with patch('ai.ai_analysis_layer.AsyncOpenAI'):
            layer = AIAnalysisLayer(config)
            layer.logger = Mock()
            return layer
    
    def test_prepare_market_data_with_none_indicators(self, ai_layer_edge):
        """Test _prepare_market_data with None indicators."""
        candles = [CandleData(
            timestamp=datetime.utcnow(),
            open=Decimal("1.2345"),
            high=Decimal("1.2350"),
            low=Decimal("1.2340"),
            close=Decimal("1.2348"),
            pair="EUR_USD"
        )]
        
        market_context = MarketContext()
        
        market_data = ai_layer_edge._prepare_market_data("EUR_USD", candles, market_context, None)
        
        # Should still work with None indicators
        assert market_data["pair"] == "EUR_USD"
        assert market_data["current_price"] == 1.2348
        assert market_data["technical_indicators"]["rsi"] is None
        assert market_data["technical_indicators"]["macd"] is None
    
    def test_prepare_market_data_with_extreme_values(self, ai_layer_edge):
        """Test _prepare_market_data with extreme values."""
        candles = [CandleData(
            timestamp=datetime.utcnow(),
            open=Decimal("999999.999999"),
            high=Decimal("999999.999999"),
            low=Decimal("0.000001"),
            close=Decimal("999999.999999"),
            pair="EUR_USD"
        )]
        
        indicators = TechnicalIndicators(
            rsi=100.0,  # Maximum RSI
            macd=999999.0,  # Very large MACD
            atr=0.0,  # Zero ATR
            support_level=0.0,  # Zero support
            resistance_level=999999.0  # Very large resistance
        )
        
        market_context = MarketContext(
            volatility=1.0,  # Maximum volatility
            trend_strength=1.0,  # Maximum trend strength
            news_sentiment=1.0  # Maximum sentiment
        )
        
        market_data = ai_layer_edge._prepare_market_data("EUR_USD", candles, market_context, indicators)
        
        assert market_data["current_price"] == 999999.999999
        assert market_data["volatility"] == 1.0
        assert market_data["trend_strength"] == 1.0
        assert market_data["news_sentiment"] == 1.0
        assert market_data["technical_indicators"]["rsi"] == 100.0
        assert market_data["technical_indicators"]["macd"] == 999999.0
        assert market_data["technical_indicators"]["atr"] == 0.0
        assert market_data["technical_indicators"]["support"] == 0.0
        assert market_data["technical_indicators"]["resistance"] == 999999.0
    
    @pytest.mark.asyncio
    async def test_analyze_market_with_empty_candles(self, ai_layer_edge):
        """Test analyze_market with empty candles list."""
        market_context = MarketContext()
        
        recommendation = await ai_layer_edge.analyze_market(
            "EUR_USD", [], market_context, TimeFrame.M5
        )
        
        assert recommendation is None
    
    @pytest.mark.asyncio
    async def test_analyze_market_with_insufficient_candles(self, ai_layer_edge):
        """Test analyze_market with insufficient candles."""
        # Create only 10 candles (less than 20 required)
        candles = []
        for i in range(10):
            candle = CandleData(
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                open=Decimal("1.2345"),
                high=Decimal("1.2350"),
                low=Decimal("1.2340"),
                close=Decimal("1.2348"),
                pair="EUR_USD"
            )
            candles.append(candle)
        
        market_context = MarketContext()
        
        recommendation = await ai_layer_edge.analyze_market(
            "EUR_USD", candles, market_context, TimeFrame.M5
        )
        
        assert recommendation is None
    
    def test_parse_ai_response_with_extreme_hold_time(self, ai_layer_edge):
        """Test _parse_ai_response with extreme hold time values."""
        data = {
            "signal": "buy",
            "confidence": 0.85,
            "reasoning": "Test reasoning",
            "estimated_hold_time_minutes": 1000  # Very large value
        }
        
        recommendation = ai_layer_edge._parse_ai_response(data, "EUR_USD")
        
        # Should be clamped to maximum of 300 minutes
        assert recommendation.estimated_hold_time == timedelta(minutes=300)
        
        # Test negative value
        data["estimated_hold_time_minutes"] = -10
        recommendation = ai_layer_edge._parse_ai_response(data, "EUR_USD")
        
        # Should be clamped to minimum of 30 minutes
        assert recommendation.estimated_hold_time == timedelta(minutes=30)
    
    def test_parse_ai_response_with_missing_prices(self, ai_layer_edge):
        """Test _parse_ai_response with missing price fields."""
        data = {
            "signal": "buy",
            "confidence": 0.85,
            "reasoning": "Test reasoning"
            # Missing entry_price, stop_loss, take_profit
        }
        
        recommendation = ai_layer_edge._parse_ai_response(data, "EUR_USD")
        
        assert recommendation is not None
        assert recommendation.entry_price is None
        assert recommendation.stop_loss is None
        assert recommendation.take_profit is None
    
    def test_parse_ai_response_with_invalid_prices(self, ai_layer_edge):
        """Test _parse_ai_response with invalid price values."""
        data = {
            "signal": "buy",
            "confidence": 0.85,
            "reasoning": "Test reasoning",
            "entry_price": "invalid_price",  # Invalid string
            "stop_loss": None,  # None value
            "take_profit": 0  # Zero value
        }
        
        recommendation = ai_layer_edge._parse_ai_response(data, "EUR_USD")
        
        assert recommendation is not None
        # Should handle invalid prices gracefully
        assert recommendation.entry_price is None
        assert recommendation.stop_loss is None
        assert recommendation.take_profit == Decimal("0") 