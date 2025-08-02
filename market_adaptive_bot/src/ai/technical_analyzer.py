"""
Enhanced Technical Analyzer - Uses existing technical indicators from technicals/indicators.py
"""
import numpy as np
import pandas as pd
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal
import sys
from pathlib import Path

# Add the root directory to the path to import technicals
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.append(str(root_dir))

# Try relative import first, then absolute import
try:
    from market_adaptive_bot.src.core.models import CandleData, TechnicalIndicators, TimeFrame
except ImportError:
    from market_adaptive_bot.src.core.models import CandleData, TechnicalIndicators, TimeFrame

from technicals.indicators import RSI, MACD, BollingerBands, ATR, KeltnerChannels
from technicals.patterns import apply_candle_props, set_candle_patterns


class TechnicalAnalyzer:
    """Enhanced technical analyzer using existing technical indicators."""
    
    def __init__(self):
        """Initialize the technical analyzer."""
        self.logger = None  # Will be set by parent class
    
    def calculate_indicators(self, candles: List[CandleData]) -> TechnicalIndicators:
        """Calculate technical indicators using existing technicals/indicators.py functions."""
        if len(candles) < 20:
            return TechnicalIndicators()
        
        try:
            # Convert candles to DataFrame format expected by technicals
            df = self._candles_to_dataframe(candles)
            
            # Apply existing technical indicators
            df = RSI(df, n=14)
            df = MACD(df, n_slow=26, n_fast=12, n_signal=9)
            df = BollingerBands(df, n=20, s=2)
            df = ATR(df, n=14)
            df = KeltnerChannels(df, n_ema=20, n_atr=10)
            
            # Apply candle properties and patterns
            df = apply_candle_props(df)
            df = set_candle_patterns(df)
            
            # Extract the latest values
            latest = df.iloc[-1]
            
            # Create TechnicalIndicators object with ALL your custom indicators
            indicators = TechnicalIndicators(
                # RSI
                rsi=float(latest.get('RSI_14', 0)) if pd.notna(latest.get('RSI_14')) else None,
                rsi_14=float(latest.get('RSI_14', 0)) if pd.notna(latest.get('RSI_14')) else None,
                
                # MACD
                macd=float(latest.get('MACD', 0)) if pd.notna(latest.get('MACD')) else None,
                macd_line=float(latest.get('MACD', 0)) if pd.notna(latest.get('MACD')) else None,
                macd_signal=float(latest.get('SIGNAL', 0)) if pd.notna(latest.get('SIGNAL')) else None,
                macd_signal_line=float(latest.get('SIGNAL', 0)) if pd.notna(latest.get('SIGNAL')) else None,
                macd_histogram=float(latest.get('HIST', 0)) if pd.notna(latest.get('HIST')) else None,
                macd_histogram_line=float(latest.get('HIST', 0)) if pd.notna(latest.get('HIST')) else None,
                
                # Bollinger Bands
                bollinger_upper=float(latest.get('BB_UP', 0)) if pd.notna(latest.get('BB_UP')) else None,
                bollinger_middle=float(latest.get('BB_MA', 0)) if pd.notna(latest.get('BB_MA')) else None,
                bb_ma=float(latest.get('BB_MA', 0)) if pd.notna(latest.get('BB_MA')) else None,
                bollinger_lower=float(latest.get('BB_LW', 0)) if pd.notna(latest.get('BB_LW')) else None,
                
                # ATR
                atr=float(latest.get('ATR_14', 0)) if pd.notna(latest.get('ATR_14')) else None,
                
                # Keltner Channels
                keltner_upper=float(latest.get('KeUp', 0)) if pd.notna(latest.get('KeUp')) else None,
                keltner_lower=float(latest.get('KeLo', 0)) if pd.notna(latest.get('KeLo')) else None,
                keltner_middle=float(latest.get('EMA', 0)) if pd.notna(latest.get('EMA')) else None,
                
                # EMA (from Keltner calculation)
                ema_fast=float(latest.get('EMA', 0)) if pd.notna(latest.get('EMA')) else None,
                ema_slow=float(latest.get('EMA', 0)) if pd.notna(latest.get('EMA')) else None,  # Using same EMA for now
                
                # Support/Resistance
                support_level=float(df['mid_l'].min()) if len(df) > 0 else None,
                resistance_level=float(df['mid_h'].max()) if len(df) > 0 else None,
                
                # Stochastic (not in your custom indicators, but keeping for compatibility)
                stoch_k=None,
                stoch_d=None
            )
            
            return indicators
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error calculating technical indicators: {e}")
            return TechnicalIndicators()
    
    def _candles_to_dataframe(self, candles: List[CandleData]) -> pd.DataFrame:
        """Convert CandleData list to DataFrame format expected by technicals."""
        data = []
        for candle in candles:
            data.append({
                'mid_o': float(candle.open),
                'mid_h': float(candle.high),
                'mid_l': float(candle.low),
                'mid_c': float(candle.close),
                'volume': float(candle.volume) if candle.volume else 0
            })
        
        df = pd.DataFrame(data)
        return df
    
    def calculate_volatility(self, candles: List[CandleData], period: int = 20) -> float:
        """Calculate volatility using existing ATR indicator."""
        if len(candles) < period:
            return 0.0
        
        try:
            df = self._candles_to_dataframe(candles)
            df = ATR(df, n=period)
            latest_atr = df.iloc[-1].get(f'ATR_{period}', 0)
            return float(latest_atr) if pd.notna(latest_atr) else 0.0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error calculating volatility: {e}")
            return 0.0
    
    def calculate_momentum(self, candles: List[CandleData], period: int = 10) -> float:
        """Calculate momentum using RSI."""
        if len(candles) < period:
            return 0.0
        
        try:
            df = self._candles_to_dataframe(candles)
            df = RSI(df, n=period)
            latest_rsi = df.iloc[-1].get(f'RSI_{period}', 50)
            return float(latest_rsi) if pd.notna(latest_rsi) else 50.0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error calculating momentum: {e}")
            return 50.0
    
    def detect_patterns(self, candles: List[CandleData]) -> dict:
        """Detect candlestick patterns using existing patterns."""
        if len(candles) < 3:
            return {}
        
        try:
            df = self._candles_to_dataframe(candles)
            df = apply_candle_props(df)
            df = set_candle_patterns(df)
            
            latest = df.iloc[-1]
            patterns = {}
            
            # Check for various patterns
            pattern_columns = [col for col in df.columns if col.startswith('pattern_')]
            for col in pattern_columns:
                if latest.get(col, False):
                    pattern_name = col.replace('pattern_', '')
                    patterns[pattern_name] = True
            
            return patterns
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error detecting patterns: {e}")
            return {}
    
    def get_trend_analysis(self, candles: List[CandleData]) -> Dict[str, Any]:
        """Get comprehensive trend analysis using existing indicators."""
        if len(candles) < 20:
            return {}
            
        try:
            df = self._candles_to_dataframe(candles)
            
            # Apply all indicators
            df = RSI(df, n=14)
            df = MACD(df, n_slow=26, n_fast=12, n_signal=9)
            df = BollingerBands(df, n=20, s=2)
            df = ATR(df, n=14)
            df = KeltnerChannels(df, n_ema=20, n_atr=10)
            df = apply_candle_props(df)
            df = set_candle_patterns(df)
            
            latest = df.iloc[-1]
            
            # Determine trend direction
            current_price = latest['mid_c']
            bb_upper = latest.get('BB_UP', current_price)
            bb_lower = latest.get('BB_LW', current_price)
            bb_middle = latest.get('BB_MA', current_price)
            
            # Trend analysis
            if current_price > bb_upper:
                trend = "strong_uptrend"
            elif current_price > bb_middle:
                trend = "uptrend"
            elif current_price < bb_lower:
                trend = "strong_downtrend"
            elif current_price < bb_middle:
                trend = "downtrend"
            else:
                trend = "sideways"
            
            return {
                'trend': trend,
                'rsi': float(latest.get('RSI_14', 50)),
                'macd': float(latest.get('MACD', 0)),
                'macd_signal': float(latest.get('SIGNAL', 0)),
                'macd_histogram': float(latest.get('HIST', 0)),
                'bollinger_upper': float(bb_upper),
                'bollinger_middle': float(bb_middle),
                'bollinger_lower': float(bb_lower),
                'atr': float(latest.get('ATR_14', 0)),
                'volatility': float(latest.get('ATR_14', 0)),
                'support': float(df['mid_l'].min()),
                'resistance': float(df['mid_h'].max())
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in trend analysis: {e}")
            return {} 