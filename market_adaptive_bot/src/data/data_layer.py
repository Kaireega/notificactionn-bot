"""
Data Layer - Handles real-time market data collection and storage.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import pandas as pd
import redis
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from ..core.models import CandleData, TimeFrame, MarketContext, MarketCondition
from ..utils.config import Config
from ..utils.logger import get_logger


class DataLayer:
    """Handles all data operations including real-time collection and storage."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize connections
        self._init_mongodb()
        self._init_redis()
        self._init_oanda_api()
        
        # Data caches
        self._candle_cache: Dict[str, List[CandleData]] = {}
        self._market_context_cache: Dict[str, MarketContext] = {}
        
        # Collection tasks
        self._collection_tasks: Dict[str, asyncio.Task] = {}
        self._running = False
    
    def _init_mongodb(self) -> None:
        """Initialize MongoDB connection."""
        try:
            self.mongo_client = MongoClient(self.config.mongodb_uri)
            self.db = self.mongo_client.trading_bot
            self.candles_collection = self.db.candles
            self.market_context_collection = self.db.market_context
            self.trades_collection = self.db.trades
            
            # Test connection
            self.mongo_client.admin.command('ping')
            self.logger.info("MongoDB connection established")
        except ConnectionFailure as e:
            self.logger.error(f"MongoDB connection failed: {e}")
            raise
    
    def _init_redis(self) -> None:
        """Initialize Redis connection for caching."""
        try:
            self.redis_client = redis.from_url(self.config.redis_url)
            self.redis_client.ping()
            self.logger.info("Redis connection established")
        except redis.ConnectionError as e:
            self.logger.error(f"Redis connection failed: {e}")
            raise
    
    def _init_oanda_api(self) -> None:
        """Initialize OANDA API client."""
        # This would integrate with your existing OANDA API
        # For now, we'll create a placeholder
        self.oanda_api = None  # TODO: Integrate with existing OANDA API
    
    async def start_data_collection(self) -> None:
        """Start real-time data collection for all configured pairs."""
        self._running = True
        
        for pair in self.config.trading_pairs:
            for timeframe in self.config.timeframes:
                task = asyncio.create_task(
                    self._collect_candle_data(pair, timeframe)
                )
                self._collection_tasks[f"{pair}_{timeframe}"] = task
        
        self.logger.info(f"Started data collection for {len(self._collection_tasks)} streams")
    
    async def stop_data_collection(self) -> None:
        """Stop all data collection tasks."""
        self._running = False
        
        for task in self._collection_tasks.values():
            task.cancel()
        
        await asyncio.gather(*self._collection_tasks.values(), return_exceptions=True)
        self._collection_tasks.clear()
        self.logger.info("Stopped all data collection tasks")
    
    async def _collect_candle_data(self, pair: str, timeframe: TimeFrame) -> None:
        """Collect candle data for a specific pair and timeframe."""
        while self._running:
            try:
                # Get latest candle data from OANDA
                candles = await self._fetch_latest_candles(pair, timeframe)
                
                if candles:
                    # Store in MongoDB
                    await self._store_candles(candles)
                    
                    # Update cache
                    cache_key = f"{pair}_{timeframe.value}"
                    self._candle_cache[cache_key] = candles
                    
                    # Update market context
                    await self._update_market_context(pair, timeframe, candles)
                
                # Wait for next update
                await asyncio.sleep(self.config.data_update_frequency)
                
            except Exception as e:
                self.logger.error(f"Error collecting data for {pair}_{timeframe}: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _fetch_latest_candles(self, pair: str, timeframe: TimeFrame) -> List[CandleData]:
        """Fetch latest candle data from OANDA API."""
        try:
            # This would integrate with your existing OANDA API
            # For now, return mock data
            return self._generate_mock_candles(pair, timeframe)
        except Exception as e:
            self.logger.error(f"Error fetching candles for {pair}: {e}")
            return []
    
    def _generate_mock_candles(self, pair: str, timeframe: TimeFrame) -> List[CandleData]:
        """Generate mock candle data for testing."""
        # This is for demonstration - replace with actual API calls
        import random
        
        candles = []
        base_price = 1.2000 if "USD" in pair else 100.0
        
        for i in range(100):
            timestamp = datetime.utcnow() - timedelta(minutes=i * 5)
            open_price = base_price + random.uniform(-0.01, 0.01)
            high_price = open_price + random.uniform(0, 0.005)
            low_price = open_price - random.uniform(0, 0.005)
            close_price = random.uniform(low_price, high_price)
            
            candle = CandleData(
                timestamp=timestamp,
                open=Decimal(str(open_price)),
                high=Decimal(str(high_price)),
                low=Decimal(str(low_price)),
                close=Decimal(str(close_price)),
                pair=pair,
                timeframe=timeframe
            )
            candles.append(candle)
        
        return candles
    
    async def _store_candles(self, candles: List[CandleData]) -> None:
        """Store candle data in MongoDB."""
        try:
            # Convert to dict format for MongoDB
            candle_docs = []
            for candle in candles:
                doc = {
                    "timestamp": candle.timestamp,
                    "pair": candle.pair,
                    "timeframe": candle.timeframe.value,
                    "open": float(candle.open),
                    "high": float(candle.high),
                    "low": float(candle.low),
                    "close": float(candle.close),
                    "volume": float(candle.volume) if candle.volume else None
                }
                candle_docs.append(doc)
            
            if candle_docs:
                # Use bulk operations for efficiency
                self.candles_collection.insert_many(candle_docs, ordered=False)
                
        except Exception as e:
            self.logger.error(f"Error storing candles: {e}")
    
    async def _update_market_context(self, pair: str, timeframe: TimeFrame, candles: List[CandleData]) -> None:
        """Update market context based on latest candle data."""
        if not candles:
            return
        
        try:
            # Calculate market context indicators
            context = self._calculate_market_context(candles)
            
            # Store in MongoDB
            context_doc = {
                "pair": pair,
                "timeframe": timeframe.value,
                "timestamp": datetime.utcnow(),
                "condition": context.condition.value,
                "volatility": context.volatility,
                "trend_strength": context.trend_strength,
                "news_sentiment": context.news_sentiment,
                "economic_events": context.economic_events,
                "key_levels": context.key_levels
            }
            
            self.market_context_collection.insert_one(context_doc)
            
            # Update cache
            cache_key = f"{pair}_{timeframe.value}_context"
            self._market_context_cache[cache_key] = context
            
        except Exception as e:
            self.logger.error(f"Error updating market context: {e}")
    
    def _calculate_market_context(self, candles: List[CandleData]) -> MarketContext:
        """Calculate market context from candle data."""
        if len(candles) < 20:
            return MarketContext()
        
        # Calculate volatility (ATR-like)
        highs = [float(c.high) for c in candles[-20:]]
        lows = [float(c.low) for c in candles[-20:]]
        closes = [float(c.close) for c in candles[-20:]]
        
        # Simple volatility calculation
        price_changes = [abs(closes[i] - closes[i-1]) for i in range(1, len(closes))]
        volatility = sum(price_changes) / len(price_changes) if price_changes else 0
        
        # Determine market condition
        condition = self._determine_market_condition(candles, volatility)
        
        # Calculate trend strength
        trend_strength = self._calculate_trend_strength(candles)
        
        return MarketContext(
            condition=condition,
            volatility=volatility,
            trend_strength=trend_strength,
            news_sentiment=0.0,  # Would be calculated from news data
            economic_events=[],  # Would be populated from economic calendar
            key_levels=self._calculate_key_levels(candles)
        )
    
    def _determine_market_condition(self, candles: List[CandleData], volatility: float) -> MarketCondition:
        """Determine market condition based on price action and volatility."""
        if len(candles) < 20:
            return MarketCondition.UNKNOWN
        
        # High volatility suggests news/reactionary market
        if volatility > self.config.market_conditions.volatility_threshold:
            return MarketCondition.NEWS_REACTIONARY
        
        # Check for ranging market (low volatility, sideways movement)
        if volatility < self.config.market_conditions.ranging_threshold:
            return MarketCondition.RANGING
        
        # Check for breakout conditions
        recent_highs = [float(c.high) for c in candles[-10:]]
        recent_lows = [float(c.low) for c in candles[-10:]]
        
        if max(recent_highs) > max([float(c.high) for c in candles[-20:-10]]):
            return MarketCondition.BREAKOUT
        
        # Check for reversal conditions
        if self._detect_reversal_pattern(candles):
            return MarketCondition.REVERSAL
        
        return MarketCondition.UNKNOWN
    
    def _detect_reversal_pattern(self, candles: List[CandleData]) -> bool:
        """Detect potential reversal patterns."""
        if len(candles) < 10:
            return False
        
        # Simple reversal detection based on price action
        recent_closes = [float(c.close) for c in candles[-5:]]
        previous_closes = [float(c.close) for c in candles[-10:-5]]
        
        # Check for trend change
        recent_trend = recent_closes[-1] - recent_closes[0]
        previous_trend = previous_closes[-1] - previous_closes[0]
        
        return (recent_trend * previous_trend) < 0  # Opposite trends
    
    def _calculate_trend_strength(self, candles: List[CandleData]) -> float:
        """Calculate trend strength using linear regression."""
        if len(candles) < 10:
            return 0.0
        
        # Simple trend strength calculation
        prices = [float(c.close) for c in candles[-10:]]
        x = list(range(len(prices)))
        
        # Linear regression
        n = len(prices)
        sum_x = sum(x)
        sum_y = sum(prices)
        sum_xy = sum(x[i] * prices[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        if n * sum_x2 - sum_x ** 2 == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        # Normalize slope to 0-1 range
        max_price = max(prices)
        trend_strength = abs(slope) / max_price if max_price > 0 else 0
        
        return min(trend_strength, 1.0)
    
    def _calculate_key_levels(self, candles: List[CandleData]) -> Dict[str, float]:
        """Calculate key support and resistance levels."""
        if len(candles) < 20:
            return {}
        
        highs = [float(c.high) for c in candles[-20:]]
        lows = [float(c.low) for c in candles[-20:]]
        
        return {
            "resistance": max(highs),
            "support": min(lows),
            "pivot": (max(highs) + min(lows)) / 2
        }
    
    async def get_latest_candles(self, pair: str, timeframe: TimeFrame, count: int = 100) -> List[CandleData]:
        """Get latest candle data for a pair and timeframe."""
        try:
            # Try cache first
            cache_key = f"{pair}_{timeframe.value}"
            if cache_key in self._candle_cache:
                cached_candles = self._candle_cache[cache_key]
                if len(cached_candles) >= count:
                    return cached_candles[-count:]
            
            # Fallback to database
            cursor = self.candles_collection.find(
                {"pair": pair, "timeframe": timeframe.value}
            ).sort("timestamp", -1).limit(count)
            
            candles = []
            for doc in cursor:
                candle = CandleData(
                    timestamp=doc["timestamp"],
                    open=Decimal(str(doc["open"])),
                    high=Decimal(str(doc["high"])),
                    low=Decimal(str(doc["low"])),
                    close=Decimal(str(doc["close"])),
                    volume=Decimal(str(doc["volume"])) if doc.get("volume") else None,
                    pair=doc["pair"],
                    timeframe=TimeFrame(doc["timeframe"])
                )
                candles.append(candle)
            
            return list(reversed(candles))  # Return in chronological order
            
        except Exception as e:
            self.logger.error(f"Error getting candles for {pair}: {e}")
            return []
    
    async def get_market_context(self, pair: str, timeframe: TimeFrame) -> Optional[MarketContext]:
        """Get current market context for a pair and timeframe."""
        try:
            # Try cache first
            cache_key = f"{pair}_{timeframe.value}_context"
            if cache_key in self._market_context_cache:
                return self._market_context_cache[cache_key]
            
            # Fallback to database
            doc = self.market_context_collection.find_one(
                {"pair": pair, "timeframe": timeframe.value},
                sort=[("timestamp", -1)]
            )
            
            if doc:
                return MarketContext(
                    condition=MarketCondition(doc["condition"]),
                    volatility=doc["volatility"],
                    trend_strength=doc["trend_strength"],
                    news_sentiment=doc["news_sentiment"],
                    economic_events=doc["economic_events"],
                    key_levels=doc["key_levels"],
                    timestamp=doc["timestamp"]
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting market context for {pair}: {e}")
            return None
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """Clean up old data to prevent database bloat."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Clean up old candles
            result = self.candles_collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            self.logger.info(f"Cleaned up {result.deleted_count} old candle records")
            
            # Clean up old market context
            result = self.market_context_collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            self.logger.info(f"Cleaned up {result.deleted_count} old market context records")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    async def close(self) -> None:
        """Close all database connections."""
        try:
            await self.stop_data_collection()
            self.mongo_client.close()
            self.redis_client.close()
            self.logger.info("Data layer connections closed")
        except Exception as e:
            self.logger.error(f"Error closing data layer: {e}") 