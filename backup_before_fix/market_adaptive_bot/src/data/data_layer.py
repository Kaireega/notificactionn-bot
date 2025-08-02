"""
Data Layer - Collects and manages market data.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import random

from core.models import CandleData, TimeFrame, MarketContext, MarketCondition
from utils.config import Config
from utils.logger import get_logger


class DataLayer:
    """Manages market data collection and storage."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Data storage
        self._candles: Dict[str, Dict[TimeFrame, List[CandleData]]] = {}
        self._market_contexts: Dict[str, MarketContext] = {}
        
        # Mock data generation
        self._base_prices = {
            'EUR_USD': Decimal('1.0850'),
            'GBP_USD': Decimal('1.2650'),
            'USD_JPY': Decimal('150.50'),
            'USD_CAD': Decimal('1.3550'),
            'AUD_USD': Decimal('0.6650'),
            'NZD_USD': Decimal('0.6150')
        }
        
        self._is_running = False
        self._update_task = None
    
    async def start(self) -> None:
        """Start the data layer."""
        self.logger.info("Starting data layer...")
        self._is_running = True
        
        # Initialize data for all pairs
        for pair in self.config.trading_pairs:
            await self._initialize_pair_data(pair)
        
        # Start data update loop
        self._update_task = asyncio.create_task(self._data_update_loop())
        self.logger.info("Data layer started successfully")
    
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
        
        if pair not in self._candles or timeframe not in self._candles[pair]:
            return []
        
        candles = self._candles[pair][timeframe]
        return candles[-count:] if len(candles) >= count else candles
    
    async def get_market_context(self, pair: str) -> MarketContext:
        """Get market context for a pair."""
        return self._market_contexts.get(pair, MarketContext())
    
    async def get_current_price(self, pair: str) -> Optional[Decimal]:
        """Get current price for a pair."""
        if pair in self._candles and TimeFrame.M5 in self._candles[pair]:
            candles = self._candles[pair][TimeFrame.M5]
            if candles:
                return candles[-1].close
        return None
    
    async def _initialize_pair_data(self, pair: str) -> None:
        """Initialize data for a trading pair."""
        self.logger.info(f"Initializing data for {pair}")
        
        # Initialize candle storage
        if pair not in self._candles:
            self._candles[pair] = {}
        
        # Generate historical data for each timeframe
        for timeframe in self.config.timeframes:
            candles = await self._generate_historical_candles(pair, timeframe)
            self._candles[pair][timeframe] = candles
        
        # Initialize market context
        self._market_contexts[pair] = MarketContext(
            condition=MarketCondition.RANGING,
            volatility=0.001,
            trend_strength=0.5,
            news_sentiment=0.0,
            timestamp=datetime.utcnow()
        )
    
    async def _generate_historical_candles(self, pair: str, timeframe: TimeFrame) -> List[CandleData]:
        """Generate historical candle data for testing."""
        candles = []
        base_price = self._base_prices.get(pair, Decimal('1.0000'))
        
        # Generate 200 candles (about 1 week of M5 data)
        for i in range(200):
            # Calculate timestamp
            minutes_back = (200 - i) * 5  # 5-minute candles
            timestamp = datetime.utcnow() - timedelta(minutes=minutes_back)
            
            # Generate price movement
            price_change = Decimal(str(random.uniform(-0.002, 0.002)))
            current_price = base_price + price_change
            
            # Generate OHLCV
            open_price = current_price
            high_price = current_price + Decimal(str(random.uniform(0, 0.001)))
            low_price = current_price - Decimal(str(random.uniform(0, 0.001)))
            close_price = current_price + Decimal(str(random.uniform(-0.0005, 0.0005)))
            volume = Decimal(str(random.uniform(1000, 5000)))
            
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
        while self._is_running:
            try:
                await self._update_all_data()
                await asyncio.sleep(self.config.data_update_frequency)
            except Exception as e:
                self.logger.error(f"Error in data update loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _update_all_data(self) -> None:
        """Update data for all pairs."""
        for pair in self.config.trading_pairs:
            await self._update_pair_data(pair)
    
    async def _update_pair_data(self, pair: str) -> None:
        """Update data for a specific pair."""
        try:
            # Generate new candle for each timeframe
            for timeframe in self.config.timeframes:
                new_candle = await self._generate_new_candle(pair, timeframe)
                if new_candle:
                    self._candles[pair][timeframe].append(new_candle)
                    
                    # Keep only last 1000 candles to prevent memory issues
                    if len(self._candles[pair][timeframe]) > 1000:
                        self._candles[pair][timeframe] = self._candles[pair][timeframe][-1000:]
            
            # Update market context
            await self._update_market_context(pair)
                
        except Exception as e:
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
            
            # Generate price movement
            price_change = Decimal(str(random.uniform(-0.001, 0.001)))
            current_price = last_candle.close + price_change
            
            # Generate OHLCV
            open_price = last_candle.close
            high_price = max(open_price, current_price) + Decimal(str(random.uniform(0, 0.0005)))
            low_price = min(open_price, current_price) - Decimal(str(random.uniform(0, 0.0005)))
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
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error updating market context for {pair}: {e}")
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility."""
        if len(prices) < 2:
            return 0.0
        
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        return float(sum(abs(r) for r in returns) / len(returns))
    
    def _determine_market_condition(self, candles: List[CandleData], volatility: float) -> MarketCondition:
        """Determine market condition based on price action."""
        if volatility > 0.002:
            return MarketCondition.NEWS_REACTIONARY
        elif volatility > 0.0015:
            return MarketCondition.BREAKOUT
        elif volatility > 0.001:
            return MarketCondition.REVERSAL
        else:
            return MarketCondition.RANGING
    
    def _calculate_trend_strength(self, candles: List[CandleData]) -> float:
        """Calculate trend strength."""
        if len(candles) < 10:
            return 0.5
        
        # Simple trend calculation
        first_price = float(candles[0].close)
        last_price = float(candles[-1].close)
        
        price_change = (last_price - first_price) / first_price
        return min(abs(price_change) * 10, 1.0)  # Scale to 0-1
    
    async def get_all_pairs_data(self) -> Dict[str, Dict[str, Any]]:
        """Get data for all pairs."""
        result = {}
        
        for pair in self.config.trading_pairs:
            result[pair] = {
                'current_price': await self.get_current_price(pair),
                'market_context': await self.get_market_context(pair),
                'candles': {
                    timeframe.value: await self.get_candles(pair, timeframe, 50)
                    for timeframe in self.config.timeframes
                }
            }
        
        return result 