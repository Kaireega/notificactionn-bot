"""
Improved Fundamental Analysis Integration Layer - Smart caching and targeted data scraping.
Only scrapes necessary data and caches relevant information to avoid redundant requests.
"""
import asyncio
import logging
import urllib3
import json
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Set
from decimal import Decimal
import pytz
import pickle
import os
from pathlib import Path

import sys
from pathlib import Path

# Add the project root to the path to import API modules
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.append(str(root_dir))

from scraping.fx_calendar import get_fx_calendar
from scraping.bloomberg_com import bloomberg_com
from scraping.dailyfx_com import dailyfx_com
from db.db import DataDB
from ..core.models import MarketContext, MarketCondition
from ..utils.config import Config
from ..utils.logger import get_logger


class ImprovedFundamentalAnalyzer:
    """Enhanced fundamental analysis with smart caching and targeted data scraping."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        print("🔧 [DEBUG] Initializing Improved Fundamental Analyzer...")
        
        # Initialize database connection
        self.db = None
        self.db_available = False
        if getattr(self.config, 'enable_db', False):
            try:
                self.db = DataDB()
                self.db_available = True
                print("✅ [DEBUG] Database connection established")
            except Exception as e:
                print(f"❌ [DEBUG] Database connection failed: {e}")
                self.db = None
                self.db_available = False
        
        # Smart cache system with relevance tracking
        self._cache_dir = Path("cache/fundamental_analysis")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._calendar_cache = {}
        self._news_cache = {}
        self._sentiment_cache = {}
        self._last_update = None
        self._cache_duration = timedelta(minutes=30)  # Increased cache duration
        
        # Relevance tracking
        self._relevant_currencies = set()
        self._relevant_events = set()
        self._last_relevance_check = None
        self._relevance_check_interval = timedelta(hours=2)
        
        # Market session times (UTC)
        self.sessions = {
            'tokyo': {'start': 0, 'end': 9},
            'london': {'start': 8, 'end': 17},
            'new_york': {'start': 13, 'end': 22}
        }
        
        # High-impact events with relevance scoring
        self.high_impact_events = {
            'NFP': {'impact': 10, 'currencies': ['USD'], 'cache_duration': timedelta(hours=6)},
            'CPI': {'impact': 9, 'currencies': ['USD', 'EUR', 'GBP', 'JPY'], 'cache_duration': timedelta(hours=4)},
            'PPI': {'impact': 8, 'currencies': ['USD', 'EUR', 'GBP'], 'cache_duration': timedelta(hours=3)},
            'GDP': {'impact': 9, 'currencies': ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD'], 'cache_duration': timedelta(hours=6)},
            'FOMC': {'impact': 10, 'currencies': ['USD'], 'cache_duration': timedelta(hours=8)},
            'ECB': {'impact': 10, 'currencies': ['EUR'], 'cache_duration': timedelta(hours=8)},
            'BOE': {'impact': 9, 'currencies': ['GBP'], 'cache_duration': timedelta(hours=6)},
            'BOJ': {'impact': 8, 'currencies': ['JPY'], 'cache_duration': timedelta(hours=6)},
            'RBA': {'impact': 7, 'currencies': ['AUD'], 'cache_duration': timedelta(hours=4)},
            'BOC': {'impact': 7, 'currencies': ['CAD'], 'cache_duration': timedelta(hours=4)}
        }
        
        # Currency correlations for targeted analysis
        self.correlations = {
            'USD_PAIRS': ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CAD', 'AUD_USD', 'NZD_USD'],
            'JPY_PAIRS': ['USD_JPY', 'EUR_JPY', 'GBP_JPY', 'AUD_JPY'],
            'EUR_PAIRS': ['EUR_USD', 'EUR_JPY', 'EUR_GBP'],
            'GBP_PAIRS': ['GBP_USD', 'GBP_JPY', 'EUR_GBP'],
            'COMMODITY_PAIRS': ['AUD_USD', 'NZD_USD', 'USD_CAD']
        }
        
        # Load existing cache
        self._load_cache()
        
        print("✅ [DEBUG] Improved Fundamental Analyzer initialization complete")
    
    def _load_cache(self):
        """Load cached data from disk."""
        try:
            cache_file = self._cache_dir / "fundamental_cache.pkl"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    self._calendar_cache = cache_data.get('calendar', {})
                    self._news_cache = cache_data.get('news', {})
                    self._sentiment_cache = cache_data.get('sentiment', {})
                    self._last_update = cache_data.get('last_update')
                    self._relevant_currencies = cache_data.get('relevant_currencies', set())
                    self._relevant_events = cache_data.get('relevant_events', set())
                    self._last_relevance_check = cache_data.get('last_relevance_check')
                
                print(f"💾 [DEBUG] Loaded cache: {len(self._calendar_cache)} calendar, {len(self._news_cache)} news")
        except Exception as e:
            print(f"⚠️ [DEBUG] Could not load cache: {e}")
    
    def _save_cache(self):
        """Save cache data to disk."""
        try:
            cache_data = {
                'calendar': self._calendar_cache,
                'news': self._news_cache,
                'sentiment': self._sentiment_cache,
                'last_update': self._last_update,
                'relevant_currencies': self._relevant_currencies,
                'relevant_events': self._relevant_events,
                'last_relevance_check': self._last_relevance_check
            }
            
            cache_file = self._cache_dir / "fundamental_cache.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            print("💾 [DEBUG] Cache saved to disk")
        except Exception as e:
            print(f"⚠️ [DEBUG] Could not save cache: {e}")
    
    async def start(self) -> None:
        """Start improved fundamental analysis system."""
        print("📰 [DEBUG] Starting improved fundamental analyzer...")
        self.logger.info("Starting improved fundamental analyzer...")
        
        # Check relevance and load only necessary data
        await self._check_relevance_and_load_data()
        
        print("✅ [DEBUG] Improved fundamental analyzer started")
    
    async def stop(self) -> None:
        """Stop fundamental analysis system."""
        print("📰 [DEBUG] Stopping improved fundamental analyzer...")
        self._save_cache()
        self.logger.info("Improved fundamental analyzer stopped")
    
    async def _check_relevance_and_load_data(self):
        """Check what data is relevant and load only necessary information."""
        now = datetime.now(timezone.utc)
        
        # Check if we need to update relevance
        if (self._last_relevance_check is None or 
            now - self._last_relevance_check > self._relevance_check_interval):
            
            print("🔍 [DEBUG] Checking data relevance...")
            
            # Determine relevant currencies based on trading pairs
            self._relevant_currencies = self._get_relevant_currencies()
            
            # Determine relevant events based on currencies
            self._relevant_events = self._get_relevant_events()
            
            self._last_relevance_check = now
            print(f"🎯 [DEBUG] Relevant currencies: {self._relevant_currencies}")
            print(f"📅 [DEBUG] Relevant events: {self._relevant_events}")
        
        # Load only relevant data
        await self._load_relevant_calendar_data()
        await self._load_relevant_news_data()
    
    def _get_relevant_currencies(self) -> Set[str]:
        """Get currencies relevant to current trading pairs."""
        currencies = set()
        
        for pair in self.config.trading_pairs:
            base, quote = pair.split('_')
            currencies.add(base)
            currencies.add(quote)
        
        return currencies
    
    def _get_relevant_events(self) -> Set[str]:
        """Get events relevant to current currencies."""
        events = set()
        
        for event_name, event_data in self.high_impact_events.items():
            if any(currency in self._relevant_currencies for currency in event_data['currencies']):
                events.add(event_name)
        
        return events
    
    async def _load_relevant_calendar_data(self):
        """Load only relevant calendar data with smart caching."""
        print("📅 [DEBUG] Loading relevant calendar data...")
        
        try:
            now = datetime.now(timezone.utc)
            cache_key = f"calendar_{now.strftime('%Y-%m-%d')}"
            
            # Check if we have recent, relevant cached data
            if (cache_key in self._calendar_cache and 
                self._calendar_cache[cache_key].get('timestamp') and
                now - self._calendar_cache[cache_key]['timestamp'] < self._cache_duration):
                
                cached_data = self._calendar_cache[cache_key]['data']
                relevant_data = self._filter_relevant_events(cached_data)
                
                if relevant_data:
                    print(f"✅ [DEBUG] Using cached calendar data: {len(relevant_data)} relevant events")
                    return
            
            # Need to scrape new data
            print("📅 [DEBUG] Scraping fresh calendar data...")
            from_date = now - timedelta(days=1)
            calendar_data = get_fx_calendar(from_date)
            
            if calendar_data:
                # Filter for relevant events only
                relevant_data = self._filter_relevant_events(calendar_data)
                
                # Cache the filtered data
                self._calendar_cache[cache_key] = {
                    'data': relevant_data,
                    'timestamp': now,
                    'total_events': len(calendar_data),
                    'relevant_events': len(relevant_data)
                }
                
                print(f"📊 [DEBUG] Scraped {len(calendar_data)} total events, {len(relevant_data)} relevant")
                
                # Store in database if available
                if self.db_available and self.db:
                    self.db.add_many(DataDB.CALENDAR_COLL, relevant_data)
                    print("💾 [DEBUG] Relevant calendar data stored in database")
            else:
                print("⚠️ [DEBUG] No calendar data retrieved")
                
        except Exception as e:
            print(f"❌ [DEBUG] Error loading relevant calendar data: {e}")
            self.logger.error(f"Error loading relevant calendar data: {e}")
    
    def _filter_relevant_events(self, calendar_data: List[Dict]) -> List[Dict]:
        """Filter calendar events for relevance to current trading pairs."""
        if not calendar_data:
            return []
        
        relevant_events = []
        
        for event in calendar_data:
            # Check if event is relevant based on currency
            event_currency = event.get('currency', '').upper()
            event_name = event.get('event', '').upper()
            
            # Check currency relevance
            currency_relevant = event_currency in self._relevant_currencies
            
            # Check event type relevance
            event_relevant = any(event_type in event_name for event_type in self._relevant_events)
            
            # Check impact level
            impact = event.get('impact', 0)
            impact_relevant = impact >= 2  # Medium impact or higher
            
            if currency_relevant or event_relevant or impact_relevant:
                relevant_events.append(event)
        
        return relevant_events
    
    async def _load_relevant_news_data(self):
        """Load only relevant news data with smart caching."""
        print("📰 [DEBUG] Loading relevant news data...")
        
        try:
            now = datetime.now(timezone.utc)
            cache_key = f"news_{now.strftime('%Y-%m-%d_%H')}"
            
            # Check if we have recent cached news data
            if (cache_key in self._news_cache and 
                self._news_cache[cache_key].get('timestamp') and
                now - self._news_cache[cache_key]['timestamp'] < timedelta(hours=1)):
                
                print("✅ [DEBUG] Using cached news data")
                return
            
            # Scrape only relevant news
            print("📰 [DEBUG] Scraping relevant news data...")
            relevant_news = await self._scrape_relevant_news()
            
            if relevant_news:
                self._news_cache[cache_key] = {
                    'data': relevant_news,
                    'timestamp': now
                }
                
                print(f"📊 [DEBUG] Scraped {len(relevant_news)} relevant news items")
            else:
                print("⚠️ [DEBUG] No relevant news data retrieved")
                
        except Exception as e:
            print(f"❌ [DEBUG] Error loading relevant news data: {e}")
            self.logger.error(f"Error loading relevant news data: {e}")
    
    async def _scrape_relevant_news(self) -> List[Dict]:
        """Scrape only news relevant to current trading pairs."""
        relevant_news = []
        
        try:
            # Disable SSL warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Scrape from multiple sources with relevance filtering
            sources = [
                ('bloomberg', bloomberg_com),
                ('dailyfx', dailyfx_com)
            ]
            
            for source_name, scraper_func in sources:
                try:
                    print(f"📰 [DEBUG] Scraping from {source_name}...")
                    news_data = scraper_func()
                    
                    if news_data:
                        # Filter for relevant news
                        filtered_news = self._filter_relevant_news(news_data)
                        relevant_news.extend(filtered_news)
                        
                        print(f"📊 [DEBUG] {source_name}: {len(news_data)} total, {len(filtered_news)} relevant")
                    
                except Exception as e:
                    print(f"⚠️ [DEBUG] Error scraping {source_name}: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ [DEBUG] Error in news scraping: {e}")
        
        return relevant_news
    
    def _filter_relevant_news(self, news_data: List[Dict]) -> List[Dict]:
        """Filter news for relevance to current trading pairs."""
        if not news_data:
            return []
        
        relevant_news = []
        
        for news_item in news_data:
            title = news_item.get('title', '').upper()
            content = news_item.get('content', '').upper()
            
            # Check if news mentions relevant currencies
            currency_relevant = any(currency in title or currency in content 
                                  for currency in self._relevant_currencies)
            
            # Check if news mentions relevant events
            event_relevant = any(event in title or event in content 
                               for event in self._relevant_events)
            
            # Check if news mentions trading pairs
            pair_relevant = any(pair in title or pair in content 
                              for pair in self.config.trading_pairs)
            
            if currency_relevant or event_relevant or pair_relevant:
                relevant_news.append(news_item)
        
        return relevant_news
    
    async def analyze_fundamentals_for_trading(self, pair: str, market_context: MarketContext) -> Dict[str, Any]:
        """Analyze fundamentals for a specific trading pair with smart caching."""
        try:
            print(f"🔍 [DEBUG] Analyzing fundamentals for {pair}...")
            
            # Get current session
            current_session = self._get_current_session()
            
            # Get relevant calendar events for this pair
            calendar_events = await self._get_relevant_calendar_events(pair)
            
            # Get relevant news sentiment for this pair
            news_sentiment = await self._get_relevant_news_sentiment(pair)
            
            # Calculate fundamental score
            fundamental_score = self._calculate_fundamental_score(
                pair, calendar_events, news_sentiment, current_session, market_context
            )
            
            # Determine if we should avoid trading
            avoid_trading = self._should_avoid_trading(pair, calendar_events, current_session)
            
            # Calculate position size multiplier based on fundamentals
            position_multiplier = self._calculate_position_multiplier(
                fundamental_score, calendar_events, current_session
            )
            
            # Get session volatility
            session_volatility = self._get_session_volatility(current_session)
            
            # Correlation analysis
            correlation_analysis = self._analyze_correlations(pair)
            
            result = {
                'fundamental_score': fundamental_score,
                'current_session': current_session,
                'calendar_events': calendar_events,
                'news_sentiment': news_sentiment,
                'avoid_trading': avoid_trading,
                'session_volatility': session_volatility,
                'correlation_analysis': correlation_analysis,
                'position_size_multiplier': position_multiplier,
                'analysis_timestamp': datetime.now(timezone.utc)
            }
            
            print(f"📊 [DEBUG] {pair} fundamental analysis complete: score={fundamental_score:.3f}, avoid={avoid_trading}")
            
            return result
            
        except Exception as e:
            print(f"❌ [DEBUG] Error in fundamental analysis for {pair}: {e}")
            self.logger.error(f"Error in fundamental analysis for {pair}: {e}")
            
            # Return safe defaults
            return {
                'fundamental_score': 0.5,
                'current_session': 'unknown',
                'calendar_events': [],
                'news_sentiment': 0.5,
                'avoid_trading': False,
                'session_volatility': 1.0,
                'correlation_analysis': {},
                'position_size_multiplier': 1.0,
                'analysis_timestamp': datetime.now(timezone.utc)
            }
    
    async def _get_relevant_calendar_events(self, pair: str) -> List[Dict]:
        """Get calendar events relevant to a specific pair."""
        base_currency, quote_currency = pair.split('_')
        
        # Get cached calendar data
        now = datetime.now(timezone.utc)
        cache_key = f"calendar_{now.strftime('%Y-%m-%d')}"
        
        if cache_key in self._calendar_cache:
            calendar_data = self._calendar_cache[cache_key]['data']
            
            # Filter for events affecting this pair
            relevant_events = []
            for event in calendar_data:
                event_currency = event.get('currency', '').upper()
                
                # Check if event affects either currency in the pair
                if event_currency in [base_currency, quote_currency]:
                    # Check if event is within next 24 hours
                    event_time = event.get('time')
                    if event_time:
                        try:
                            event_datetime = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                            if event_datetime > now and event_datetime < now + timedelta(hours=24):
                                relevant_events.append(event)
                        except:
                            pass
            
            return relevant_events
        
        return []
    
    async def _get_relevant_news_sentiment(self, pair: str) -> float:
        """Get news sentiment relevant to a specific pair."""
        base_currency, quote_currency = pair.split('_')
        
        # Get cached news data
        now = datetime.now(timezone.utc)
        cache_key = f"news_{now.strftime('%Y-%m-%d_%H')}"
        
        if cache_key in self._news_cache:
            news_data = self._news_cache[cache_key]['data']
            
            # Calculate sentiment for this pair
            positive_keywords = ['bullish', 'strong', 'positive', 'growth', 'rise', 'gain']
            negative_keywords = ['bearish', 'weak', 'negative', 'decline', 'fall', 'drop']
            
            positive_count = 0
            negative_count = 0
            
            for news_item in news_data:
                title = news_item.get('title', '').lower()
                content = news_item.get('content', '').lower()
                
                # Check if news mentions either currency in the pair
                if base_currency.lower() in title or base_currency.lower() in content:
                    if any(keyword in title or keyword in content for keyword in positive_keywords):
                        positive_count += 1
                    elif any(keyword in title or keyword in content for keyword in negative_keywords):
                        negative_count += 1
                
                if quote_currency.lower() in title or quote_currency.lower() in content:
                    if any(keyword in title or keyword in content for keyword in positive_keywords):
                        positive_count += 1
                    elif any(keyword in title or keyword in content for keyword in negative_keywords):
                        negative_count += 1
            
            # Calculate sentiment score
            total_mentions = positive_count + negative_count
            if total_mentions > 0:
                sentiment = positive_count / total_mentions
            else:
                sentiment = 0.5  # Neutral
            
            return sentiment
        
        return 0.5  # Neutral if no news data
    
    def _calculate_fundamental_score(self, pair: str, calendar_events: List[Dict], 
                                   news_sentiment: float, current_session: str, 
                                   market_context: MarketContext) -> float:
        """Calculate comprehensive fundamental score."""
        score = 0.5  # Base neutral score
        
        # Calendar events impact (40% weight)
        if calendar_events:
            event_score = self._calculate_event_score(calendar_events)
            score += event_score * 0.4
        
        # News sentiment impact (30% weight)
        score += news_sentiment * 0.3
        
        # Session volatility impact (20% weight)
        session_score = self._get_session_score(current_session)
        score += session_score * 0.2
        
        # Market condition impact (10% weight)
        condition_score = self._get_market_condition_score(market_context.condition)
        score += condition_score * 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_event_score(self, events: List[Dict]) -> float:
        """Calculate score based on calendar events."""
        if not events:
            return 0.5
        
        total_impact = 0
        total_weight = 0
        
        for event in events:
            impact = event.get('impact', 1)
            forecast = event.get('forecast', 0)
            previous = event.get('previous', 0)
            
            # Calculate event sentiment
            if forecast > previous:
                sentiment = 0.7  # Positive
            elif forecast < previous:
                sentiment = 0.3  # Negative
            else:
                sentiment = 0.5  # Neutral
            
            weight = impact / 10.0  # Normalize impact
            total_impact += sentiment * weight
            total_weight += weight
        
        if total_weight > 0:
            return total_impact / total_weight
        
        return 0.5
    
    def _should_avoid_trading(self, pair: str, calendar_events: List[Dict], current_session: str) -> bool:
        """Determine if trading should be avoided."""
        # Check for high-impact events within next 2 hours
        now = datetime.now(timezone.utc)
        
        for event in calendar_events:
            event_time = event.get('time')
            if event_time:
                try:
                    event_datetime = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                    time_until_event = event_datetime - now
                    
                    # Avoid trading 2 hours before and 1 hour after high-impact events
                    if (time_until_event.total_seconds() > -3600 and  # Within 1 hour after
                        time_until_event.total_seconds() < 7200 and   # Within 2 hours before
                        event.get('impact', 0) >= 8):                # High impact
                        return True
                except:
                    pass
        
        # Avoid trading during low-liquidity sessions
        if current_session == 'tokyo' and datetime.now(timezone.utc).hour < 2:
            return True
        
        return False
    
    def _calculate_position_multiplier(self, fundamental_score: float, 
                                     calendar_events: List[Dict], current_session: str) -> float:
        """Calculate position size multiplier based on fundamentals."""
        multiplier = 1.0
        
        # Adjust based on fundamental score
        if fundamental_score > 0.7:
            multiplier *= 1.2  # Increase position size for strong fundamentals
        elif fundamental_score < 0.3:
            multiplier *= 0.8  # Decrease position size for weak fundamentals
        
        # Adjust based on upcoming events
        if calendar_events:
            high_impact_count = sum(1 for event in calendar_events if event.get('impact', 0) >= 8)
            if high_impact_count > 0:
                multiplier *= 0.9  # Reduce position size before high-impact events
        
        # Adjust based on session
        if current_session == 'london':
            multiplier *= 1.1  # Slightly increase during London session
        elif current_session == 'tokyo':
            multiplier *= 0.9  # Slightly decrease during Tokyo session
        
        return max(0.5, min(2.0, multiplier))  # Limit between 0.5 and 2.0
    
    def _get_current_session(self) -> str:
        """Get current market session."""
        current_hour = datetime.now(timezone.utc).hour
        
        if self.sessions['tokyo']['start'] <= current_hour < self.sessions['tokyo']['end']:
            return 'tokyo'
        elif self.sessions['london']['start'] <= current_hour < self.sessions['london']['end']:
            return 'london'
        elif self.sessions['new_york']['start'] <= current_hour < self.sessions['new_york']['end']:
            return 'new_york'
        else:
            return 'unknown'
    
    def _get_session_volatility(self, session: str) -> float:
        """Get typical volatility for current session."""
        session_volatility = {
            'tokyo': 0.8,      # Lower volatility
            'london': 1.2,     # Higher volatility
            'new_york': 1.0,   # Medium volatility
            'unknown': 1.0     # Default
        }
        return session_volatility.get(session, 1.0)
    
    def _get_session_score(self, session: str) -> float:
        """Get session quality score."""
        session_scores = {
            'london': 0.8,     # Best session
            'new_york': 0.7,   # Good session
            'tokyo': 0.6,      # Lower quality
            'unknown': 0.5     # Unknown
        }
        return session_scores.get(session, 0.5)
    
    def _get_market_condition_score(self, condition: MarketCondition) -> float:
        """Get score based on market condition."""
        condition_scores = {
            MarketCondition.RANGING: 0.7,           # Good for range trading
            MarketCondition.BREAKOUT: 0.6,          # Moderate
            MarketCondition.REVERSAL: 0.5,          # Neutral
            MarketCondition.NEWS_REACTIONARY: 0.3,  # Poor for systematic trading
            MarketCondition.UNKNOWN: 0.5            # Unknown
        }
        return condition_scores.get(condition, 0.5)
    
    def _analyze_correlations(self, pair: str) -> Dict[str, Any]:
        """Analyze currency correlations for the pair."""
        correlations = {}
        
        # Find which correlation group this pair belongs to
        for group_name, pairs in self.correlations.items():
            if pair in pairs:
                # Get other pairs in the same group
                related_pairs = [p for p in pairs if p != pair]
                correlations['related_pairs'] = related_pairs
                correlations['group'] = group_name
                break
        
        return correlations
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        return {
            'calendar_cache_size': len(self._calendar_cache),
            'news_cache_size': len(self._news_cache),
            'sentiment_cache_size': len(self._sentiment_cache),
            'relevant_currencies': list(self._relevant_currencies),
            'relevant_events': list(self._relevant_events),
            'last_update': self._last_update,
            'last_relevance_check': self._last_relevance_check,
            'cache_directory': str(self._cache_dir)
        }
