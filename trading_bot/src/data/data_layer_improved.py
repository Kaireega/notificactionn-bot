"""
Improved Data Layer - Market data collection and management with enhanced features.
"""
import asyncio
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal
import random
import sys
from pathlib import Path

# Add the root directory to the path to import API modules
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.append(str(root_dir))

from ..core.models import CandleData, TimeFrame, MarketContext, MarketCondition
from ..utils.config import Config
from ..utils.logger import get_logger

# Import OANDA API
try:
    # Add the project root to the path to import API modules
    root_dir = Path(__file__).parent.parent.parent.parent
    sys.path.append(str(root_dir))
    
    from api.oanda_api import OandaApi
    from constants import defs
    OANDA_AVAILABLE = True
except ImportError as e:
    OANDA_AVAILABLE = False
    print(f"⚠️ OANDA API not available: {e}")
    print("⚠️ Using mock data")


class ImprovedDataLayer:
    """Enhanced market data collection and storage with improved features."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Data storage with increased capacity
        self._candles: Dict[str, Dict[TimeFrame, List[CandleData]]] = {}
        self._market_contexts: Dict[str, MarketContext] = {}
        
        # OANDA API integration - REAL DATA ONLY
        if OANDA_AVAILABLE:
            self.oanda_api = OandaApi()
            # Force real data usage - no mock data
            self.use_real_data = True
            self.logger.info("Using real OANDA API data only")
        else:
            self.oanda_api = None
            self.use_real_data = False
            self.logger.error("OANDA API not available - cannot run without real data")
            raise Exception("OANDA API required for improved data layer")
        
        # Enhanced data tracking
        self._data_quality_metrics = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'last_update_time': None,
            'data_freshness': {}
        }
        
        self._is_running = False
        self._update_task = None
    
    async def _validate_oanda_credentials(self) -> bool:
        """Validate OANDA API credentials."""
        try:
            if self.use_real_data and self.oanda_api:
                return self.oanda_api.validate_credentials()
            return False  # Must have real data
        except Exception as e:
            self.logger.error(f"Error validating OANDA credentials: {e}")
            return False

    async def start(self):
        """Start the improved data layer."""
        try:
            # Validate OANDA credentials
            if not await self._validate_oanda_credentials():
                raise Exception("Invalid OANDA credentials - real data required")
            
            # Initialize data for all trading pairs with increased storage
            for pair in self.config.trading_pairs:
                await self._initialize_pair_data(pair)
            
            # Start data update loop
            self._is_running = True
            asyncio.create_task(self._data_update_loop())
            
            self.logger.info("Improved data layer started successfully")
            
        except Exception as e:
            print(f"❌ [DEBUG] Error starting improved data layer: {e}")
            self.logger.error(f"Error starting improved data layer: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the improved data layer."""
        self.logger.info("Stopping improved data layer...")
        self._is_running = False
        
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Improved data layer stopped")
    
    async def get_candles(
        self, 
        pair: str, 
        timeframe: TimeFrame, 
        count: int = 2000  # Increased default
    ) -> List[CandleData]:
        """Get candle data for a pair and timeframe with increased capacity."""
        
        if self.use_real_data and self.oanda_api:
            return await self._get_real_candles(pair, timeframe, count)
        else:
            # Fallback to cached data
            if pair not in self._candles or timeframe not in self._candles[pair]:
                return []
            
            candles = self._candles[pair][timeframe]
            return candles[-count:] if len(candles) >= count else candles
    
    async def get_market_context(self, pair: str) -> MarketContext:
        """Get market context for a pair."""
        return self._market_contexts.get(pair, MarketContext())
    
    async def get_current_price(self, pair: str) -> Optional[Decimal]:
        """Get current price for a pair."""
        # First try to get from cached candle data (most efficient)
        if pair in self._candles and TimeFrame.M5 in self._candles[pair]:
            candles = self._candles[pair][TimeFrame.M5]
            if candles:
                return candles[-1].close
        
        # If no cached data, try real API call
        if self.use_real_data and self.oanda_api:
            return await self._get_real_current_price(pair)
        
        return None
    
    async def _initialize_pair_data(self, pair: str) -> None:
        """Initialize data for a trading pair with increased storage."""
        print(f"📊 [DEBUG] Initializing improved data for {pair}")
        self.logger.info(f"Initializing improved data for {pair}")
        
        # Initialize candle storage
        if pair not in self._candles:
            self._candles[pair] = {}
            print(f"📊 [DEBUG] {pair}: Created enhanced candle storage")
        
        # Get historical data for each timeframe with increased capacity
        print(f"📊 [DEBUG] {pair}: Getting data for {len(self.config.timeframes)} timeframes: {[tf.value for tf in self.config.timeframes]}")
        for timeframe in self.config.timeframes:
            print(f"📊 [DEBUG] {pair}: Getting {timeframe.value} data...")
            if self.use_real_data and self.oanda_api:
                # Get real data from API with increased capacity
                print(f"📊 [DEBUG] {pair}: Using real OANDA API data")
                candles = await self._get_real_candles(pair, timeframe, 2000)  # Increased to 2000
            else:
                # No mock data - raise error
                raise Exception(f"Cannot initialize {pair} - real data required")
            
            self._candles[pair][timeframe] = candles
            print(f"📊 [DEBUG] {pair}: {timeframe.value} - {len(candles)} candles loaded")
        
        # Initialize market context
        print(f"🌍 [DEBUG] {pair}: Initializing market context...")
        self._market_contexts[pair] = MarketContext(
            condition=MarketCondition.RANGING,
            volatility=0.001,
            trend_strength=0.5,
            news_sentiment=0.0,
            timestamp=datetime.now(timezone.utc)
        )
        print(f"✅ [DEBUG] {pair}: Market context initialized")
    
    async def _data_update_loop(self) -> None:
        """Enhanced data update loop with better error handling."""
        print("🔄 [DEBUG] Improved data update loop started")
        update_count = 0
        while self._is_running:
            try:
                update_count += 1
                print(f"🔄 [DEBUG] Data update iteration {update_count}")
                
                # Update data quality metrics
                self._data_quality_metrics['total_updates'] += 1
                self._data_quality_metrics['last_update_time'] = datetime.now(timezone.utc)
                
                await self._update_all_data()
                
                # Mark successful update
                self._data_quality_metrics['successful_updates'] += 1
                
                print(f"⏰ [DEBUG] Waiting {self.config.data_update_frequency} seconds for next update...")
                await asyncio.sleep(self.config.data_update_frequency)
                
            except Exception as e:
                # Mark failed update
                self._data_quality_metrics['failed_updates'] += 1
                
                print(f"❌ [DEBUG] Error in improved data update loop: {e}")
                print(f"❌ [DEBUG] Traceback: {traceback.format_exc()}")
                self.logger.error(f"Error in improved data update loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _update_all_data(self) -> None:
        """Update data for all pairs with enhanced tracking."""
        print(f"📊 [DEBUG] Updating improved data for {len(self.config.trading_pairs)} pairs")
        for pair in self.config.trading_pairs:
            print(f"📊 [DEBUG] Updating improved data for {pair}...")
            await self._update_pair_data(pair)
            print(f"✅ [DEBUG] Improved data updated for {pair}")
    
    async def _update_pair_data(self, pair: str) -> None:
        """Update data for a specific pair with NO MOCK DATA and increased storage."""
        try:
            print(f"📊 [DEBUG] {pair}: Starting improved data update...")
            
            # Update candles for each timeframe
            for timeframe in self.config.timeframes:
                print(f"📊 [DEBUG] {pair}: Updating {timeframe.value} data...")
                if self.use_real_data and self.oanda_api:
                    # Get fresh real data from API with increased capacity
                    print(f"📊 [DEBUG] {pair}: Getting fresh real data for {timeframe.value}")
                    new_candles = await self._get_real_candles(pair, timeframe, 100)
                    if new_candles:
                        # Replace with fresh data, keeping only the latest candles with increased capacity
                        self._candles[pair][timeframe] = new_candles[-2000:]  # Keep last 2000
                        print(f"📊 [DEBUG] {pair}: {timeframe.value} - Updated with {len(new_candles)} candles")
                        
                        # Update data freshness
                        self._data_quality_metrics['data_freshness'][f"{pair}_{timeframe.value}"] = datetime.now(timezone.utc)
                    else:
                        print(f"⚠️ [DEBUG] {pair}: {timeframe.value} - No new candles received")
                else:
                    # NO MOCK DATA - only use real data
                    print(f"❌ [DEBUG] {pair}: {timeframe.value} - No real data available, skipping update")
                    continue
            
            # Update market context
            print(f"🌍 [DEBUG] {pair}: Updating market context...")
            await self._update_market_context(pair)
            print(f"✅ [DEBUG] {pair}: Market context updated")
                
        except Exception as e:
            print(f"❌ [DEBUG] {pair}: Error updating improved data: {e}")
            print(f"❌ [DEBUG] {pair}: Traceback: {traceback.format_exc()}")
            self.logger.error(f"Error updating improved data for {pair}: {e}")
    
    async def _update_market_context(self, pair: str) -> None:
        """Update market context for a pair with enhanced analysis."""
        try:
            # Get recent candles for analysis
            recent_candles = await self.get_candles(pair, TimeFrame.M5, 20)
            if not recent_candles:
                self.logger.warning(f"No recent candles available for {pair} market context update")
                return
            
            # Calculate enhanced volatility
            prices = [float(c.close) for c in recent_candles]
            volatility = self._calculate_enhanced_volatility(prices)
        
            # Determine market condition with improved logic
            condition = self._determine_enhanced_market_condition(recent_candles, volatility)
        
            # Calculate trend strength with improved algorithm
            trend_strength = self._calculate_enhanced_trend_strength(recent_candles)
        
            # Update market context
            self._market_contexts[pair] = MarketContext(
                condition=condition,
                volatility=volatility,
                trend_strength=trend_strength,
                news_sentiment=0.0,  # Will be updated by fundamental analyzer
                timestamp=datetime.now(timezone.utc)
            )
            
            # Log enhanced market context update
            self.logger.debug(f"📊 Enhanced market context updated for {pair}: "
                            f"Condition={condition.value}, "
                            f"Volatility={volatility:.3f}%, "
                            f"Trend Strength={trend_strength:.3f}")
            
        except Exception as e:
            self.logger.error(f"Error updating enhanced market context for {pair}: {e}")
    
    def _calculate_enhanced_volatility(self, prices: List[float]) -> float:
        """Calculate enhanced price volatility with better algorithm."""
        if len(prices) < 2:
            return 0.0
        
        # Calculate percentage returns
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        # Calculate standard deviation of returns (more accurate than average absolute)
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        # Convert to percentage (multiply by 100 for display)
        volatility_percentage = std_dev * 100
        
        # Debug logging
        if len(prices) > 0:
            self.logger.debug(f"Enhanced volatility calculation: {len(prices)} prices, "
                            f"range: {min(prices):.5f}-{max(prices):.5f}, "
                            f"volatility: {volatility_percentage:.6f}%")
        
        return volatility_percentage
    
    def _determine_enhanced_market_condition(self, candles: List[CandleData], volatility: float) -> MarketCondition:
        """Determine enhanced market condition based on improved analysis."""
        # Enhanced volatility thresholds
        if volatility > 0.3:  # > 0.3%
            return MarketCondition.NEWS_REACTIONARY
        elif volatility > 0.2:  # > 0.2%
            return MarketCondition.BREAKOUT
        elif volatility > 0.15:  # > 0.15%
            return MarketCondition.REVERSAL
        else:
            return MarketCondition.RANGING
    
    def _calculate_enhanced_trend_strength(self, candles: List[CandleData]) -> float:
        """Calculate enhanced trend strength with improved algorithm."""
        if len(candles) < 10:
            return 0.5
        
        # Calculate trend using linear regression slope
        prices = [float(c.close) for c in candles]
        n = len(prices)
        
        if n < 2:
            return 0.0
        
        # Calculate linear regression slope
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(prices) / n
        
        numerator = sum((x[i] - x_mean) * (prices[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        # Enhanced normalization using price range and volatility
        price_range = max(prices) - min(prices)
        if price_range == 0:
            return 0.0
        
        # Calculate trend strength based on slope relative to price range and volatility
        trend_strength = min(abs(slope * n / price_range), 1.0)
        
        # Apply volatility adjustment
        avg_price = sum(prices) / len(prices)
        volatility_adjustment = min(1.0, avg_price * 0.001)  # Normalize by average price
        trend_strength *= volatility_adjustment
        
        return trend_strength
    
    async def get_all_data(self) -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
        """Get candles data for all pairs and timeframes with increased capacity."""
        result = {}
        
        for pair in self.config.trading_pairs:
            try:
                # Get candles for all timeframes
                candles = {}
                for timeframe in self.config.timeframes:
                    timeframe_candles = await self.get_candles(pair, timeframe, 2000)  # Increased capacity
                    candles[timeframe] = timeframe_candles
                
                result[pair] = candles
                
            except Exception as e:
                self.logger.error(f"Error getting improved data for {pair}: {e}")
                result[pair] = {}
        
        return result

    async def get_data_quality_metrics(self) -> Dict[str, Any]:
        """Get data quality metrics."""
        return {
            'total_updates': self._data_quality_metrics['total_updates'],
            'successful_updates': self._data_quality_metrics['successful_updates'],
            'failed_updates': self._data_quality_metrics['failed_updates'],
            'success_rate': (self._data_quality_metrics['successful_updates'] / 
                           max(1, self._data_quality_metrics['total_updates'])) * 100,
            'last_update_time': self._data_quality_metrics['last_update_time'],
            'data_freshness': self._data_quality_metrics['data_freshness']
        }

    async def _get_real_candles(self, pair: str, timeframe: TimeFrame, count: int) -> List[CandleData]:
        """Get real candle data from OANDA API with enhanced error handling."""
        try:
            # Convert TimeFrame enum to OANDA granularity
            granularity_map = {
                TimeFrame.M1: "M1",
                TimeFrame.M5: "M5", 
                TimeFrame.M15: "M15",
                TimeFrame.M30: "M30",
                TimeFrame.H1: "H1",
                TimeFrame.H4: "H4",
                TimeFrame.D1: "D"
            }
            
            granularity = granularity_map.get(timeframe, "M5")
            
            # Fetch candles from OANDA with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    candles_data = self.oanda_api.fetch_candles(pair, count=count, granularity=granularity)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(1)  # Wait before retry
            
            if not candles_data:
                self.logger.warning(f"No candle data received for {pair} {timeframe}")
                return []
            
            # Convert OANDA data to CandleData objects
            candles = []
            for candle_data in candles_data:
                if candle_data.get('complete', False):  # Only complete candles
                    candle = CandleData(
                        timestamp=datetime.fromisoformat(candle_data['time'].replace('Z', '+00:00')),
                        open=Decimal(str(candle_data['mid']['o'])),
                        high=Decimal(str(candle_data['mid']['h'])),
                        low=Decimal(str(candle_data['mid']['l'])),
                        close=Decimal(str(candle_data['mid']['c'])),
                        volume=Decimal(str(candle_data.get('volume', 0))),
                        pair=pair,
                        timeframe=timeframe
                    )
                    candles.append(candle)
            
            self.logger.info(f"Fetched {len(candles)} real candles for {pair} {timeframe}")
            return candles
            
        except Exception as e:
            self.logger.error(f"Error fetching real candles for {pair} {timeframe}: {e}")
            return []
    
    async def _get_real_current_price(self, pair: str) -> Optional[Decimal]:
        """Get real current price from OANDA API with enhanced error handling."""
        try:
            # Get the latest candle to get current price
            candles = await self._get_real_candles(pair, TimeFrame.M5, 1)
            if candles:
                return candles[-1].close
            
            # Fallback: try to get prices endpoint
            prices_data = self.oanda_api.get_prices([pair])
            if prices_data:
                for price_obj in prices_data:
                    if price_obj.instrument == pair:
                        # Use bid price as current price
                        return Decimal(str(price_obj.bid))
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching real current price for {pair}: {e}")
            return None
