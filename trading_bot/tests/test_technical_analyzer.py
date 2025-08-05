"""
Comprehensive tests for technical analyzer with edge cases and proper mocking.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai.technical_analyzer import TechnicalAnalyzer
from core.models import (
    TimeFrame, CandleData, TechnicalIndicators, MarketCondition
)
from utils.config import Config


class TestTechnicalAnalyzer:
    """Test TechnicalAnalyzer class functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock(spec=Config)
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
    def technical_analyzer(self, mock_config):
        """Create TechnicalAnalyzer instance for testing."""
        with patch('ai.technical_analyzer.sys.path.append'):
            analyzer = TechnicalAnalyzer(mock_config)
            analyzer.logger = Mock()
            return analyzer
    
    def test_technical_analyzer_initialization(self, mock_config):
        """Test TechnicalAnalyzer initialization."""
        with patch('ai.technical_analyzer.sys.path.append') as mock_append:
            analyzer = TechnicalAnalyzer(mock_config)
            
            assert analyzer.config == mock_config
            assert analyzer.logger is not None
            mock_append.assert_called()
    
    def test_candles_to_dataframe_conversion(self, technical_analyzer, sample_candles):
        """Test _candles_to_dataframe method."""
        df = technical_analyzer._candles_to_dataframe(sample_candles)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(sample_candles)
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
        
        # Check data types
        assert df['open'].dtype == 'float64'
        assert df['high'].dtype == 'float64'
        assert df['low'].dtype == 'float64'
        assert df['close'].dtype == 'float64'
        assert df['volume'].dtype == 'float64'
        
        # Check values
        assert df['open'].iloc[0] == float(sample_candles[0].open)
        assert df['high'].iloc[0] == float(sample_candles[0].high)
        assert df['low'].iloc[0] == float(sample_candles[0].low)
        assert df['close'].iloc[0] == float(sample_candles[0].close)
        assert df['volume'].iloc[0] == float(sample_candles[0].volume)
    
    def test_candles_to_dataframe_with_empty_list(self, technical_analyzer):
        """Test _candles_to_dataframe with empty candles list."""
        df = technical_analyzer._candles_to_dataframe([])
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
    
    def test_candles_to_dataframe_with_none_volume(self, technical_analyzer):
        """Test _candles_to_dataframe with None volume."""
        candles = [CandleData(
            timestamp=datetime.utcnow(),
            open=Decimal("1.2345"),
            high=Decimal("1.2350"),
            low=Decimal("1.2340"),
            close=Decimal("1.2348"),
            volume=None,  # None volume
            pair="EUR_USD"
        )]
        
        df = technical_analyzer._candles_to_dataframe(candles)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert pd.isna(df['volume'].iloc[0])  # Should be NaN for None volume
    
    @patch('ai.technical_analyzer.RSI')
    @patch('ai.technical_analyzer.MACD')
    @patch('ai.technical_analyzer.BollingerBands')
    @patch('ai.technical_analyzer.ATR')
    @patch('ai.technical_analyzer.KeltnerChannels')
    @patch('ai.technical_analyzer.apply_candle_props')
    @patch('ai.technical_analyzer.set_candle_patterns')
    def test_calculate_indicators_success(
        self, mock_patterns, mock_props, mock_keltner, mock_atr, 
        mock_bollinger, mock_macd, mock_rsi, technical_analyzer, sample_candles
    ):
        """Test successful indicator calculation."""
        # Mock the technical indicator functions
        mock_df = pd.DataFrame({
            'open': [1.2345] * 50,
            'high': [1.2350] * 50,
            'low': [1.2340] * 50,
            'close': [1.2348] * 50,
            'volume': [1000] * 50,
            'RSI_14': [50.0] * 50,
            'MACD': [0.001] * 50,
            'SIGNAL': [0.002] * 50,
            'HIST': [-0.001] * 50,
            'BB_UP': [1.2400] * 50,
            'BB_MA': [1.2345] * 50,
            'BB_LW': [1.2290] * 50,
            'ATR_14': [0.005] * 50,
            'KeUp': [1.2390] * 50,
            'KeLo': [1.2300] * 50,
            'EMA': [1.2345] * 50,
            'mid_l': [1.2300] * 50,
            'mid_h': [1.2400] * 50
        })
        
        # Set up mocks to return the mock dataframe
        mock_rsi.return_value = mock_df
        mock_macd.return_value = mock_df
        mock_bollinger.return_value = mock_df
        mock_atr.return_value = mock_df
        mock_keltner.return_value = mock_df
        mock_props.return_value = mock_df
        mock_patterns.return_value = mock_df
        
        indicators = technical_analyzer.calculate_indicators(sample_candles)
        
        assert isinstance(indicators, TechnicalIndicators)
        assert indicators.rsi == 50.0
        assert indicators.rsi_14 == 50.0
        assert indicators.macd == 0.001
        assert indicators.macd_line == 0.001
        assert indicators.macd_signal == 0.002
        assert indicators.macd_signal_line == 0.002
        assert indicators.macd_histogram == -0.001
        assert indicators.macd_histogram_line == -0.001
        assert indicators.bollinger_upper == 1.2400
        assert indicators.bollinger_middle == 1.2345
        assert indicators.bb_ma == 1.2345
        assert indicators.bollinger_lower == 1.2290
        assert indicators.atr == 0.005
        assert indicators.keltner_upper == 1.2390
        assert indicators.keltner_lower == 1.2300
        assert indicators.keltner_middle == 1.2345
        assert indicators.ema_fast == 1.2345
        assert indicators.ema_slow == 1.2345
        assert indicators.support_level == 1.2300
        assert indicators.resistance_level == 1.2400
        
        # Verify all indicator functions were called
        mock_rsi.assert_called_once()
        mock_macd.assert_called_once()
        mock_bollinger.assert_called_once()
        mock_atr.assert_called_once()
        mock_keltner.assert_called_once()
        mock_props.assert_called_once()
        mock_patterns.assert_called_once()
    
    def test_calculate_indicators_insufficient_candles(self, technical_analyzer):
        """Test indicator calculation with insufficient candles."""
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
        
        indicators = technical_analyzer.calculate_indicators(candles)
        
        # Should return empty TechnicalIndicators
        assert isinstance(indicators, TechnicalIndicators)
        assert indicators.rsi is None
        assert indicators.macd is None
        assert indicators.bollinger_upper is None
    
    def test_calculate_indicators_empty_candles(self, technical_analyzer):
        """Test indicator calculation with empty candles list."""
        indicators = technical_analyzer.calculate_indicators([])
        
        assert isinstance(indicators, TechnicalIndicators)
        assert indicators.rsi is None
        assert indicators.macd is None
        assert indicators.bollinger_upper is None
    
    @patch('ai.technical_analyzer.RSI')
    @patch('ai.technical_analyzer.MACD')
    @patch('ai.technical_analyzer.BollingerBands')
    @patch('ai.technical_analyzer.ATR')
    @patch('ai.technical_analyzer.KeltnerChannels')
    @patch('ai.technical_analyzer.apply_candle_props')
    @patch('ai.technical_analyzer.set_candle_patterns')
    def test_calculate_indicators_with_nan_values(
        self, mock_patterns, mock_props, mock_keltner, mock_atr, 
        mock_bollinger, mock_macd, mock_rsi, technical_analyzer, sample_candles
    ):
        """Test indicator calculation with NaN values."""
        # Mock dataframe with NaN values
        mock_df = pd.DataFrame({
            'open': [1.2345] * 50,
            'high': [1.2350] * 50,
            'low': [1.2340] * 50,
            'close': [1.2348] * 50,
            'volume': [1000] * 50,
            'RSI_14': [np.nan] * 50,  # NaN RSI
            'MACD': [0.001] * 50,
            'SIGNAL': [np.nan] * 50,  # NaN signal
            'HIST': [-0.001] * 50,
            'BB_UP': [1.2400] * 50,
            'BB_MA': [1.2345] * 50,
            'BB_LW': [1.2290] * 50,
            'ATR_14': [0.005] * 50,
            'KeUp': [np.nan] * 50,  # NaN Keltner upper
            'KeLo': [1.2300] * 50,
            'EMA': [1.2345] * 50,
            'mid_l': [1.2300] * 50,
            'mid_h': [1.2400] * 50
        })
        
        # Set up mocks
        mock_rsi.return_value = mock_df
        mock_macd.return_value = mock_df
        mock_bollinger.return_value = mock_df
        mock_atr.return_value = mock_df
        mock_keltner.return_value = mock_df
        mock_props.return_value = mock_df
        mock_patterns.return_value = mock_df
        
        indicators = technical_analyzer.calculate_indicators(sample_candles)
        
        # NaN values should be converted to None
        assert indicators.rsi is None
        assert indicators.rsi_14 is None
        assert indicators.macd == 0.001  # Valid value
        assert indicators.macd_signal is None  # NaN value
        assert indicators.macd_signal_line is None  # NaN value
        assert indicators.keltner_upper is None  # NaN value
        assert indicators.keltner_lower == 1.2300  # Valid value
    
    @patch('ai.technical_analyzer.RSI')
    @patch('ai.technical_analyzer.MACD')
    @patch('ai.technical_analyzer.BollingerBands')
    @patch('ai.technical_analyzer.ATR')
    @patch('ai.technical_analyzer.KeltnerChannels')
    @patch('ai.technical_analyzer.apply_candle_props')
    @patch('ai.technical_analyzer.set_candle_patterns')
    def test_calculate_indicators_with_extreme_values(
        self, mock_patterns, mock_props, mock_keltner, mock_atr, 
        mock_bollinger, mock_macd, mock_rsi, technical_analyzer, sample_candles
    ):
        """Test indicator calculation with extreme values."""
        # Mock dataframe with extreme values
        mock_df = pd.DataFrame({
            'open': [1.2345] * 50,
            'high': [1.2350] * 50,
            'low': [1.2340] * 50,
            'close': [1.2348] * 50,
            'volume': [1000] * 50,
            'RSI_14': [100.0] * 50,  # Maximum RSI
            'MACD': [999999.0] * 50,  # Very large MACD
            'SIGNAL': [-999999.0] * 50,  # Very negative signal
            'HIST': [0.0] * 50,  # Zero histogram
            'BB_UP': [999999.0] * 50,  # Very large Bollinger upper
            'BB_MA': [1.2345] * 50,
            'BB_LW': [0.0] * 50,  # Zero Bollinger lower
            'ATR_14': [0.0] * 50,  # Zero ATR
            'KeUp': [1.2390] * 50,
            'KeLo': [1.2300] * 50,
            'EMA': [1.2345] * 50,
            'mid_l': [0.0] * 50,  # Zero support
            'mid_h': [999999.0] * 50  # Very large resistance
        })
        
        # Set up mocks
        mock_rsi.return_value = mock_df
        mock_macd.return_value = mock_df
        mock_bollinger.return_value = mock_df
        mock_atr.return_value = mock_df
        mock_keltner.return_value = mock_df
        mock_props.return_value = mock_df
        mock_patterns.return_value = mock_df
        
        indicators = technical_analyzer.calculate_indicators(sample_candles)
        
        # Should handle extreme values
        assert indicators.rsi == 100.0
        assert indicators.rsi_14 == 100.0
        assert indicators.macd == 999999.0
        assert indicators.macd_line == 999999.0
        assert indicators.macd_signal == -999999.0
        assert indicators.macd_signal_line == -999999.0
        assert indicators.macd_histogram == 0.0
        assert indicators.macd_histogram_line == 0.0
        assert indicators.bollinger_upper == 999999.0
        assert indicators.bollinger_lower == 0.0
        assert indicators.bb_ma == 1.2345
        assert indicators.atr == 0.0
        assert indicators.support_level == 0.0
        assert indicators.resistance_level == 999999.0
    
    @patch('ai.technical_analyzer.RSI')
    def test_calculate_indicators_exception_handling(self, mock_rsi, technical_analyzer, sample_candles):
        """Test indicator calculation with exception."""
        # Mock RSI to raise an exception
        mock_rsi.side_effect = Exception("RSI calculation error")
        
        indicators = technical_analyzer.calculate_indicators(sample_candles)
        
        # Should return empty TechnicalIndicators on exception
        assert isinstance(indicators, TechnicalIndicators)
        assert indicators.rsi is None
        assert indicators.macd is None
        assert indicators.bollinger_upper is None
        
        # Should log the error
        technical_analyzer.logger.error.assert_called()
    
    def test_calculate_indicators_with_missing_columns(self, technical_analyzer, sample_candles):
        """Test indicator calculation with missing DataFrame columns."""
        with patch('ai.technical_analyzer.RSI') as mock_rsi:
            # Mock dataframe with missing columns
            mock_df = pd.DataFrame({
                'open': [1.2345] * 50,
                'high': [1.2350] * 50,
                'low': [1.2340] * 50,
                'close': [1.2348] * 50,
                'volume': [1000] * 50
                # Missing technical indicator columns
            })
            
            mock_rsi.return_value = mock_df
            
            indicators = technical_analyzer.calculate_indicators(sample_candles)
            
            # Should handle missing columns gracefully
            assert isinstance(indicators, TechnicalIndicators)
            assert indicators.rsi is None  # Missing RSI_14 column
            assert indicators.macd is None  # Missing MACD column
            assert indicators.bollinger_upper is None  # Missing BB_UP column
    
    def test_calculate_indicators_with_empty_dataframe(self, technical_analyzer):
        """Test indicator calculation with empty DataFrame."""
        with patch('ai.technical_analyzer.RSI') as mock_rsi:
            # Mock empty dataframe
            mock_df = pd.DataFrame()
            
            mock_rsi.return_value = mock_df
            
            # Create minimal candles
            candles = [CandleData(
                timestamp=datetime.utcnow(),
                open=Decimal("1.2345"),
                high=Decimal("1.2350"),
                low=Decimal("1.2340"),
                close=Decimal("1.2348"),
                pair="EUR_USD"
            )] * 20  # Minimum required candles
            
            indicators = technical_analyzer.calculate_indicators(candles)
            
            # Should handle empty dataframe gracefully
            assert isinstance(indicators, TechnicalIndicators)
            assert indicators.rsi is None
            assert indicators.macd is None
            assert indicators.bollinger_upper is None
    
    @pytest.mark.asyncio
    async def test_start(self, technical_analyzer):
        """Test start method."""
        await technical_analyzer.start()
        
        technical_analyzer.logger.info.assert_called_with("Technical analyzer started successfully")
    
    @pytest.mark.asyncio
    async def test_start_with_exception(self, technical_analyzer):
        """Test start method with exception."""
        technical_analyzer.logger.info.side_effect = Exception("Start error")
        
        with pytest.raises(Exception):
            await technical_analyzer.start()
    
    @pytest.mark.asyncio
    async def test_close(self, technical_analyzer):
        """Test close method."""
        await technical_analyzer.close()
        
        technical_analyzer.logger.info.assert_called_with("Technical analyzer closed")
    
    @pytest.mark.asyncio
    async def test_close_with_exception(self, technical_analyzer):
        """Test close method with exception."""
        technical_analyzer.logger.info.side_effect = Exception("Close error")
        
        await technical_analyzer.close()
        
        technical_analyzer.logger.error.assert_called_with("Error closing technical analyzer: Close error")


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def technical_analyzer_edge(self):
        """Create TechnicalAnalyzer instance for edge case testing."""
        config = Mock(spec=Config)
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
        
        with patch('ai.technical_analyzer.sys.path.append'):
            analyzer = TechnicalAnalyzer(config)
            analyzer.logger = Mock()
            return analyzer
    
    def test_candles_to_dataframe_with_invalid_data(self, technical_analyzer_edge):
        """Test _candles_to_dataframe with invalid candle data."""
        # Create candles with invalid price relationships
        candles = [CandleData(
            timestamp=datetime.utcnow(),
            open=Decimal("1.2350"),
            high=Decimal("1.2300"),  # High is lower than low
            low=Decimal("1.2400"),   # Low is higher than high
            close=Decimal("1.2345"),
            pair="EUR_USD"
        )]
        
        df = technical_analyzer_edge._candles_to_dataframe(candles)
        
        # Should still create DataFrame even with invalid data
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df['high'].iloc[0] == 1.2300
        assert df['low'].iloc[0] == 1.2400
    
    def test_candles_to_dataframe_with_extreme_prices(self, technical_analyzer_edge):
        """Test _candles_to_dataframe with extreme price values."""
        candles = [CandleData(
            timestamp=datetime.utcnow(),
            open=Decimal("999999.999999"),
            high=Decimal("999999.999999"),
            low=Decimal("0.000001"),
            close=Decimal("999999.999999"),
            volume=Decimal("999999999"),
            pair="EUR_USD"
        )]
        
        df = technical_analyzer_edge._candles_to_dataframe(candles)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df['open'].iloc[0] == 999999.999999
        assert df['high'].iloc[0] == 999999.999999
        assert df['low'].iloc[0] == 0.000001
        assert df['close'].iloc[0] == 999999.999999
        assert df['volume'].iloc[0] == 999999999.0
    
    def test_candles_to_dataframe_with_zero_prices(self, technical_analyzer_edge):
        """Test _candles_to_dataframe with zero price values."""
        candles = [CandleData(
            timestamp=datetime.utcnow(),
            open=Decimal("0"),
            high=Decimal("0"),
            low=Decimal("0"),
            close=Decimal("0"),
            volume=Decimal("0"),
            pair="EUR_USD"
        )]
        
        df = technical_analyzer_edge._candles_to_dataframe(candles)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df['open'].iloc[0] == 0.0
        assert df['high'].iloc[0] == 0.0
        assert df['low'].iloc[0] == 0.0
        assert df['close'].iloc[0] == 0.0
        assert df['volume'].iloc[0] == 0.0
    
    @patch('ai.technical_analyzer.RSI')
    @patch('ai.technical_analyzer.MACD')
    @patch('ai.technical_analyzer.BollingerBands')
    @patch('ai.technical_analyzer.ATR')
    @patch('ai.technical_analyzer.KeltnerChannels')
    @patch('ai.technical_analyzer.apply_candle_props')
    @patch('ai.technical_analyzer.set_candle_patterns')
    def test_calculate_indicators_with_inf_values(
        self, mock_patterns, mock_props, mock_keltner, mock_atr, 
        mock_bollinger, mock_macd, mock_rsi, technical_analyzer_edge
    ):
        """Test indicator calculation with infinite values."""
        # Create candles
        candles = [CandleData(
            timestamp=datetime.utcnow() - timedelta(minutes=i),
            open=Decimal("1.2345"),
            high=Decimal("1.2350"),
            low=Decimal("1.2340"),
            close=Decimal("1.2348"),
            pair="EUR_USD"
        ) for i in range(50)]
        
        # Mock dataframe with infinite values
        mock_df = pd.DataFrame({
            'open': [1.2345] * 50,
            'high': [1.2350] * 50,
            'low': [1.2340] * 50,
            'close': [1.2348] * 50,
            'volume': [1000] * 50,
            'RSI_14': [np.inf] * 50,  # Infinite RSI
            'MACD': [-np.inf] * 50,  # Negative infinite MACD
            'SIGNAL': [0.002] * 50,
            'HIST': [-0.001] * 50,
            'BB_UP': [1.2400] * 50,
            'BB_MA': [1.2345] * 50,
            'BB_LW': [1.2290] * 50,
            'ATR_14': [0.005] * 50,
            'KeUp': [1.2390] * 50,
            'KeLo': [1.2300] * 50,
            'EMA': [1.2345] * 50,
            'mid_l': [1.2300] * 50,
            'mid_h': [1.2400] * 50
        })
        
        # Set up mocks
        mock_rsi.return_value = mock_df
        mock_macd.return_value = mock_df
        mock_bollinger.return_value = mock_df
        mock_atr.return_value = mock_df
        mock_keltner.return_value = mock_df
        mock_props.return_value = mock_df
        mock_patterns.return_value = mock_df
        
        indicators = technical_analyzer_edge.calculate_indicators(candles)
        
        # Should handle infinite values gracefully
        assert isinstance(indicators, TechnicalIndicators)
        # Infinite values should be converted to None or handled appropriately
        assert indicators.rsi is None or np.isinf(indicators.rsi)
        assert indicators.macd is None or np.isinf(indicators.macd)
    
    @patch('ai.technical_analyzer.RSI')
    @patch('ai.technical_analyzer.MACD')
    @patch('ai.technical_analyzer.BollingerBands')
    @patch('ai.technical_analyzer.ATR')
    @patch('ai.technical_analyzer.KeltnerChannels')
    @patch('ai.technical_analyzer.apply_candle_props')
    @patch('ai.technical_analyzer.set_candle_patterns')
    def test_calculate_indicators_with_string_values(
        self, mock_patterns, mock_props, mock_keltner, mock_atr, 
        mock_bollinger, mock_macd, mock_rsi, technical_analyzer_edge
    ):
        """Test indicator calculation with string values in DataFrame."""
        # Create candles
        candles = [CandleData(
            timestamp=datetime.utcnow() - timedelta(minutes=i),
            open=Decimal("1.2345"),
            high=Decimal("1.2350"),
            low=Decimal("1.2340"),
            close=Decimal("1.2348"),
            pair="EUR_USD"
        ) for i in range(50)]
        
        # Mock dataframe with string values
        mock_df = pd.DataFrame({
            'open': [1.2345] * 50,
            'high': [1.2350] * 50,
            'low': [1.2340] * 50,
            'close': [1.2348] * 50,
            'volume': [1000] * 50,
            'RSI_14': ["50.0"] * 50,  # String RSI
            'MACD': ["0.001"] * 50,  # String MACD
            'SIGNAL': [0.002] * 50,
            'HIST': [-0.001] * 50,
            'BB_UP': [1.2400] * 50,
            'BB_MA': [1.2345] * 50,
            'BB_LW': [1.2290] * 50,
            'ATR_14': [0.005] * 50,
            'KeUp': [1.2390] * 50,
            'KeLo': [1.2300] * 50,
            'EMA': [1.2345] * 50,
            'mid_l': [1.2300] * 50,
            'mid_h': [1.2400] * 50
        })
        
        # Set up mocks
        mock_rsi.return_value = mock_df
        mock_macd.return_value = mock_df
        mock_bollinger.return_value = mock_df
        mock_atr.return_value = mock_df
        mock_keltner.return_value = mock_df
        mock_props.return_value = mock_df
        mock_patterns.return_value = mock_df
        
        indicators = technical_analyzer_edge.calculate_indicators(candles)
        
        # Should handle string values gracefully
        assert isinstance(indicators, TechnicalIndicators)
        # String values should be converted to float or handled appropriately
        assert indicators.rsi == 50.0  # Should convert string to float
        assert indicators.macd == 0.001  # Should convert string to float
    
    def test_candles_to_dataframe_with_mixed_data_types(self, technical_analyzer_edge):
        """Test _candles_to_dataframe with mixed data types."""
        # Create candles with mixed data types
        candles = [
            CandleData(
                timestamp=datetime.utcnow(),
                open=Decimal("1.2345"),
                high=Decimal("1.2350"),
                low=Decimal("1.2340"),
                close=Decimal("1.2348"),
                volume=Decimal("1000"),
                pair="EUR_USD"
            ),
            CandleData(
                timestamp=datetime.utcnow() - timedelta(minutes=1),
                open=Decimal("1.2346"),
                high=Decimal("1.2351"),
                low=Decimal("1.2341"),
                close=Decimal("1.2349"),
                volume=None,  # None volume
                pair="EUR_USD"
            )
        ]
        
        df = technical_analyzer_edge._candles_to_dataframe(candles)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert df['volume'].iloc[0] == 1000.0  # Decimal converted to float
        assert pd.isna(df['volume'].iloc[1])  # None converted to NaN 