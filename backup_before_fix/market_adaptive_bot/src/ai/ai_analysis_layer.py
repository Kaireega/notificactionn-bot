"""
AI Analysis Layer - Uses OpenAI to analyze market conditions and generate trade recommendations.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import openai
from openai import AsyncOpenAI

from core.models import (
    CandleData, MarketContext, MarketCondition, TradeRecommendation, 
    TradeSignal, TechnicalIndicators, TimeFrame
)
from utils.config import Config
from utils.logger import get_logger
from .technical_analyzer import TechnicalAnalyzer
from .multi_timeframe_analyzer import MultiTimeframeAnalyzer


class AIAnalysisLayer:
    """AI-powered market analysis and trade recommendation system."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize OpenAI client
        self.openai_client = AsyncOpenAI(api_key=config.openai_api_key)
        
        # Initialize technical analyzer
        self.technical_analyzer = TechnicalAnalyzer()
        
        # Initialize multi-timeframe analyzer
        self.multi_timeframe_analyzer = MultiTimeframeAnalyzer()
        
        # Rate limiting
        self._last_analysis_time: Dict[str, datetime] = {}
        self._analysis_cache: Dict[str, TradeRecommendation] = {}
        
        # Analysis prompts
        self._load_analysis_prompts()
    
    def _load_analysis_prompts(self) -> None:
        """Load analysis prompts for different market conditions with ALL indicators."""
        self.prompts = {
            MarketCondition.NEWS_REACTIONARY: """
You are an expert forex trader analyzing a NEWS/REACTIONARY market condition. 
This market is characterized by high volatility due to news events or market reactions.

Current market data:
- Pair: {pair}
- Current price: {current_price}
- Volatility: {volatility}
- Technical indicators: {technical_indicators}
- Market context: {market_context}

Analyze this market using ALL available technical indicators:
1. RSI (14): Check for overbought/oversold conditions
2. MACD: Confirm trend direction and momentum
3. Bollinger Bands: Check price position relative to bands
4. ATR (14): Measure volatility for stop placement
5. Keltner Channels: Identify dynamic support/resistance
6. EMA: Confirm trend direction

Consider:
1. High volatility requires tighter stops and faster exits
2. News-driven moves can be unpredictable
3. Focus on momentum and volume confirmation
4. Risk management is crucial in volatile conditions

Provide your analysis in JSON format:
{{
    "signal": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "entry_price": float,
    "stop_loss": float,
    "take_profit": float,
    "reasoning": "detailed explanation using specific indicator values",
    "risk_reward_ratio": float,
    "estimated_hold_time_minutes": int (30-180 minutes for news trades),
    "market_condition": "news_reactionary"
}}
""",
            
            MarketCondition.REVERSAL: """
You are an expert forex trader analyzing a REVERSAL market condition.
This market is showing signs of a potential trend reversal.

Current market data:
- Pair: {pair}
- Current price: {current_price}
- Volatility: {volatility}
- Technical indicators: {technical_indicators}
- Market context: {market_context}

Analyze this market using ALL available technical indicators:
1. RSI (14): Look for divergences and extreme readings
2. MACD: Check for signal line crossovers and histogram changes
3. Bollinger Bands: Identify price touching bands for reversal signals
4. ATR (14): Measure volatility for wider stops
5. Keltner Channels: Check for channel breakouts
6. EMA: Confirm trend change direction

Consider:
1. Look for reversal patterns and divergences
2. Confirm with multiple timeframes
3. Wait for confirmation before entering
4. Use wider stops for reversal trades

Provide your analysis in JSON format:
{{
    "signal": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "entry_price": float,
    "stop_loss": float,
    "take_profit": float,
    "reasoning": "detailed explanation using specific indicator values",
    "risk_reward_ratio": float,
    "estimated_hold_time_minutes": int (60-300 minutes for reversal trades),
    "market_condition": "reversal"
}}
""",
            
            MarketCondition.BREAKOUT: """
You are an expert forex trader analyzing a BREAKOUT market condition.
This market is breaking through key support/resistance levels.

Current market data:
- Pair: {pair}
- Current price: {current_price}
- Volatility: {volatility}
- Technical indicators: {technical_indicators}
- Market context: {market_context}

Analyze this market using ALL available technical indicators:
1. RSI (14): Confirm momentum in breakout direction
2. MACD: Check for strong momentum confirmation
3. Bollinger Bands: Identify band expansion and price position
4. ATR (14): Measure volatility for stop placement
5. Keltner Channels: Check for channel breakouts
6. EMA: Confirm trend direction

Consider:
1. Confirm breakout with volume and momentum
2. Look for retest of broken levels
3. Use breakout levels for entry and stop placement
4. Target previous swing highs/lows

Provide your analysis in JSON format:
{{
    "signal": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "entry_price": float,
    "stop_loss": float,
    "take_profit": float,
    "reasoning": "detailed explanation using specific indicator values",
    "risk_reward_ratio": float,
    "estimated_hold_time_minutes": int (120-300 minutes for breakout trades),
    "market_condition": "breakout"
}}
""",
            
            MarketCondition.RANGING: """
You are an expert forex trader analyzing a RANGING market condition.
This market is moving sideways within a defined range.

Current market data:
- Pair: {pair}
- Current price: {current_price}
- Volatility: {volatility}
- Technical indicators: {technical_indicators}
- Market context: {market_context}

Analyze this market using ALL available technical indicators:
1. RSI (14): Use for overbought/oversold signals within range
2. MACD: Check for range-bound momentum
3. Bollinger Bands: Trade from band to band
4. ATR (14): Measure range volatility
5. Keltner Channels: Use channels for range boundaries
6. EMA: Confirm sideways movement

Consider:
1. Trade from range boundaries to the opposite side
2. Use oscillators for entry timing
3. Tight stops and targets within the range
4. Avoid trading in the middle of the range

Provide your analysis in JSON format:
{{
    "signal": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "entry_price": float,
    "stop_loss": float,
    "take_profit": float,
    "reasoning": "detailed explanation using specific indicator values",
    "risk_reward_ratio": float,
    "estimated_hold_time_minutes": int (30-180 minutes for ranging trades),
    "market_condition": "ranging"
}}
"""
        }
    
    async def analyze_market(
        self, 
        pair: str, 
        candles: List[CandleData], 
        market_context: MarketContext,
        timeframe: TimeFrame
    ) -> Optional[TradeRecommendation]:
        """Analyze market for a single timeframe."""
        
        # Check if we can analyze this pair
        if not self._can_analyze(pair):
            return None
        
        try:
            # Calculate technical indicators
            technical_indicators = self.technical_analyzer.calculate_indicators(candles)
            
            # Prepare market data for AI
            market_data = self._prepare_market_data(pair, candles, market_context, technical_indicators)
            
            # Get analysis prompt
            prompt = self._get_analysis_prompt(market_context.condition, market_data)
            
            # Call OpenAI API
            recommendation = await self._call_openai_api(prompt, pair)
            
            if recommendation:
                # Update cache
                cache_key = f"{pair}_{timeframe.value}"
                self._analysis_cache[cache_key] = recommendation
                self._last_analysis_time[pair] = datetime.utcnow()
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error analyzing market for {pair} on {timeframe}: {e}")
            return None

    def _can_analyze(self, pair: str) -> bool:
        """Check if enough time has passed since last analysis."""
        if pair not in self._last_analysis_time:
            return True
        
        time_since_last = datetime.utcnow() - self._last_analysis_time[pair]
        return time_since_last.total_seconds() >= self.config.ai_analysis_frequency
    
    def _prepare_market_data(
        self, 
        pair: str, 
        candles: List[CandleData], 
        market_context: MarketContext,
        technical_indicators: TechnicalIndicators
    ) -> Dict[str, Any]:
        """Prepare market data for AI analysis with ALL custom indicators."""
        if not candles:
            return {}
        
        latest_candle = candles[-1]
        
        # Format ALL technical indicators from your custom file
        tech_data = {
            # RSI
            "rsi": technical_indicators.rsi,
            "rsi_14": technical_indicators.rsi_14,
            
            # MACD
            "macd": technical_indicators.macd,
            "macd_line": technical_indicators.macd_line,
            "macd_signal": technical_indicators.macd_signal,
            "macd_signal_line": technical_indicators.macd_signal_line,
            "macd_histogram": technical_indicators.macd_histogram,
            "macd_histogram_line": technical_indicators.macd_histogram_line,
            
            # Bollinger Bands
            "bollinger_upper": technical_indicators.bollinger_upper,
            "bollinger_middle": technical_indicators.bollinger_middle,
            "bb_ma": technical_indicators.bb_ma,
            "bollinger_lower": technical_indicators.bollinger_lower,
            
            # ATR
            "atr": technical_indicators.atr,
            "atr_14": technical_indicators.atr,
            
            # Keltner Channels
            "keltner_upper": technical_indicators.keltner_upper,
            "keltner_lower": technical_indicators.keltner_lower,
            "keltner_middle": technical_indicators.keltner_middle,
            
            # EMA
            "ema_fast": technical_indicators.ema_fast,
            "ema_slow": technical_indicators.ema_slow,
            
            # Support/Resistance
            "support": technical_indicators.support_level,
            "resistance": technical_indicators.resistance_level
        }
        
        # Calculate price momentum
        if len(candles) >= 5:
            price_change = float(latest_candle.close - candles[-5].close)
            price_change_pct = (price_change / float(candles[-5].close)) * 100
        else:
            price_change_pct = 0.0
        
        return {
            "pair": pair,
            "current_price": float(latest_candle.close),
            "volatility": market_context.volatility,
            "trend_strength": market_context.trend_strength,
            "price_change_5_periods": price_change_pct,
            "technical_indicators": tech_data,
            "market_context": {
                "condition": market_context.condition.value,
                "key_levels": market_context.key_levels,
                "news_sentiment": market_context.news_sentiment
            },
            "recent_prices": [float(c.close) for c in candles[-10:]]
        }
    
    def _get_analysis_prompt(self, market_condition: MarketCondition, market_data: Dict[str, Any]) -> str:
        """Get the appropriate analysis prompt for the market condition."""
        if market_condition not in self.prompts:
            market_condition = MarketCondition.RANGING  # Default fallback
        
        prompt_template = self.prompts[market_condition]
        
        # Format the prompt with market data
        return prompt_template.format(
            pair=market_data.get("pair", ""),
            current_price=market_data.get("current_price", 0),
            volatility=market_data.get("volatility", 0),
            technical_indicators=json.dumps(market_data.get("technical_indicators", {}), indent=2),
            market_context=json.dumps(market_data.get("market_context", {}), indent=2)
        )
    
    async def _call_openai_api(self, prompt: str, pair: str) -> Optional[TradeRecommendation]:
        """Call OpenAI API to get trade recommendation."""
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.config.ai_model,
                messages=[
                    {"role": "system", "content": "You are an expert forex trader. Provide only valid JSON responses."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.ai_max_tokens,
                temperature=self.config.ai_temperature,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            if not content:
                return None
            
            # Parse JSON response
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON response from OpenAI for {pair}: {e}")
                return None
            
            # Validate and create recommendation
            recommendation = self._parse_ai_response(data, pair)
            return recommendation
            
        except Exception as e:
            self.logger.error(f"OpenAI API error for {pair}: {e}")
            return None
    
    def _parse_ai_response(self, data: Dict[str, Any], pair: str) -> Optional[TradeRecommendation]:
        """Parse AI response and create TradeRecommendation."""
        try:
            # Validate required fields
            required_fields = ["signal", "confidence", "reasoning"]
            for field in required_fields:
                if field not in data:
                    self.logger.error(f"Missing required field '{field}' in AI response for {pair}")
                    return None
            
            # Parse signal
            signal_str = data["signal"].lower()
            if signal_str == "buy":
                signal = TradeSignal.BUY
            elif signal_str == "sell":
                signal = TradeSignal.SELL
            elif signal_str == "hold":
                signal = TradeSignal.HOLD
            else:
                self.logger.error(f"Invalid signal '{signal_str}' in AI response for {pair}")
                return None
            
            # Parse market condition
            condition_str = data.get("market_condition", "unknown")
            try:
                market_condition = MarketCondition(condition_str)
            except ValueError:
                market_condition = MarketCondition.UNKNOWN
            
            # Parse hold time with validation
            hold_time_minutes = int(data.get("estimated_hold_time_minutes", 30))
            
            # Validate hold time range (30 minutes to 5 hours)
            hold_time_minutes = max(30, min(300, hold_time_minutes))
            
            # Create recommendation
            recommendation = TradeRecommendation(
                pair=pair,
                signal=signal,
                entry_price=Decimal(str(data.get("entry_price", 0))) if data.get("entry_price") else None,
                stop_loss=Decimal(str(data.get("stop_loss", 0))) if data.get("stop_loss") else None,
                take_profit=Decimal(str(data.get("take_profit", 0))) if data.get("take_profit") else None,
                confidence=float(data["confidence"]),
                market_condition=market_condition,
                reasoning=data["reasoning"],
                risk_reward_ratio=float(data.get("risk_reward_ratio", 0)),
                estimated_hold_time=timedelta(minutes=hold_time_minutes)
            )
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error parsing AI response for {pair}: {e}")
            return None
    
    async def get_market_sentiment(self, pair: str) -> float:
        """Get market sentiment score for a pair."""
        try:
            # This would integrate with news sentiment analysis
            # For now, return a neutral sentiment
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting market sentiment for {pair}: {e}")
            return 0.0
    
    async def analyze_multiple_timeframes(
        self, 
        pair: str, 
        candles_by_timeframe: Dict[TimeFrame, List[CandleData]],
        market_context: MarketContext
    ) -> tuple[Optional[TradeRecommendation], Dict[TimeFrame, TechnicalIndicators]]:
        """Analyze multiple timeframes and generate consensus recommendation."""
        try:
            # Use the new multi-timeframe analyzer
            technical_indicators = {}
            
            # Calculate technical indicators for each timeframe
            for timeframe, candles in candles_by_timeframe.items():
                if candles and len(candles) >= 20:
                    technical_indicators[timeframe] = self.technical_analyzer.calculate_indicators(candles)
            
            # Perform comprehensive multi-timeframe analysis
            recommendation = await self.multi_timeframe_analyzer.analyze_all_timeframes(
                pair, candles_by_timeframe, market_context, technical_indicators
            )
            
            if recommendation:
                # Update cache
                cache_key = f"{pair}_multi_timeframe"
                self._analysis_cache[cache_key] = recommendation
                self._last_analysis_time[pair] = datetime.utcnow()
                
                self.logger.info(f"Multi-timeframe analysis completed for {pair}: {recommendation.signal.value} "
                               f"with confidence {recommendation.confidence:.2f}")
            
            return recommendation, technical_indicators
            
        except Exception as e:
            self.logger.error(f"Error in multi-timeframe analysis for {pair}: {e}")
            return None, {}
    
    def _generate_consensus_recommendation(
        self, 
        recommendations: List[TradeRecommendation], 
        pair: str
    ) -> TradeRecommendation:
        """Generate consensus recommendation from multiple timeframes."""
        if not recommendations:
            return None
        
        # Count signals
        signal_counts = {}
        total_confidence = 0.0
        
        for rec in recommendations:
            signal = rec.signal.value
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
            total_confidence += rec.confidence
        
        # Find most common signal
        consensus_signal = max(signal_counts.items(), key=lambda x: x[1])[0]
        
        # Calculate average confidence
        avg_confidence = total_confidence / len(recommendations)
        
        # Use the recommendation with highest confidence as base
        best_recommendation = max(recommendations, key=lambda x: x.confidence)
        
        # Create consensus recommendation
        consensus = TradeRecommendation(
            pair=pair,
            signal=TradeSignal(consensus_signal),
            entry_price=best_recommendation.entry_price,
            stop_loss=best_recommendation.stop_loss,
            take_profit=best_recommendation.take_profit,
            confidence=avg_confidence,
            market_condition=best_recommendation.market_condition,
            reasoning=f"Consensus from {len(recommendations)} timeframes: {best_recommendation.reasoning}",
            risk_reward_ratio=best_recommendation.risk_reward_ratio,
            estimated_hold_time=best_recommendation.estimated_hold_time
        )
        
        return consensus
    
    def clear_cache(self) -> None:
        """Clear analysis cache."""
        self._analysis_cache.clear()
        self._last_analysis_time.clear()
        self.logger.info("AI analysis cache cleared")
    
    async def start(self) -> None:
        """Start the AI analysis layer."""
        try:
            self.logger.info("Starting AI analysis layer...")
            # Initialize OpenAI client
            if not self.config.openai_api_key:
                self.logger.warning("OpenAI API key not configured - AI analysis will be limited")
            else:
                self.logger.info("OpenAI client initialized successfully")
            
            self.logger.info("AI analysis layer started successfully")
        except Exception as e:
            self.logger.error(f"Error starting AI analysis layer: {e}")
            raise
    
    async def close(self) -> None:
        """Close AI analysis layer."""
        try:
            # Clear cache
            self.clear_cache()
            self.logger.info("AI analysis layer closed")
        except Exception as e:
            self.logger.error(f"Error closing AI analysis layer: {e}") 