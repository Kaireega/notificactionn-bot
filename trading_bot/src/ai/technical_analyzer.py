"""
Technical Analyzer - Calculates technical indicators from candle data.
"""

from typing import List, Optional
from decimal import Decimal
from ..core.models import CandleData, TechnicalIndicators
from ..utils.config import Config
from ..utils.logger import get_logger


class TechnicalAnalyzer:
    """Calculates technical indicators from candle data."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
    
    def calculate_indicators(self, candles: List[CandleData]) -> TechnicalIndicators:
        """Calculate technical indicators from candle data."""
        if not candles or len(candles) < 20:
            return TechnicalIndicators()
        
        try:
            # Calculate RSI
            rsi = self._calculate_rsi(candles)
            
            # Calculate MACD
            macd, macd_signal = self._calculate_macd(candles)
            
            # Calculate Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(candles)
            
            # Calculate EMAs
            ema_fast = self._calculate_ema(candles, 12)
            ema_slow = self._calculate_ema(candles, 26)
            
            # Calculate ATR
            atr = self._calculate_atr(candles)
            
            return TechnicalIndicators(
                rsi=rsi,
                macd=macd,
                macd_signal=macd_signal,
                bollinger_upper=bb_upper,
                bollinger_middle=bb_middle,
                bollinger_lower=bb_lower,
                ema_fast=ema_fast,
                ema_slow=ema_slow,
                atr=atr
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return TechnicalIndicators()
    
    def _calculate_rsi(self, candles: List[CandleData], period: int = 14) -> Optional[float]:
        """Calculate RSI (Relative Strength Index)."""
        if len(candles) < period + 1:
            return None
        
        try:
            gains = []
            losses = []
            
            for i in range(1, len(candles)):
                change = float(candles[i].close - candles[i-1].close)
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            if len(gains) < period:
                return None
            
            # Calculate average gain and loss
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return None
    
    def _calculate_macd(self, candles: List[CandleData]) -> tuple[Optional[float], Optional[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(candles) < 26:
            return None, None
        
        try:
            # Calculate EMAs
            ema12 = self._calculate_ema(candles, 12)
            ema26 = self._calculate_ema(candles, 26)
            
            if ema12 is None or ema26 is None:
                return None, None
            
            # MACD line
            macd = float(ema12 - ema26)
            
            # Signal line (EMA of MACD)
            # For simplicity, we'll use a simple average
            macd_signal = macd * 0.8  # Simplified signal line
            
            return macd, macd_signal
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            return None, None
    
    def _calculate_bollinger_bands(self, candles: List[CandleData], period: int = 20) -> tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
        """Calculate Bollinger Bands."""
        if len(candles) < period:
            return None, None, None
        
        try:
            # Calculate SMA
            closes = [float(candle.close) for candle in candles[-period:]]
            sma = sum(closes) / len(closes)
            
            # Calculate standard deviation
            variance = sum((price - sma) ** 2 for price in closes) / len(closes)
            std_dev = variance ** 0.5
            
            # Calculate bands
            middle = Decimal(str(sma))
            upper = middle + Decimal(str(std_dev * 2))
            lower = middle - Decimal(str(std_dev * 2))
            
            return upper, middle, lower
            
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            return None, None, None
    
    def _calculate_ema(self, candles: List[CandleData], period: int) -> Optional[Decimal]:
        """Calculate EMA (Exponential Moving Average)."""
        if len(candles) < period:
            return None
        
        try:
            multiplier = 2 / (period + 1)
            closes = [float(candle.close) for candle in candles]
            
            # Start with SMA
            ema = sum(closes[:period]) / period
            
            # Calculate EMA
            for i in range(period, len(closes)):
                ema = (closes[i] * multiplier) + (ema * (1 - multiplier))
            
            return Decimal(str(ema))
            
        except Exception as e:
            self.logger.error(f"Error calculating EMA: {e}")
            return None
    
    def _calculate_atr(self, candles: List[CandleData], period: int = 14) -> Optional[Decimal]:
        """Calculate ATR (Average True Range)."""
        if len(candles) < period + 1:
            return None
        
        try:
            true_ranges = []
            
            for i in range(1, len(candles)):
                high = float(candles[i].high)
                low = float(candles[i].low)
                prev_close = float(candles[i-1].close)
                
                tr1 = high - low
                tr2 = abs(high - prev_close)
                tr3 = abs(low - prev_close)
                
                true_range = max(tr1, tr2, tr3)
                true_ranges.append(true_range)
            
            if len(true_ranges) < period:
                return None
            
            # Calculate average true range
            atr = sum(true_ranges[-period:]) / period
            
            return Decimal(str(atr))
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR: {e}")
            return None
