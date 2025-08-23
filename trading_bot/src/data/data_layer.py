"""
Data Layer - Collects and manages market data.
"""
import asyncio
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal
import random
import sys
from pathlib import Path

# Add the root directory to the path to import OANDA API
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


class DataLayer:
    """Manages market data collection and storage."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Data storage
        self._candles: Dict[str, Dict[TimeFrame, List[CandleData]]] = {}
        self._market_contexts: Dict[str, MarketContext] = {}
        
        # OANDA API integration
        if OANDA_AVAILABLE:
            self.oanda_api = OandaApi()
            # Use real OANDA data - set to True for live trading
            self.use_real_data = True
            self.logger.info("Using real OANDA API data")
        else:
            self.oanda_api = None
            self.use_real_data = False
            self.logger.warning("Using mock data - OANDA API not available")
        
        # Mock data generation (fallback)
        self._base_prices = {
            'EUR_USD': Decimal('1.1050'),  # Updated to match current market
            'GBP_USD': Decimal('1.2650'),
            'USD_JPY': Decimal('150.50'),
            'GBP_JPY': Decimal('195.50'),  # Added missing GBP_JPY base price
            'USD_CAD': Decimal('1.3550'),
            'AUD_USD': Decimal('0.6650'),
            'NZD_USD': Decimal('0.6150')
        }
        
        self._is_running = False
        self._update_task = None
    
    async def _validate_oanda_credentials(self) -> bool:
        """Validate OANDA API credentials."""
        try:
            if self.use_real_data and self.oanda_api:
                return self.oanda_api.validate_credentials()
            return True
        except Exception as e:
            self.logger.error(f"Error validating OANDA credentials: {e}")
            return False

    async def start(self):
        """Start the data layer."""
        try:
            # Validate OANDA credentials
            if not await self._validate_oanda_credentials():
                raise Exception("Invalid OANDA credentials")
            
            # Initialize data for all trading pairs
            for pair in self.config.trading_pairs:
                await self._initialize_pair_data(pair)
            
            # Start data update loop
            asyncio.create_task(self._data_update_loop())
            
            self.logger.info("Data layer started successfully")
            
        except Exception as e:
            print(f"❌ [DEBUG] Error starting data layer: {e}")
            self.logger.error(f"Error starting data layer: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the data layer."""
        self.logger.info("Stopping data layer...")
        self._is_running = False
        
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Data layer stopped")
    
    async def get_candles(
        self, 
        pair: str, 
        timeframe: TimeFrame, 
        count: int = 100
    ) -> List[CandleData]:
        """Get candle data for a pair and timeframe."""
        
        if self.use_real_data and self.oanda_api:
            return await self._get_real_candles(pair, timeframe, count)
        else:
            # Fallback to mock data
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
        """Initialize data for a trading pair."""
        print(f"📊 [DEBUG] Initializing data for {pair}")
        self.logger.info(f"Initializing data for {pair}")
        
        # Initialize candle storage
        if pair not in self._candles:
            self._candles[pair] = {}
            print(f"📊 [DEBUG] {pair}: Created candle storage")
        
        # Get historical data for each timeframe
        print(f"📊 [DEBUG] {pair}: Getting data for {len(self.config.timeframes)} timeframes: {[tf.value for tf in self.config.timeframes]}")
        for timeframe in self.config.timeframes:
            print(f"📊 [DEBUG] {pair}: Getting {timeframe.value} data...")
            if self.use_real_data and self.oanda_api:
                # Get real data from API
                print(f"📊 [DEBUG] {pair}: Using real OANDA API data")
                candles = await self._get_real_candles(pair, timeframe, 200)
            else:
                # Generate mock data for testing
                print(f"📊 [DEBUG] {pair}: Using mock data")
                candles = await self._generate_historical_candles(pair, timeframe)
            
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
    
    async def _generate_historical_candles(self, pair: str, timeframe: TimeFrame) -> List[CandleData]:
        """Generate historical candle data for testing with more volatility to trigger trades."""
        candles = []
        base_price = self._base_prices.get(pair, Decimal('1.0000'))
        
        # Generate 200 candles with more volatile patterns
        current_price = base_price
        trend_direction = random.choice([-1, 1])  # Random trend direction
        trend_strength = random.uniform(0.5, 1.0)  # Trend strength
        
        for i in range(200):
            # Calculate timestamp
            minutes_back = (200 - i) * 5  # 5-minute candles
            timestamp = datetime.now(timezone.utc) - timedelta(minutes=minutes_back)
            
            # Create more volatile price movements with trends
            if i < 50:  # First 50 candles - strong trend
                price_change_pct = random.uniform(-0.005, 0.005) * trend_direction * trend_strength
            elif i < 100:  # Next 50 candles - reversal
                price_change_pct = random.uniform(-0.003, 0.003) * (-trend_direction) * 0.7
            elif i < 150:  # Next 50 candles - consolidation
                price_change_pct = random.uniform(-0.002, 0.002)
            else:  # Last 50 candles - breakout
                price_change_pct = random.uniform(-0.008, 0.008) * trend_direction * 1.2
            
            price_change = current_price * Decimal(str(price_change_pct))
            current_price = current_price + price_change
            
            # Generate OHLCV with more realistic movements
            open_price = current_price
            high_price = current_price + (current_price * Decimal(str(random.uniform(0, 0.002))))
            low_price = current_price - (current_price * Decimal(str(random.uniform(0, 0.002))))
            close_price = current_price + (current_price * Decimal(str(random.uniform(-0.001, 0.001))))
            volume = Decimal(str(random.uniform(2000, 8000)))
            
            candle = CandleData(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                pair=pair,
                timeframe=timeframe
            )
            
            candles.append(candle)
        
        return candles
    
    async def _data_update_loop(self) -> None:
        """Main data update loop."""
        print("🔄 [DEBUG] Data update loop started")
        update_count = 0
        while self._is_running:
            try:
                update_count += 1
                print(f"🔄 [DEBUG] Data update iteration {update_count}")
                await self._update_all_data()
                print(f"⏰ [DEBUG] Waiting {self.config.data_update_frequency} seconds for next update...")
                await asyncio.sleep(self.config.data_update_frequency)
            except Exception as e:
                print(f"❌ [DEBUG] Error in data update loop: {e}")
                print(f"❌ [DEBUG] Traceback: {traceback.format_exc()}")
                self.logger.error(f"Error in data update loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _update_all_data(self) -> None:
        """Update data for all pairs."""
        print(f"📊 [DEBUG] Updating data for {len(self.config.trading_pairs)} pairs")
        for pair in self.config.trading_pairs:
            print(f"📊 [DEBUG] Updating data for {pair}...")
            await self._update_pair_data(pair)
            print(f"✅ [DEBUG] Data updated for {pair}")
    
    async def _update_pair_data(self, pair: str) -> None:
        """Update data for a specific pair."""
        try:
            print(f"📊 [DEBUG] {pair}: Starting data update...")
            
            # Update candles for each timeframe
            for timeframe in self.config.timeframes:
                print(f"📊 [DEBUG] {pair}: Updating {timeframe.value} data...")
                if self.use_real_data and self.oanda_api:
                    # Get fresh real data from API
                    print(f"📊 [DEBUG] {pair}: Getting fresh real data for {timeframe.value}")
                    new_candles = await self._get_real_candles(pair, timeframe, 50)
                    if new_candles:
                        # Replace with fresh data, keeping only the latest candles
                        self._candles[pair][timeframe] = new_candles[-1000:]  # Keep last 1000
                        print(f"📊 [DEBUG] {pair}: {timeframe.value} - Updated with {len(new_candles)} candles")
                    else:
                        print(f"⚠️ [DEBUG] {pair}: {timeframe.value} - No new candles received")
                else:
                    # Generate new mock candle
                    print(f"📊 [DEBUG] {pair}: Generating new mock candle for {timeframe.value}")
                    new_candle = await self._generate_new_candle(pair, timeframe)
                    if new_candle:
                        self._candles[pair][timeframe].append(new_candle)
                        
                        # Keep only last 1000 candles to prevent memory issues
                        if len(self._candles[pair][timeframe]) > 1000:
                            self._candles[pair][timeframe] = self._candles[pair][timeframe][-1000:]
                        print(f"📊 [DEBUG] {pair}: {timeframe.value} - Added new mock candle")
                    else:
                        print(f"⚠️ [DEBUG] {pair}: {timeframe.value} - Failed to generate mock candle")
            
            # Update market context
            print(f"🌍 [DEBUG] {pair}: Updating market context...")
            await self._update_market_context(pair)
            print(f"✅ [DEBUG] {pair}: Market context updated")
                
        except Exception as e:
            print(f"❌ [DEBUG] {pair}: Error updating data: {e}")
            print(f"❌ [DEBUG] {pair}: Traceback: {traceback.format_exc()}")
            self.logger.error(f"Error updating data for {pair}: {e}")
    
    async def _generate_new_candle(self, pair: str, timeframe: TimeFrame) -> Optional[CandleData]:
        """Generate a new candle for the pair."""
        try:
            # Get the last candle
            candles = self._candles[pair][timeframe]
            if not candles:
                return None
            
            last_candle = candles[-1]
            
            # Calculate new timestamp
            if timeframe == TimeFrame.M1:
                minutes = 1
            elif timeframe == TimeFrame.M5:
                minutes = 5
            elif timeframe == TimeFrame.M15:
                minutes = 15
            elif timeframe == TimeFrame.H1:
                minutes = 60
            else:
                minutes = 5
            
            timestamp = last_candle.timestamp + timedelta(minutes=minutes)
            
            # Generate price movement proportional to current price
            price_change_pct = random.uniform(-0.001, 0.001)  # 0.1% movement
            price_change = last_candle.close * Decimal(str(price_change_pct))
            current_price = last_candle.close + price_change
            
            # Generate OHLCV with proportional movements
            open_price = last_candle.close
            high_price = max(open_price, current_price) + (current_price * Decimal(str(random.uniform(0, 0.0003))))
            low_price = min(open_price, current_price) - (current_price * Decimal(str(random.uniform(0, 0.0003))))
            close_price = current_price
            volume = Decimal(str(random.uniform(1000, 5000)))
            
            return CandleData(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                pair=pair,
                timeframe=timeframe
            )
            
        except Exception as e:
            self.logger.error(f"Error generating new candle for {pair}: {e}")
            return None
    
    async def _update_market_context(self, pair: str) -> None:
        """Update market context for a pair."""
        try:
            # Get recent candles for analysis
            recent_candles = await self.get_candles(pair, TimeFrame.M5, 20)
            if not recent_candles:
                self.logger.warning(f"No recent candles available for {pair} market context update")
                return
            
            # Calculate volatility
            prices = [float(c.close) for c in recent_candles]
            volatility = self._calculate_volatility(prices)
        
            # Determine market condition
            condition = self._determine_market_condition(recent_candles, volatility)
        
            # Calculate trend strength
            trend_strength = self._calculate_trend_strength(recent_candles)
        
            # Update market context
            self._market_contexts[pair] = MarketContext(
                condition=condition,
                volatility=volatility,
                trend_strength=trend_strength,
                news_sentiment=0.0,  # Mock value
                timestamp=datetime.now(timezone.utc)
            )
            
            # Log market context update
            self.logger.debug(f"📊 Market context updated for {pair}: "
                            f"Condition={condition.value}, "
                            f"Volatility={volatility:.3f}%, "
                            f"Trend Strength={trend_strength:.3f}")
            
        except Exception as e:
            self.logger.error(f"Error updating market context for {pair}: {e}")
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility."""
        if len(prices) < 2:
            return 0.0
        
        # Calculate percentage returns
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        # Calculate average absolute return (volatility)
        avg_abs_return = sum(abs(r) for r in returns) / len(returns)
        
        # Convert to percentage (multiply by 100 for display)
        volatility_percentage = avg_abs_return * 100
        
        # Debug logging
        if len(prices) > 0:
            self.logger.debug(f"Volatility calculation: {len(prices)} prices, "
                            f"range: {min(prices):.5f}-{max(prices):.5f}, "
                            f"returns: {[f'{r:.6f}' for r in returns[:3]]}..., "
                            f"volatility: {volatility_percentage:.6f}%")
        
        return volatility_percentage
    
    def _determine_market_condition(self, candles: List[CandleData], volatility: float) -> MarketCondition:
        """Determine market condition based on price action."""
        # Volatility is now in percentage (0.1 = 0.1%)
        if volatility > 0.2:  # > 0.2%
            return MarketCondition.NEWS_REACTIONARY
        elif volatility > 0.15:  # > 0.15%
            return MarketCondition.BREAKOUT
        elif volatility > 0.1:  # > 0.1%
            return MarketCondition.REVERSAL
        else:
            return MarketCondition.RANGING
    
    def _calculate_trend_strength(self, candles: List[CandleData]) -> float:
        """Calculate trend strength."""
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
        
        # Normalize slope to trend strength (0-1)
        # Use price range to normalize
        price_range = max(prices) - min(prices)
        if price_range == 0:
            return 0.0
        
        # Calculate trend strength based on slope relative to price range
        trend_strength = min(abs(slope * n / price_range), 1.0)
        
        return trend_strength
    
    async def get_all_data(self) -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
        """Get candles data for all pairs and timeframes."""
        result = {}
        
        for pair in self.config.trading_pairs:
            try:
                # Get candles for all timeframes
                candles = {}
                for timeframe in self.config.timeframes:
                    timeframe_candles = await self.get_candles(pair, timeframe, 50)
                    candles[timeframe] = timeframe_candles
                
                result[pair] = candles
                
            except Exception as e:
                self.logger.error(f"Error getting data for {pair}: {e}")
                result[pair] = {}
        
        return result

    async def get_all_pairs_data(self) -> Dict[str, Dict[str, Any]]:
        """Get data for all pairs."""
        result = {}
        
        for pair in self.config.trading_pairs:
            try:
                # Get current price
                current_price = await self.get_current_price(pair)
                
                # Get market context
                market_context = await self.get_market_context(pair)
                
                # Get candles for all timeframes
                candles = {}
                for timeframe in self.config.timeframes:
                    timeframe_candles = await self.get_candles(pair, timeframe, 50)
                    candles[timeframe.value] = timeframe_candles
                
                result[pair] = {
                    'current_price': current_price,
                    'market_context': market_context,
                    'candles': candles
                }
                
            except Exception as e:
                self.logger.error(f"❌ Error getting data for {pair}: {e}")
                result[pair] = {
                    'current_price': None,
                    'market_context': None,
                    'candles': {}
                }
        
        return result

    async def _get_real_candles(self, pair: str, timeframe: TimeFrame, count: int) -> List[CandleData]:
        """Get real candle data from OANDA API."""
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
            
            # Fetch candles from OANDA
            candles_data = self.oanda_api.fetch_candles(pair, count=count, granularity=granularity)
            
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
        """Get real current price from OANDA API."""
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