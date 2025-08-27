"""
Technical Analysis Layer - Calculates technical indicators and generates signals without AI.
This replaces the AI analysis layer with pure technical analysis.
"""
import asyncio
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal

from ..core.models import (
    CandleData, MarketContext, MarketCondition, TradeRecommendation, 
    TradeSignal, TechnicalIndicators, TimeFrame
)
from ..utils.config import Config
from ..utils.logger import get_logger
from .technical_analyzer import TechnicalAnalyzer
from .multi_timeframe_analyzer import MultiTimeframeAnalyzer


class TechnicalAnalysisLayer:
    """Technical analysis and signal generation without AI."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize technical analyzer
        self.technical_analyzer = TechnicalAnalyzer(config)
        self.technical_analyzer.logger = self.logger
        
        # Initialize multi-timeframe analyzer
        self.multi_timeframe_analyzer = MultiTimeframeAnalyzer()
        self.multi_timeframe_analyzer.logger = self.logger
        
        # Analysis tracking
        self._last_analysis_time: Dict[str, datetime] = {}
        self._analysis_cache: Dict[str, TradeRecommendation] = {}
        
        # Technical thresholds
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.macd_signal_threshold = 0.0001
        self.bollinger_threshold = 0.1
        self.atr_multiplier = 2.0
        self.min_signal_strength = 0.5  # Minimum signal strength for trade
        
    async def analyze_multiple_timeframes(
        self, 
        pair: str, 
        candles_by_timeframe: Dict[TimeFrame, List[CandleData]], 
        market_context: MarketContext
    ) -> Tuple[Optional[TradeRecommendation], Optional[TechnicalIndicators]]:
        """Analyze multiple timeframes and generate consensus recommendation."""
        
        try:
            # Calculate technical indicators for all timeframes
            technical_indicators = {}
            
            for timeframe, candles in candles_by_timeframe.items():
                if len(candles) < 20:  # Need minimum data for indicators
                    continue
                    
                indicators = self.technical_analyzer.calculate_indicators(candles)
                technical_indicators[timeframe] = indicators
            
            if not technical_indicators:
                self.logger.debug(f"❌ {pair}: No technical indicators calculated")
                return None, None
            
            # Get primary timeframe (M5) for main analysis
            primary_timeframe = TimeFrame.M5
            primary_indicators = technical_indicators.get(primary_timeframe)
            
            if not primary_indicators:
                # Fallback to first available timeframe
                primary_timeframe = list(technical_indicators.keys())[0]
                primary_indicators = technical_indicators[primary_timeframe]
            
            # Analyze technical signals
            signal_analysis = self._analyze_technical_signals(primary_indicators, market_context)
            
            if not signal_analysis['has_signal']:
                self.logger.debug(f"ℹ️ {pair}: No clear technical signal detected")
                return None, primary_indicators
            
            # Calculate confidence based on signal strength and multi-timeframe agreement
            confidence = self._calculate_technical_confidence(signal_analysis, technical_indicators)
            
            # Check minimum signal strength
            if confidence < self.min_signal_strength:
                self.logger.debug(f"❌ {pair}: Signal strength {confidence:.2f} below minimum {self.min_signal_strength}")
                return None, primary_indicators
            
            # Get current price from latest candle
            current_price = self._get_current_price(candles_by_timeframe[primary_timeframe])
            
            # Create trade recommendation
            recommendation = self._create_technical_recommendation(
                pair, signal_analysis, confidence, current_price, primary_indicators
            )
            
            # Log the recommendation
            self.logger.info(f"🎯 Technical Recommendation for {pair}: "
                           f"Signal={recommendation.signal.value}, "
                           f"Confidence={recommendation.confidence:.2f}, "
                           f"RR={recommendation.risk_reward_ratio:.2f}")
            
            # Update cache
            cache_key = f"{pair}_{primary_timeframe.value}"
            self._analysis_cache[cache_key] = recommendation
            self._last_analysis_time[pair] = datetime.now(timezone.utc)
            
            return recommendation, primary_indicators
            
        except Exception as e:
            self.logger.error(f"Error in technical analysis for {pair}: {e}")
            return None, None
    
    def _analyze_technical_signals(self, indicators: TechnicalIndicators, market_context: MarketContext) -> Dict[str, Any]:
        """Analyze technical indicators to generate trading signals."""
        
        signals = {
            'rsi_signal': None,
            'macd_signal': None,
            'bollinger_signal': None,
            'ema_signal': None,
            'overall_signal': None,
            'has_signal': False,
            'signal_strength': 0.0,
            'reasoning': []
        }
        
        try:
            # RSI Analysis
            if indicators.rsi is not None:
                if indicators.rsi < self.rsi_oversold:
                    signals['rsi_signal'] = TradeSignal.BUY
                    signals['reasoning'].append(f"RSI oversold ({indicators.rsi:.2f})")
                elif indicators.rsi > self.rsi_overbought:
                    signals['rsi_signal'] = TradeSignal.SELL
                    signals['reasoning'].append(f"RSI overbought ({indicators.rsi:.2f})")
            
            # MACD Analysis
            if (indicators.macd is not None and indicators.macd_signal is not None and 
                abs(indicators.macd - indicators.macd_signal) > self.macd_signal_threshold):
                
                if indicators.macd > indicators.macd_signal:
                    signals['macd_signal'] = TradeSignal.BUY
                    signals['reasoning'].append("MACD bullish crossover")
                else:
                    signals['macd_signal'] = TradeSignal.SELL
                    signals['reasoning'].append("MACD bearish crossover")
            
            # Bollinger Bands Analysis
            if (indicators.bollinger_upper is not None and indicators.bollinger_lower is not None and 
                indicators.bollinger_middle is not None):
                
                # Calculate price position relative to bands
                price = indicators.bollinger_middle  # Use middle band as reference
                upper_distance = (indicators.bollinger_upper - price) / price
                lower_distance = (price - indicators.bollinger_lower) / price
                
                if upper_distance < self.bollinger_threshold:
                    signals['bollinger_signal'] = TradeSignal.SELL
                    signals['reasoning'].append("Price near upper Bollinger band")
                elif lower_distance < self.bollinger_threshold:
                    signals['bollinger_signal'] = TradeSignal.BUY
                    signals['reasoning'].append("Price near lower Bollinger band")
            
            # EMA Analysis
            if (indicators.ema_fast is not None and indicators.ema_slow is not None):
                if indicators.ema_fast > indicators.ema_slow:
                    signals['ema_signal'] = TradeSignal.BUY
                    signals['reasoning'].append("Fast EMA above slow EMA")
                else:
                    signals['ema_signal'] = TradeSignal.SELL
                    signals['reasoning'].append("Fast EMA below slow EMA")
            
            # Volume Analysis (if available)
            if hasattr(indicators, 'volume') and indicators.volume is not None:
                # Check for volume spike (50% above average)
                if hasattr(indicators, 'volume_avg') and indicators.volume_avg is not None:
                    volume_ratio = indicators.volume / indicators.volume_avg
                    if volume_ratio > 1.5:
                        signals['volume_confirmed'] = True
                        signals['reasoning'].append(f"Volume spike detected ({volume_ratio:.1f}x average)")
                    else:
                        signals['volume_confirmed'] = False
                        signals['reasoning'].append(f"Low volume ({volume_ratio:.1f}x average)")
                else:
                    signals['volume_confirmed'] = True  # Assume confirmed if no average available
            else:
                signals['volume_confirmed'] = True  # Assume confirmed if no volume data
            
            # Trend Strength Analysis
            if (indicators.ema_fast is not None and indicators.ema_slow is not None and 
                indicators.bollinger_middle is not None):
                
                # Calculate trend strength based on EMA separation and price position
                ema_separation = abs(indicators.ema_fast - indicators.ema_slow) / indicators.ema_slow
                price_position = abs(indicators.bollinger_middle - indicators.ema_slow) / indicators.ema_slow
                
                trend_strength = (ema_separation + price_position) / 2
                
                if trend_strength > 0.01:  # 1% separation indicates strong trend
                    signals['trend_strength'] = 'strong'
                    signals['reasoning'].append("Strong trend detected")
                elif trend_strength > 0.005:  # 0.5% separation indicates moderate trend
                    signals['trend_strength'] = 'moderate'
                    signals['reasoning'].append("Moderate trend detected")
                else:
                    signals['trend_strength'] = 'weak'
                    signals['reasoning'].append("Weak trend detected")
            else:
                signals['trend_strength'] = 'unknown'
            
            # Determine overall signal
            buy_signals = sum(1 for signal in [signals['rsi_signal'], signals['macd_signal'], 
                                             signals['bollinger_signal'], signals['ema_signal']] 
                            if signal == TradeSignal.BUY)
            sell_signals = sum(1 for signal in [signals['rsi_signal'], signals['macd_signal'], 
                                              signals['bollinger_signal'], signals['ema_signal']] 
                             if signal == TradeSignal.SELL)
            
            # Enhanced signal requirements - Stricter consensus
            if buy_signals > sell_signals and buy_signals >= 2:  # Require at least 2 signals
                signals['overall_signal'] = TradeSignal.BUY
                signals['has_signal'] = True
                signals['signal_strength'] = buy_signals / 4.0
            elif sell_signals > buy_signals and sell_signals >= 2:  # Require at least 2 signals
                signals['overall_signal'] = TradeSignal.SELL
                signals['has_signal'] = True
                signals['signal_strength'] = sell_signals / 4.0
            elif buy_signals == sell_signals and buy_signals >= 2:  # Handle tie cases with higher requirement
                # In case of tie, prefer the stronger signal or use RSI as tiebreaker
                if signals['rsi_signal'] == TradeSignal.BUY:
                    signals['overall_signal'] = TradeSignal.BUY
                    signals['has_signal'] = True
                    signals['signal_strength'] = buy_signals / 4.0
                elif signals['rsi_signal'] == TradeSignal.SELL:
                    signals['overall_signal'] = TradeSignal.SELL
                    signals['has_signal'] = True
                    signals['signal_strength'] = sell_signals / 4.0
            
        except Exception as e:
            self.logger.error(f"Error analyzing technical signals: {e}")
        
        return signals
    
    def _calculate_technical_confidence(self, signal_analysis: Dict[str, Any], 
                                      technical_indicators: Dict[TimeFrame, TechnicalIndicators]) -> float:
        """Calculate confidence based on technical signal strength and consistency."""
        
        base_confidence = signal_analysis['signal_strength']
        
        # Boost confidence based on multi-timeframe agreement
        timeframe_agreement = 0.0
        total_timeframes = 0
        
        for timeframe, indicators in technical_indicators.items():
            if indicators is None:
                continue
                
            total_timeframes += 1
            timeframe_signals = self._analyze_technical_signals(indicators, None)
            
            if (timeframe_signals['overall_signal'] == signal_analysis['overall_signal'] and 
                timeframe_signals['has_signal']):
                timeframe_agreement += 1.0
        
        if total_timeframes > 0:
            timeframe_agreement /= total_timeframes
            base_confidence += timeframe_agreement * 0.3
        
        # Enhanced confidence factors
        confidence_boost = 0.0
        
        # Volume confirmation boost
        if signal_analysis.get('volume_confirmed', False):
            confidence_boost += 0.15
            self.logger.debug("Volume confirmation adds 15% confidence boost")
        
        # Trend strength boost
        trend_strength = signal_analysis.get('trend_strength', 'unknown')
        if trend_strength == 'strong':
            confidence_boost += 0.2
            self.logger.debug("Strong trend adds 20% confidence boost")
        elif trend_strength == 'moderate':
            confidence_boost += 0.1
            self.logger.debug("Moderate trend adds 10% confidence boost")
        elif trend_strength == 'weak':
            confidence_boost -= 0.1
            self.logger.debug("Weak trend reduces confidence by 10%")
        
        # Signal strength boost
        if signal_analysis['signal_strength'] >= 0.75:  # 3 out of 4 signals
            confidence_boost += 0.1
            self.logger.debug("Strong signal consensus adds 10% confidence boost")
        
        # Apply confidence boost
        final_confidence = base_confidence + confidence_boost
        
        # Cap confidence at 0.95
        return min(max(final_confidence, 0.0), 0.95)
    
    def _get_current_price(self, candles: List[CandleData]) -> Decimal:
        """Get current price from the latest candle."""
        if not candles:
            return Decimal('0')
        
        latest_candle = candles[-1]
        return (latest_candle.high + latest_candle.low) / Decimal('2')  # Use typical price
    
    def _create_technical_recommendation(
        self, 
        pair: str, 
        signal_analysis: Dict[str, Any], 
        confidence: float, 
        current_price: Decimal,
        indicators: TechnicalIndicators
    ) -> TradeRecommendation:
        """Create trade recommendation from technical analysis."""
        
        # Calculate stop loss and take profit using ATR
        atr = Decimal(str(indicators.atr)) if indicators.atr else Decimal('0.001')
        atr_distance = atr * Decimal(str(self.atr_multiplier))
        
        if signal_analysis['overall_signal'] == TradeSignal.BUY:
            stop_loss = current_price - atr_distance
            take_profit = current_price + (atr_distance * Decimal('2'))  # 1:2 risk-reward
        else:
            stop_loss = current_price + atr_distance
            take_profit = current_price - (atr_distance * Decimal('2'))  # 1:2 risk-reward
        
        # Calculate risk-reward ratio
        risk = abs(current_price - stop_loss)
        reward = abs(take_profit - current_price)
        risk_reward_ratio = float(reward / risk) if risk > 0 else 0.0
        
        reasoning = " | ".join(signal_analysis['reasoning'])
        
        return TradeRecommendation(
            pair=pair,
            signal=signal_analysis['overall_signal'],
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=risk_reward_ratio,
            reasoning=reasoning,
            market_condition=MarketCondition.BREAKOUT,  # Default to breakout
            estimated_hold_time=timedelta(minutes=120)  # 2 hours default
        )
    
    async def start(self) -> None:
        """Start the technical analysis layer."""
        try:
            print("📊 [DEBUG] Starting technical analysis layer...")
            self.logger.info("Starting technical analysis layer...")
            print("✅ [DEBUG] Technical analysis layer started successfully")
            self.logger.info("Technical analysis layer started successfully")
        except Exception as e:
            print(f"❌ [DEBUG] Error starting technical analysis layer: {e}")
            self.logger.error(f"Error starting technical analysis layer: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the technical analysis layer."""
        try:
            self.logger.info("Technical analysis layer stopped")
        except Exception as e:
            self.logger.error(f"Error stopping technical analysis layer: {e}")
