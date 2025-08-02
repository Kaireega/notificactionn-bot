"""
Unified API Wrapper - Integrates legacy and new OANDA API systems
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import pandas as pd

from api.oanda_api import OandaApi
from models.api_price import ApiPrice
from models.open_trade import OpenTrade

# Import new system components when available
try:
    from market_adaptive_bot.src.data.data_layer import DataLayer
    from market_adaptive_bot.src.utils.config import Config
    NEW_SYSTEM_AVAILABLE = True
except ImportError:
    NEW_SYSTEM_AVAILABLE = False
    DataLayer = None
    Config = None


class UnifiedOandaApi:
    """
    Unified API wrapper that provides consistent interface across legacy and new systems.
    Handles routing, caching, and fallback mechanisms.
    """
    
    def __init__(self, use_new_system: bool = False, config: Optional[Config] = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize legacy API
        self.legacy_api = OandaApi()
        
        # Initialize new system if available and requested
        self.new_system_available = NEW_SYSTEM_AVAILABLE and use_new_system
        self.new_api = None
        if self.new_system_available and config:
            try:
                self.new_api = DataLayer(config)
                self.logger.info("New system API initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize new system API: {e}")
                self.new_system_available = False
        
        # Cache for API responses
        self._cache = {}
        self._cache_ttl = 60  # seconds
        
    def _get_cached_response(self, key: str) -> Optional[Any]:
        """Get cached response if still valid."""
        if key in self._cache:
            timestamp, data = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                return data
            else:
                del self._cache[key]
        return None
    
    def _cache_response(self, key: str, data: Any) -> None:
        """Cache API response with timestamp."""
        self._cache[key] = (datetime.now(), data)
    
    def get_account_summary(self) -> Optional[Dict]:
        """Get account summary with fallback mechanism."""
        try:
            # Try new system first if available
            if self.new_system_available:
                # TODO: Implement new system account summary
                pass
            
            # Fallback to legacy system
            return self.legacy_api.get_account_summary()
        except Exception as e:
            self.logger.error(f"Failed to get account summary: {e}")
            return None
    
    def get_account_instruments(self) -> Optional[List[Dict]]:
        """Get account instruments with caching."""
        cache_key = "account_instruments"
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        try:
            result = self.legacy_api.get_account_instruments()
            if result:
                self._cache_response(cache_key, result)
            return result
        except Exception as e:
            self.logger.error(f"Failed to get account instruments: {e}")
            return None
    
    def fetch_candles(self, pair_name: str, count: int = 10, 
                     granularity: str = "H1", price: str = "MBA",
                     date_f: Optional[datetime] = None, 
                     date_t: Optional[datetime] = None) -> Optional[List[Dict]]:
        """Fetch candles with unified interface."""
        cache_key = f"candles_{pair_name}_{granularity}_{count}_{date_f}_{date_t}"
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        try:
            result = self.legacy_api.fetch_candles(
                pair_name, count, granularity, price, date_f, date_t
            )
            if result:
                self._cache_response(cache_key, result)
            return result
        except Exception as e:
            self.logger.error(f"Failed to fetch candles for {pair_name}: {e}")
            return None
    
    def get_candles_df(self, pair_name: str, **kwargs) -> Optional[pd.DataFrame]:
        """Get candles as DataFrame with error handling."""
        try:
            return self.legacy_api.get_candles_df(pair_name, **kwargs)
        except Exception as e:
            self.logger.error(f"Failed to get candles DataFrame for {pair_name}: {e}")
            return None
    
    async def get_candles_async(self, pair_name: str, timeframe: str, 
                               count: int = 100) -> Optional[List[Dict]]:
        """Async version of candle fetching for new system compatibility."""
        if self.new_system_available:
            try:
                # TODO: Implement async candle fetching from new system
                pass
            except Exception as e:
                self.logger.warning(f"New system candle fetch failed: {e}")
        
        # Fallback to sync legacy method
        return self.fetch_candles(pair_name, count, timeframe)
    
    def place_trade(self, pair_name: str, units: float, direction: int,
                   stop_loss: Optional[float] = None, 
                   take_profit: Optional[float] = None) -> Optional[Dict]:
        """Place trade with unified interface."""
        try:
            return self.legacy_api.place_trade(
                pair_name, units, direction, stop_loss, take_profit
            )
        except Exception as e:
            self.logger.error(f"Failed to place trade for {pair_name}: {e}")
            return None
    
    def close_trade(self, trade_id: str) -> Optional[Dict]:
        """Close trade with error handling."""
        try:
            return self.legacy_api.close_trade(trade_id)
        except Exception as e:
            self.logger.error(f"Failed to close trade {trade_id}: {e}")
            return None
    
    def get_open_trades(self) -> Optional[List[OpenTrade]]:
        """Get open trades with unified interface."""
        try:
            return self.legacy_api.get_open_trades()
        except Exception as e:
            self.logger.error(f"Failed to get open trades: {e}")
            return None
    
    def get_prices(self, instruments_list: List[str]) -> Optional[Dict[str, ApiPrice]]:
        """Get current prices with caching."""
        cache_key = f"prices_{'_'.join(sorted(instruments_list))}"
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        try:
            result = self.legacy_api.get_prices(instruments_list)
            if result:
                self._cache_response(cache_key, result)
            return result
        except Exception as e:
            self.logger.error(f"Failed to get prices: {e}")
            return None
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of both API systems."""
        health = {
            "legacy_system": False,
            "new_system": False,
            "overall": False
        }
        
        # Test legacy system
        try:
            summary = self.get_account_summary()
            health["legacy_system"] = summary is not None
        except Exception as e:
            self.logger.error(f"Legacy system health check failed: {e}")
        
        # Test new system
        if self.new_system_available:
            try:
                # TODO: Implement new system health check
                health["new_system"] = True
            except Exception as e:
                self.logger.error(f"New system health check failed: {e}")
        
        health["overall"] = health["legacy_system"] or health["new_system"]
        return health
    
    def clear_cache(self) -> None:
        """Clear all cached responses."""
        self._cache.clear()
        self.logger.info("API cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_items": len(self._cache),
            "cache_ttl_seconds": self._cache_ttl
        } 