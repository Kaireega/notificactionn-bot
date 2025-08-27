"""
AI Analysis Layer - Uses OpenAI to analyze market conditions and generate trade recommendations.
"""

import asyncio
import json
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


class AIAnalysisLayer:
    """AI-powered market analysis and trade recommendation system."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize OpenAI client (optional)
        self.openai_client = None
        if hasattr(config, 'openai_api_key') and config.openai_api_key:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=config.openai_api_key)
                self.logger.info("OpenAI client initialized successfully")
            except ImportError:
                self.logger.warning("OpenAI package not installed - AI analysis disabled")
            except Exception as e:
                self.logger.warning(f"OpenAI client initialization failed: {e}")
        else:
            self.logger.warning("OpenAI API key not provided - AI analysis disabled")
        
        # Initialize technical analyzer
        self.technical_analyzer = TechnicalAnalyzer(config)
        self.technical_analyzer.logger = self.logger
        
        # Initialize multi-timeframe analyzer
        self.multi_timeframe_analyzer = MultiTimeframeAnalyzer()
        self.multi_timeframe_analyzer.logger = self.logger
        
        # Rate limiting
        self._last_analysis_time: Dict[str, datetime] = {}
        self._analysis_cache: Dict[str, TradeRecommendation] = {}
        
        # Analysis prompts
        self._load_analysis_prompts()
    
    def _load_analysis_prompts(self) -> None:
        """Load analysis prompts for different market conditions."""
        self.prompts = {
            MarketCondition.NEWS_REACTIONARY: "Analyze news reactionary market conditions...",
            MarketCondition.REVERSAL: "Analyze reversal market conditions...",
            MarketCondition.BREAKOUT: "Analyze breakout market conditions...",
            MarketCondition.RANGING: "Analyze ranging market conditions...",
            MarketCondition.UNKNOWN: "Analyze unknown market conditions..."
        }
    
    async def analyze_market(
        self, 
        pair: str, 
        candles_by_timeframe: Dict[TimeFrame, List[CandleData]], 
        market_context: MarketContext
    ) -> Optional[TradeRecommendation]:
        """Analyze market and generate trade recommendation."""
        
        try:
            # Check rate limiting
            if not self._should_analyze(pair):
                cached_recommendation = self._analysis_cache.get(pair)
                if cached_recommendation:
                    return cached_recommendation
                return None
            
            # Use multi-timeframe analysis as fallback
            if not self.openai_client:
                self.logger.info(f"Using technical analysis for {pair} (AI disabled)")
                return await self.multi_timeframe_analyzer.analyze_multiple_timeframes(
                    pair, candles_by_timeframe, market_context
                )
            
            # AI analysis would go here
            # For now, return None to indicate no AI analysis
            self.logger.info(f"AI analysis not implemented for {pair}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error in AI market analysis: {e}")
            return None
    
    def _should_analyze(self, pair: str) -> bool:
        """Check if we should analyze this pair (rate limiting)."""
        now = datetime.now(timezone.utc)
        last_analysis = self._last_analysis_time.get(pair)
        
        if not last_analysis:
            self._last_analysis_time[pair] = now
            return True
        
        # Check if enough time has passed
        time_since_last = now - last_analysis
        min_interval = timedelta(seconds=self.config.ai_analysis.analysis_frequency)
        
        if time_since_last >= min_interval:
            self._last_analysis_time[pair] = now
            return True
        
        return False
