"""
Fundamental Analysis Integration Layer - Economic calendar, news sentiment, and market session awareness.
Uses existing scraping components and database infrastructure.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import pytz

from scraping.fx_calendar import get_fx_calendar
from scraping.bloomberg_com import bloomberg_com
from scraping.dailyfx_com import dailyfx_com
from db.db import DataDB
from src.core.models import MarketContext, MarketCondition
from src.utils.config import Config
from src.utils.logger import get_logger


class FundamentalAnalyzer:
    """Fundamental analysis integration using existing scraping components."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize database connection with error handling
        try:
            self.db = DataDB()
            self.db_available = True
            self.logger.info("Database connection established")
        except Exception as e:
            self.logger.warning(f"Database connection failed: {e}. Running without database.")
            self.db = None
            self.db_available = False
        
        # Market session times (UTC)
        self.sessions = {
            'tokyo': {'start': 0, 'end': 9},      # 00:00-09:00 UTC
            'london': {'start': 8, 'end': 17},    # 08:00-17:00 UTC
            'new_york': {'start': 13, 'end': 22}  # 13:00-22:00 UTC
        }
        
        # High-impact events to avoid trading around
        self.high_impact_events = [
            'NFP', 'CPI', 'PPI', 'GDP', 'FOMC', 'ECB', 'BOE', 'BOJ',
            'Federal Reserve', 'European Central Bank', 'Bank of England',
            'Non-Farm Payrolls', 'Consumer Price Index', 'Gross Domestic Product'
        ]
        
        # Currency correlations (simplified)
        self.correlations = {
            'USD_PAIRS': ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CAD', 'AUD_USD', 'NZD_USD'],
            'JPY_PAIRS': ['USD_JPY', 'EUR_JPY', 'GBP_JPY', 'AUD_JPY'],
            'EUR_PAIRS': ['EUR_USD', 'EUR_JPY', 'EUR_GBP'],
            'GBP_PAIRS': ['GBP_USD', 'GBP_JPY', 'EUR_GBP'],
            'COMMODITY_PAIRS': ['AUD_USD', 'NZD_USD', 'USD_CAD']
        }
        
        # Cache for performance
        self._calendar_cache = {}
        self._news_cache = {}
        self._sentiment_cache = {}
        self._last_update = None
        self._cache_duration = timedelta(minutes=15)
    
    async def start(self) -> None:
        """Start fundamental analysis system."""
        self.logger.info("Starting fundamental analyzer...")
        await self._load_calendar_data()
        await self._load_news_data()
        self.logger.info("Fundamental analyzer started successfully")
    
    async def stop(self) -> None:
        """Stop fundamental analysis system."""
        self.logger.info("Stopping fundamental analyzer...")
        self.logger.info("Fundamental analyzer stopped")
    
    async def analyze_fundamentals(self, pair: str, market_context: MarketContext) -> Dict[str, Any]:
        """Comprehensive fundamental analysis for a pair."""
        try:
            # Get current market session
            current_session = self._get_current_session()
            session_overlap = self._get_session_overlap()
            
            # Get economic calendar events
            calendar_events = await self._get_relevant_events(pair)
            high_impact_events = self._filter_high_impact_events(calendar_events)
            
            # Get news sentiment
            news_sentiment = await self._get_news_sentiment(pair)
            
            # Get correlation analysis
            correlation_analysis = self._analyze_correlations(pair)
            
            # Calculate fundamental score
            fundamental_score = self._calculate_fundamental_score(
                pair, calendar_events, news_sentiment, current_session, session_overlap
            )
            
            # Determine if we should avoid trading
            avoid_trading = self._should_avoid_trading(
                pair, high_impact_events, news_sentiment, current_session
            )
            
            return {
                'fundamental_score': fundamental_score,
                'avoid_trading': avoid_trading,
                'current_session': current_session,
                'session_overlap': session_overlap,
                'calendar_events': calendar_events,
                'high_impact_events': high_impact_events,
                'news_sentiment': news_sentiment,
                'correlation_analysis': correlation_analysis,
                'position_size_multiplier': self._calculate_position_multiplier(
                    fundamental_score, avoid_trading, high_impact_events
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error in fundamental analysis for {pair}: {e}")
            return {
                'fundamental_score': 0.5,
                'avoid_trading': False,
                'position_size_multiplier': 1.0
            }
    
    async def _load_calendar_data(self) -> None:
        """Load economic calendar data from database or scrape if needed."""
        try:
            if self.db_available and self.db:
                # Try to get from database first
                calendar_data = self.db.query_all(DataDB.CALENDAR_COLL)
                
                if not calendar_data:
                    # Scrape fresh data using existing function
                    from_date = datetime.now(timezone.utc) - timedelta(days=1)
                    calendar_data = get_fx_calendar(from_date)
                    
                    # Store in database
                    if calendar_data:
                        self.db.add_many(DataDB.CALENDAR_COLL, calendar_data)
            else:
                # Database not available, scrape fresh data
                from_date = datetime.now(timezone.utc) - timedelta(days=1)
                calendar_data = get_fx_calendar(from_date)
            
            self._calendar_cache = calendar_data or []
            self.logger.info(f"Loaded {len(self._calendar_cache)} calendar events")
            
        except Exception as e:
            self.logger.error(f"Error loading calendar data: {e}")
            self._calendar_cache = []
    
    async def _load_news_data(self) -> None:
        """Load news sentiment data using existing scrapers."""
        try:
            # Use existing scraping functions
            bloomberg_news = bloomberg_com()
            dailyfx_sentiment = dailyfx_com()
            
            self._news_cache = {
                'bloomberg': bloomberg_news,
                'dailyfx': dailyfx_sentiment,
                'timestamp': datetime.now(timezone.utc)
            }
            
            self.logger.info(f"Loaded news data: {len(bloomberg_news)} Bloomberg headlines")
            
        except Exception as e:
            self.logger.error(f"Error loading news data: {e}")
            self._news_cache = {'bloomberg': [], 'dailyfx': [], 'timestamp': datetime.now(timezone.utc)}
    
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
            return 'after_hours'
    
    def _get_session_overlap(self) -> List[str]:
        """Get current session overlaps."""
        current_hour = datetime.now(timezone.utc).hour
        overlaps = []
        
        # Check for session overlaps
        if (self.sessions['tokyo']['start'] <= current_hour < self.sessions['tokyo']['end'] and
            self.sessions['london']['start'] <= current_hour < self.sessions['london']['end']):
            overlaps.append('tokyo_london')
        
        if (self.sessions['london']['start'] <= current_hour < self.sessions['london']['end'] and
            self.sessions['new_york']['start'] <= current_hour < self.sessions['new_york']['end']):
            overlaps.append('london_newyork')
        
        return overlaps
    
    async def _get_relevant_events(self, pair: str) -> List[Dict[str, Any]]:
        """Get economic calendar events relevant to the pair."""
        if not self._calendar_cache:
            await self._load_calendar_data()
        
        # Extract currency codes from pair
        base_currency = pair.split('_')[0]
        quote_currency = pair.split('_')[1]
        
        relevant_events = []
        current_time = datetime.now(timezone.utc)
        
        for event in self._calendar_cache:
            # Check if event is within next 24 hours
            event_time = event.get('date')
            if not event_time:
                continue
            
            if isinstance(event_time, str):
                try:
                    event_time = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                except:
                    continue
            
            time_diff = event_time - current_time
            if timedelta(hours=-2) <= time_diff <= timedelta(hours=24):
                # Check if event affects the currencies in our pair
                symbol = event.get('symbol', '').upper()
                country = event.get('country', '').lower()
                
                if (base_currency in symbol or quote_currency in symbol or
                    self._country_affects_currency(country, base_currency, quote_currency)):
                    relevant_events.append(event)
        
        return relevant_events
    
    def _country_affects_currency(self, country: str, base_currency: str, quote_currency: str) -> bool:
        """Check if a country's events affect the currencies in our pair."""
        country_currency_map = {
            'united states': 'USD',
            'euro area': 'EUR',
            'united kingdom': 'GBP',
            'japan': 'JPY',
            'australia': 'AUD',
            'new zealand': 'NZD',
            'canada': 'CAD',
            'switzerland': 'CHF'
        }
        
        affected_currency = country_currency_map.get(country)
        return affected_currency in [base_currency, quote_currency]
    
    def _filter_high_impact_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter for high-impact events."""
        high_impact = []
        
        for event in events:
            event_name = event.get('event', '').upper()
            category = event.get('category', '').upper()
            
            # Check if event is high impact
            for impact_event in self.high_impact_events:
                if impact_event.upper() in event_name or impact_event.upper() in category:
                    high_impact.append(event)
                    break
        
        return high_impact
    
    async def _get_news_sentiment(self, pair: str) -> Dict[str, Any]:
        """Get news sentiment for the pair."""
        if not self._news_cache:
            await self._load_news_data()
        
        # Extract currency codes
        base_currency = pair.split('_')[0]
        quote_currency = pair.split('_')[1]
        
        sentiment_data = {
            'overall_sentiment': 0.0,
            'bloomberg_sentiment': 0.0,
            'dailyfx_sentiment': 0.0,
            'relevant_headlines': [],
            'sentiment_score': 0.0
        }
        
        # Analyze Bloomberg headlines
        bloomberg_headlines = self._news_cache.get('bloomberg', [])
        relevant_bloomberg = []
        
        for headline in bloomberg_headlines:
            if isinstance(headline, dict):
                title = headline.get('title', '').upper()
                if base_currency in title or quote_currency in title:
                    relevant_bloomberg.append(headline)
                    # Simple sentiment analysis based on keywords
                    sentiment = self._analyze_headline_sentiment(title)
                    sentiment_data['bloomberg_sentiment'] += sentiment
        
        # Analyze DailyFX sentiment
        dailyfx_data = self._news_cache.get('dailyfx', [])
        if dailyfx_data:
            sentiment_data['dailyfx_sentiment'] = dailyfx_data.get('sentiment', 0.0)
        
        # Calculate overall sentiment
        if relevant_bloomberg:
            sentiment_data['bloomberg_sentiment'] /= len(relevant_bloomberg)
        
        sentiment_data['overall_sentiment'] = (
            sentiment_data['bloomberg_sentiment'] + sentiment_data['dailyfx_sentiment']
        ) / 2
        
        sentiment_data['relevant_headlines'] = relevant_bloomberg
        sentiment_data['sentiment_score'] = sentiment_data['overall_sentiment']
        
        return sentiment_data
    
    def _analyze_headline_sentiment(self, headline: str) -> float:
        """Simple sentiment analysis based on keywords."""
        positive_words = ['BULLISH', 'GAIN', 'RISE', 'UP', 'STRONG', 'POSITIVE', 'BUY']
        negative_words = ['BEARISH', 'DROP', 'FALL', 'DOWN', 'WEAK', 'NEGATIVE', 'SELL']
        
        headline_upper = headline.upper()
        
        positive_count = sum(1 for word in positive_words if word in headline_upper)
        negative_count = sum(1 for word in negative_words if word in headline_upper)
        
        if positive_count == 0 and negative_count == 0:
            return 0.0
        elif positive_count > negative_count:
            return 0.3
        elif negative_count > positive_count:
            return -0.3
        else:
            return 0.0
    
    def _analyze_correlations(self, pair: str) -> Dict[str, Any]:
        """Analyze currency correlations."""
        correlation_data = {
            'correlated_pairs': [],
            'correlation_strength': 0.0,
            'portfolio_heat': 0.0,
            'risk_warning': False
        }
        
        # Find which correlation group this pair belongs to
        for group_name, pairs in self.correlations.items():
            if pair in pairs:
                correlation_data['correlated_pairs'] = [p for p in pairs if p != pair]
                correlation_data['correlation_strength'] = 0.7  # Simplified
                break
        
        return correlation_data
    
    def _calculate_fundamental_score(self, pair: str, calendar_events: List[Dict[str, Any]], 
                                   news_sentiment: Dict[str, Any], current_session: str, 
                                   session_overlap: List[str]) -> float:
        """Calculate overall fundamental score (0-1)."""
        score = 0.5  # Neutral starting point
        
        # Session analysis
        if current_session == 'london':
            score += 0.1  # London session is most liquid
        elif current_session == 'new_york':
            score += 0.05  # NY session is also good
        elif current_session == 'tokyo':
            score += 0.02  # Tokyo session is less liquid
        
        # Session overlap bonus
        if session_overlap:
            score += 0.05 * len(session_overlap)
        
        # Calendar events impact
        if calendar_events:
            # More events = more volatility = higher score for active trading
            score += min(0.1, len(calendar_events) * 0.01)
        
        # News sentiment impact
        sentiment_score = news_sentiment.get('sentiment_score', 0.0)
        score += sentiment_score * 0.1
        
        # Normalize to 0-1 range
        return max(0.0, min(1.0, score))
    
    def _should_avoid_trading(self, pair: str, high_impact_events: List[Dict[str, Any]], 
                            news_sentiment: Dict[str, Any], current_session: str) -> bool:
        """Determine if we should avoid trading due to fundamental factors."""
        current_time = datetime.now(timezone.utc)
        
        # Check for high-impact events within 30 minutes
        for event in high_impact_events:
            event_time = event.get('date')
            if event_time:
                if isinstance(event_time, str):
                    try:
                        event_time = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                    except:
                        continue
                
                time_diff = abs((event_time - current_time).total_seconds() / 60)
                if time_diff <= 30:  # 30 minutes before/after
                    return True
        
        # Check for extreme news sentiment
        sentiment_score = abs(news_sentiment.get('sentiment_score', 0.0))
        if sentiment_score > 0.8:  # Very strong sentiment
            return True
        
        # Check for after-hours trading
        if current_session == 'after_hours':
            return True
        
        return False
    
    def _calculate_position_multiplier(self, fundamental_score: float, avoid_trading: bool, 
                                     high_impact_events: List[Dict[str, Any]]) -> float:
        """Calculate position size multiplier based on fundamental factors."""
        if avoid_trading:
            return 0.0  # Don't trade
        
        # Base multiplier
        multiplier = 1.0
        
        # Reduce size near high-impact events
        if high_impact_events:
            multiplier *= 0.5
        
        # Adjust based on fundamental score
        if fundamental_score > 0.7:
            multiplier *= 1.2  # Increase size for good conditions
        elif fundamental_score < 0.3:
            multiplier *= 0.7  # Reduce size for poor conditions
        
        return max(0.0, min(2.0, multiplier))  # Cap between 0 and 2
    
    async def get_market_session_info(self) -> Dict[str, Any]:
        """Get current market session information."""
        current_session = self._get_current_session()
        session_overlap = self._get_session_overlap()
        
        return {
            'current_session': current_session,
            'session_overlap': session_overlap,
            'session_quality': 'high' if session_overlap else 'medium',
            'liquidity_level': 'high' if current_session in ['london', 'new_york'] else 'medium'
        }
    
    async def get_fundamental_summary(self) -> Dict[str, Any]:
        """Get summary of fundamental analysis."""
        return {
            'calendar_events_count': len(self._calendar_cache),
            'news_sentiment': self._sentiment_cache,
            'current_session': self._get_current_session(),
            'session_overlap': self._get_session_overlap(),
            'last_update': self._last_update
        } 