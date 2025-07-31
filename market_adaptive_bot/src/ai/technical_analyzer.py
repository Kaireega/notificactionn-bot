"""
Technical Analyzer - Calculates technical indicators for market analysis.
"""
import numpy as np
import pandas as pd
from typing import List, Optional
from decimal import Decimal

from ..core.models import CandleData, TechnicalIndicators


class TechnicalAnalyzer:
    """Calculates technical indicators from candle data."""
    
    def __init__(self):
        pass
    
    def calculate_indicators(self, candles: List[CandleData]) -> TechnicalIndicators:
        """Calculate all technical indicators from candle data."""
        if len(candles) < 20:
            return TechnicalIndicators()
        
        # Convert to pandas DataFrame for easier calculations
        df = self._candles_to_dataframe(candles)
        
        indicators = TechnicalIndicators()
        
        # Calculate RSI
        indicators.rsi = self._calculate_rsi(df)
        
        # Calculate MACD
        macd_data = self._calculate_macd(df)
        indicators.macd = macd_data['macd']
        indicators.macd_signal = macd_data['signal']
        indicators.macd_histogram = macd_data['histogram']
        
        # Calculate EMAs
        ema_data = self._calculate_emas(df)
        indicators.ema_fast = ema_data['fast']
        indicators.ema_slow = ema_data['slow']
        
        # Calculate Bollinger Bands
        bb_data = self._calculate_bollinger_bands(df)
        indicators.bollinger_upper = bb_data['upper']
        indicators.bollinger_middle = bb_data['middle']
        indicators.bollinger_lower = bb_data['lower']
        
        # Calculate ATR
        indicators.atr = self._calculate_atr(df)
        
        # Calculate Stochastic
        stoch_data = self._calculate_stochastic(df)
        indicators.stoch_k = stoch_data['k']
        indicators.stoch_d = stoch_data['d']
        
        # Calculate Support and Resistance
        levels = self._calculate_support_resistance(df)
        indicators.support_level = levels['support']
        indicators.resistance_level = levels['resistance']
        
        return indicators
    
    def _candles_to_dataframe(self, candles: List[CandleData]) -> pd.DataFrame:
        """Convert candle data to pandas DataFrame."""
        data = []
        for candle in candles:
            data.append({
                'timestamp': candle.timestamp,
                'open': float(candle.open),
                'high': float(candle.high),
                'low': float(candle.low),
                'close': float(candle.close),
                'volume': float(candle.volume) if candle.volume else 0
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index."""
        try:
            if len(df) < period + 1:
                return None
            
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        except Exception:
            return None
    
    def _calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        try:
            if len(df) < slow + signal:
                return {'macd': None, 'signal': None, 'histogram': None}
            
            ema_fast = df['close'].ewm(span=fast).mean()
            ema_slow = df['close'].ewm(span=slow).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None,
                'signal': float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None,
                'histogram': float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None
            }
        except Exception:
            return {'macd': None, 'signal': None, 'histogram': None}
    
    def _calculate_emas(self, df: pd.DataFrame, fast: int = 12, slow: int = 26) -> dict:
        """Calculate Exponential Moving Averages."""
        try:
            if len(df) < slow:
                return {'fast': None, 'slow': None}
            
            ema_fast = df['close'].ewm(span=fast).mean()
            ema_slow = df['close'].ewm(span=slow).mean()
            
            return {
                'fast': float(ema_fast.iloc[-1]) if not pd.isna(ema_fast.iloc[-1]) else None,
                'slow': float(ema_slow.iloc[-1]) if not pd.isna(ema_slow.iloc[-1]) else None
            }
        except Exception:
            return {'fast': None, 'slow': None}
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> dict:
        """Calculate Bollinger Bands."""
        try:
            if len(df) < period:
                return {'upper': None, 'middle': None, 'lower': None}
            
            middle = df['close'].rolling(window=period).mean()
            std = df['close'].rolling(window=period).std()
            
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            return {
                'upper': float(upper.iloc[-1]) if not pd.isna(upper.iloc[-1]) else None,
                'middle': float(middle.iloc[-1]) if not pd.isna(middle.iloc[-1]) else None,
                'lower': float(lower.iloc[-1]) if not pd.isna(lower.iloc[-1]) else None
            }
        except Exception:
            return {'upper': None, 'middle': None, 'lower': None}
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate Average True Range."""
        try:
            if len(df) < period + 1:
                return None
            
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean()
            
            return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else None
        except Exception:
            return None
    
    def _calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> dict:
        """Calculate Stochastic Oscillator."""
        try:
            if len(df) < k_period + d_period:
                return {'k': None, 'd': None}
            
            lowest_low = df['low'].rolling(window=k_period).min()
            highest_high = df['high'].rolling(window=k_period).max()
            
            k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return {
                'k': float(k_percent.iloc[-1]) if not pd.isna(k_percent.iloc[-1]) else None,
                'd': float(d_percent.iloc[-1]) if not pd.isna(d_percent.iloc[-1]) else None
            }
        except Exception:
            return {'k': None, 'd': None}
    
    def _calculate_support_resistance(self, df: pd.DataFrame, period: int = 20) -> dict:
        """Calculate support and resistance levels."""
        try:
            if len(df) < period:
                return {'support': None, 'resistance': None}
            
            recent_data = df.tail(period)
            
            # Find local minima and maxima
            highs = recent_data['high'].values
            lows = recent_data['low'].values
            
            # Simple support and resistance calculation
            resistance = float(np.max(highs))
            support = float(np.min(lows))
            
            return {
                'support': support,
                'resistance': resistance
            }
        except Exception:
            return {'support': None, 'resistance': None}
    
    def detect_divergence(self, candles: List[CandleData], indicator_values: List[float]) -> dict:
        """Detect price and indicator divergence."""
        if len(candles) < 10 or len(indicator_values) < 10:
            return {'bullish': False, 'bearish': False}
        
        try:
            prices = [float(c.close) for c in candles[-10:]]
            indicators = indicator_values[-10:]
            
            # Calculate price and indicator trends
            price_trend = self._calculate_trend(prices)
            indicator_trend = self._calculate_trend(indicators)
            
            # Detect divergence
            bullish_divergence = price_trend < 0 and indicator_trend > 0
            bearish_divergence = price_trend > 0 and indicator_trend < 0
            
            return {
                'bullish': bullish_divergence,
                'bearish': bearish_divergence
            }
        except Exception:
            return {'bullish': False, 'bearish': False}
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend direction using linear regression."""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        y = np.array(values)
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        return slope
    
    def calculate_volatility(self, candles: List[CandleData], period: int = 20) -> float:
        """Calculate price volatility."""
        if len(candles) < period:
            return 0.0
        
        try:
            prices = [float(c.close) for c in candles[-period:]]
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns)
            return float(volatility)
        except Exception:
            return 0.0
    
    def calculate_momentum(self, candles: List[CandleData], period: int = 10) -> float:
        """Calculate price momentum."""
        if len(candles) < period:
            return 0.0
        
        try:
            current_price = float(candles[-1].close)
            past_price = float(candles[-period].close)
            momentum = (current_price - past_price) / past_price
            return float(momentum)
        except Exception:
            return 0.0
    
    def detect_patterns(self, candles: List[CandleData]) -> dict:
        """Detect common candlestick patterns."""
        if len(candles) < 3:
            return {}
        
        try:
            patterns = {}
            
            # Get last few candles
            recent_candles = candles[-3:]
            
            # Doji pattern
            patterns['doji'] = self._detect_doji(recent_candles[-1])
            
            # Hammer pattern
            patterns['hammer'] = self._detect_hammer(recent_candles[-1])
            
            # Engulfing pattern
            if len(recent_candles) >= 2:
                patterns['engulfing'] = self._detect_engulfing(recent_candles[-2:])
            
            # Three white soldiers / three black crows
            if len(recent_candles) >= 3:
                patterns['three_soldiers'] = self._detect_three_soldiers(recent_candles[-3:])
                patterns['three_crows'] = self._detect_three_crows(recent_candles[-3:])
            
            return patterns
        except Exception:
            return {}
    
    def _detect_doji(self, candle: CandleData) -> bool:
        """Detect doji pattern."""
        body_size = abs(float(candle.close) - float(candle.open))
        total_range = float(candle.high) - float(candle.low)
        
        if total_range == 0:
            return False
        
        doji_ratio = body_size / total_range
        return doji_ratio < 0.1  # Body is less than 10% of total range
    
    def _detect_hammer(self, candle: CandleData) -> bool:
        """Detect hammer pattern."""
        body_size = abs(float(candle.close) - float(candle.open))
        total_range = float(candle.high) - float(candle.low)
        
        if total_range == 0:
            return False
        
        # Hammer has small body and long lower shadow
        body_ratio = body_size / total_range
        lower_shadow = min(float(candle.open), float(candle.close)) - float(candle.low)
        lower_shadow_ratio = lower_shadow / total_range
        
        return body_ratio < 0.3 and lower_shadow_ratio > 0.6
    
    def _detect_engulfing(self, candles: List[CandleData]) -> str:
        """Detect engulfing pattern."""
        if len(candles) != 2:
            return "none"
        
        prev, curr = candles
        
        prev_body = abs(float(prev.close) - float(prev.open))
        curr_body = abs(float(curr.close) - float(curr.open))
        
        # Bullish engulfing
        if (float(curr.close) > float(curr.open) and  # Current is bullish
            float(prev.close) < float(prev.open) and  # Previous is bearish
            float(curr.open) < float(prev.close) and  # Current opens below previous close
            float(curr.close) > float(prev.open) and  # Current closes above previous open
            curr_body > prev_body):  # Current body engulfs previous
            return "bullish"
        
        # Bearish engulfing
        elif (float(curr.close) < float(curr.open) and  # Current is bearish
              float(prev.close) > float(prev.open) and  # Previous is bullish
              float(curr.open) > float(prev.close) and  # Current opens above previous close
              float(curr.close) < float(prev.open) and  # Current closes below previous open
              curr_body > prev_body):  # Current body engulfs previous
            return "bearish"
        
        return "none"
    
    def _detect_three_soldiers(self, candles: List[CandleData]) -> bool:
        """Detect three white soldiers pattern."""
        if len(candles) != 3:
            return False
        
        # All three candles should be bullish
        for candle in candles:
            if float(candle.close) <= float(candle.open):
                return False
        
        # Each candle should open within the previous candle's body
        for i in range(1, len(candles)):
            prev_open = float(candles[i-1].open)
            prev_close = float(candles[i-1].close)
            curr_open = float(candles[i].open)
            
            if not (prev_open <= curr_open <= prev_close):
                return False
        
        return True
    
    def _detect_three_crows(self, candles: List[CandleData]) -> bool:
        """Detect three black crows pattern."""
        if len(candles) != 3:
            return False
        
        # All three candles should be bearish
        for candle in candles:
            if float(candle.close) >= float(candle.open):
                return False
        
        # Each candle should open near the previous candle's close
        for i in range(1, len(candles)):
            prev_close = float(candles[i-1].close)
            curr_open = float(candles[i].open)
            
            # Allow small gap
            if abs(curr_open - prev_close) / prev_close > 0.01:
                return False
        
        return True 