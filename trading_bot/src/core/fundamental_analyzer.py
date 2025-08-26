"""
Fundamental Analysis Integration Layer - Economic calendar, news sentiment, and market session awareness.
Uses existing scraping components and database infrastructure.
"""
import asyncio
import logging
import urllib3
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import pytz

import sys
from pathlib import Path

# Add the project root to the path to import API modules
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.append(str(root_dir))

from scraping.fx_calendar import get_fx_calendar
from scraping.bloomberg_com import bloomberg_com
from db.db import DataDB
from ..core.models import MarketContext, MarketCondition
from ..utils.config import Config
from ..utils.logger import get_logger


class FundamentalAnalyzer:
    """Fundamental analysis integration using existing scraping components."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        print("🔧 [DEBUG] Initializing Fundamental Analyzer...")
        
        # Initialize database connection with error handling and toggle
        self.db = None
        self.db_available = False
        if getattr(self.config, 'enable_db', False):
            print("🗄️ [DEBUG] Database enabled in config, attempting connection...")
            try:
                self.db = DataDB()
                self.db_available = True
                print("✅ [DEBUG] Database connection established successfully")
                self.logger.info("Database connection established")
            except Exception as e:
                print(f"❌ [DEBUG] Database connection failed: {e}")
                self.logger.warning(f"Database connection failed: {e}. Running without database.")
                self.db = None
                self.db_available = False
        else:
            print("⚠️ [DEBUG] Database disabled in config, running without database")
        
        # Market session times (UTC)
        self.sessions = {
            'tokyo': {'start': 0, 'end': 9},      # 00:00-09:00 UTC
            'london': {'start': 8, 'end': 17},    # 08:00-17:00 UTC
            'new_york': {'start': 13, 'end': 22}  # 13:00-22:00 UTC
        }
        print(f"⏰ [DEBUG] Market sessions configured: {self.sessions}")
        
        # High-impact events to avoid trading around
        self.high_impact_events = [
            'NFP', 'CPI', 'PPI', 'GDP', 'FOMC', 'ECB', 'BOE', 'BOJ',
            'Federal Reserve', 'European Central Bank', 'Bank of England',
            'Non-Farm Payrolls', 'Consumer Price Index', 'Gross Domestic Product'
        ]
        print(f"🚨 [DEBUG] High-impact events configured: {len(self.high_impact_events)} events")
        
        # Currency correlations (simplified)
        self.correlations = {
            'USD_PAIRS': ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CAD', 'AUD_USD', 'NZD_USD'],
            'JPY_PAIRS': ['USD_JPY', 'EUR_JPY', 'GBP_JPY', 'AUD_JPY'],
            'EUR_PAIRS': ['EUR_USD', 'EUR_JPY', 'EUR_GBP'],
            'GBP_PAIRS': ['GBP_USD', 'GBP_JPY', 'EUR_GBP'],
            'COMMODITY_PAIRS': ['AUD_USD', 'NZD_USD', 'USD_CAD']
        }
        print(f"🔗 [DEBUG] Currency correlations configured: {len(self.correlations)} groups")
        
        # Cache for performance
        self._calendar_cache = {}
        self._news_cache = {}
        self._sentiment_cache = {}
        self._last_update = None
        self._cache_duration = timedelta(minutes=15)
        print("💾 [DEBUG] Cache system initialized")
        
        print("✅ [DEBUG] Fundamental Analyzer initialization complete")
    
    async def start(self) -> None:
        """Start fundamental analysis system."""
        print("📰 [DEBUG] Starting fundamental analyzer...")
        self.logger.info("Starting fundamental analyzer...")
        
        if getattr(self.config, 'enable_db', False):
            print("📅 [DEBUG] Loading calendar data...")
            await self._load_calendar_data()
            print("✅ [DEBUG] Calendar data loaded")
        else:
            print("⚠️ [DEBUG] Database disabled, skipping calendar data load")
        
        if getattr(self.config, 'enable_news', False):
            print("📰 [DEBUG] Loading news data...")
            await self._load_news_data()
            print("✅ [DEBUG] News data loaded")
        else:
            print("⚠️ [DEBUG] News disabled, skipping news data load")
        
        print("✅ [DEBUG] Fundamental analyzer started successfully")
        self.logger.info("Fundamental analyzer started successfully")
    
    async def stop(self) -> None:
        """Stop fundamental analysis system."""
        print("🛑 [DEBUG] Stopping fundamental analyzer...")
        self.logger.info("Stopping fundamental analyzer...")
        self.logger.info("Fundamental analyzer stopped")
    
    async def analyze_fundamentals(self, pair: str, market_context: MarketContext) -> Dict[str, Any]:
        """Analyze fundamental factors for a trading pair using enhanced multi-source sentiment."""
        print(f"🔍 [DEBUG] Starting enhanced fundamental analysis for {pair}...")
        
        try:
            # Extract base and quote currencies
            base_currency, quote_currency = pair.split('_')
            print(f"💱 [DEBUG] Currency pair: {base_currency}/{quote_currency}")
            
            # Get relevant economic events
            print(f"📅 [DEBUG] Retrieving economic events for {pair}...")
            relevant_events = await self._get_relevant_events(pair)
            print(f"📊 [DEBUG] Found {len(relevant_events)} relevant economic events")
            
            # Get high-impact events
            high_impact_events = self._filter_high_impact_events(relevant_events)
            print(f"🚨 [DEBUG] Found {len(high_impact_events)} high-impact events")
            
            # Get current session info
            current_session = self._get_current_session()
            session_overlap = self._get_session_overlap()
            
            # Get technical data from market context
            technical_data = {
                'rsi': getattr(market_context, 'rsi', 50),
                'macd': getattr(market_context, 'macd', 0),
                'atr': getattr(market_context, 'atr', 0.001)
            }
            
            # Get enhanced multi-source sentiment
            print(f"📰 [DEBUG] Retrieving enhanced sentiment for {pair}...")
            enhanced_sentiment = await self._get_enhanced_sentiment(pair, relevant_events, technical_data)
            print(f"📈 [DEBUG] Enhanced sentiment score: {enhanced_sentiment.get('sentiment_score', 0):.3f}")
            
            # Calculate enhanced fundamental score
            print(f"🧮 [DEBUG] Calculating enhanced fundamental score...")
            fundamental_score = self._calculate_enhanced_fundamental_score(
                pair, relevant_events, enhanced_sentiment, current_session, session_overlap
            )
            print(f"📊 [DEBUG] Enhanced fundamental score: {fundamental_score:.3f}")
            
            # Check if we should avoid trading
            avoid_trading = self._should_avoid_trading(pair, high_impact_events, enhanced_sentiment, current_session)
            print(f"🚫 [DEBUG] Avoid trading: {avoid_trading}")
            
            # Calculate position multiplier
            position_multiplier = self._calculate_position_multiplier(fundamental_score, avoid_trading, high_impact_events)
            print(f"📏 [DEBUG] Position multiplier: {position_multiplier:.3f}")
            
            # Determine fundamental bias
            fundamental_bias = self._determine_enhanced_fundamental_bias(fundamental_score, enhanced_sentiment)
            print(f"🎯 [DEBUG] Enhanced fundamental bias: {fundamental_bias}")
            
            result = {
                'score': fundamental_score,
                'position_multiplier': position_multiplier,
                'avoid_trading': avoid_trading,
                'fundamental_bias': fundamental_bias,
                'economic_events': relevant_events,
                'high_impact_events': high_impact_events,
                'enhanced_sentiment': enhanced_sentiment,
                'current_session': current_session,
                'session_overlap': session_overlap,
                'analysis_timestamp': datetime.now(timezone.utc)
            }
            
            print(f"✅ [DEBUG] Enhanced fundamental analysis complete for {pair}")
            return result
            
        except Exception as e:
            print(f"❌ [DEBUG] Error in enhanced fundamental analysis for {pair}: {e}")
            self.logger.error(f"❌ Error in enhanced fundamental analysis for {pair}: {e}")
            return {
                'score': 0.5,
                'position_multiplier': 1.0,
                'avoid_trading': False,
                'fundamental_bias': 'NEUTRAL',
                'economic_events': [],
                'high_impact_events': [],
                'enhanced_sentiment': {},
                'current_session': 'unknown',
                'session_overlap': [],
                'analysis_timestamp': datetime.now(timezone.utc),
                'error': str(e)
            }
    
    def _calculate_sentiment_score(self, relevant_events: List[Dict[str, Any]], 
                                 news_sentiment: Dict[str, Any]) -> float:
        """Calculate overall sentiment score from events and news."""
        print("🧮 [DEBUG] Calculating sentiment score...")
        
        try:
            # Base sentiment from news
            base_sentiment = news_sentiment.get('sentiment_score', 0.5)
            print(f"📰 [DEBUG] Base news sentiment: {base_sentiment:.3f}")
            
            # Adjust based on economic events
            event_sentiment = 0.5  # Neutral base
            if relevant_events:
                print(f"📅 [DEBUG] Processing {len(relevant_events)} economic events...")
                
                # Simple sentiment calculation based on event count and impact
                high_impact_count = len([e for e in relevant_events if e.get('impact') == 'High'])
                medium_impact_count = len([e for e in relevant_events if e.get('impact') == 'Medium'])
                print(f"🚨 [DEBUG] High impact events: {high_impact_count}, Medium impact: {medium_impact_count}")
                
                # Positive events (like GDP growth, employment) tend to be bullish
                positive_keywords = ['gdp', 'employment', 'growth', 'retail sales', 'manufacturing']
                negative_keywords = ['inflation', 'unemployment', 'deficit', 'recession']
                
                positive_count = 0
                negative_count = 0
                
                for event in relevant_events:
                    event_name = event.get('event', '').lower()
                    if any(keyword in event_name for keyword in positive_keywords):
                        positive_count += 1
                        print(f"✅ [DEBUG] Positive event found: {event_name}")
                    elif any(keyword in event_name for keyword in negative_keywords):
                        negative_count += 1
                        print(f"❌ [DEBUG] Negative event found: {event_name}")
                
                print(f"📊 [DEBUG] Positive events: {positive_count}, Negative events: {negative_count}")
                
                # Calculate event sentiment
                if positive_count > negative_count:
                    event_sentiment = 0.6 + (positive_count - negative_count) * 0.1
                elif negative_count > positive_count:
                    event_sentiment = 0.4 - (negative_count - positive_count) * 0.1
                else:
                    event_sentiment = 0.5
                
                print(f"📈 [DEBUG] Event sentiment: {event_sentiment:.3f}")
            else:
                print("📅 [DEBUG] No relevant economic events found")
            
            # Combine news and event sentiment (weighted average)
            final_sentiment = (base_sentiment * 0.7) + (event_sentiment * 0.3)
            print(f"🎯 [DEBUG] Final sentiment: {final_sentiment:.3f} (70% news + 30% events)")
            
            # Ensure it's between 0 and 1
            final_sentiment = max(0.0, min(1.0, final_sentiment))
            print(f"📊 [DEBUG] Normalized sentiment: {final_sentiment:.3f}")
            
            return final_sentiment
            
        except Exception as e:
            print(f"❌ [DEBUG] Error calculating sentiment score: {e}")
            self.logger.error(f"Error calculating sentiment score: {e}")
            return 0.5  # Neutral on error
    
    def _determine_fundamental_bias(self, sentiment_score: float) -> str:
        """Determine fundamental bias based on sentiment score."""
        if sentiment_score > 0.6:
            bias = 'BULLISH'
        elif sentiment_score < 0.4:
            bias = 'BEARISH'
        else:
            bias = 'NEUTRAL'
        
        print(f"🎯 [DEBUG] Sentiment {sentiment_score:.3f} → Bias: {bias}")
        return bias
    
    async def _load_calendar_data(self) -> None:
        """Load economic calendar data from database or scrape if needed."""
        print("📅 [DEBUG] Loading calendar data...")
        
        try:
            if self.db_available and self.db:
                print("🗄️ [DEBUG] Database available, checking for cached calendar data...")
                # Try to get from database first
                calendar_data = self.db.query_all(DataDB.CALENDAR_COLL)
                
                if not calendar_data:
                    print("📅 [DEBUG] No cached data found, scraping fresh calendar data...")
                    # Scrape fresh data using existing function
                    from_date = datetime.now(timezone.utc) - timedelta(days=1)
                    print(f"📅 [DEBUG] Scraping calendar from {from_date.strftime('%Y-%m-%d')}...")
                    calendar_data = get_fx_calendar(from_date)
                    
                    # Store in database
                    if calendar_data:
                        print(f"💾 [DEBUG] Storing {len(calendar_data)} calendar events in database...")
                        self.db.add_many(DataDB.CALENDAR_COLL, calendar_data)
                        print("✅ [DEBUG] Calendar data stored in database")
                    else:
                        print("⚠️ [DEBUG] No calendar data retrieved from scraping")
                else:
                    print(f"✅ [DEBUG] Found {len(calendar_data)} cached calendar events in database")
            else:
                print("📅 [DEBUG] Database not available, scraping fresh calendar data...")
                # Database not available, scrape fresh data
                from_date = datetime.now(timezone.utc) - timedelta(days=1)
                print(f"📅 [DEBUG] Scraping calendar from {from_date.strftime('%Y-%m-%d')}...")
                calendar_data = get_fx_calendar(from_date)
                print(f"📊 [DEBUG] Retrieved {len(calendar_data) if calendar_data else 0} calendar events")
            
            self._calendar_cache = calendar_data or []
            print(f"📅 [DEBUG] Calendar cache updated: {len(self._calendar_cache)} events")
            self.logger.info(f"Loaded {len(self._calendar_cache)} calendar events")
            
        except Exception as e:
            print(f"❌ [DEBUG] Error loading calendar data: {e}")
            self.logger.error(f"Error loading calendar data: {e}")
            self._calendar_cache = []
    
    async def _load_news_data(self) -> None:
        """Load news sentiment data using existing scrapers."""
        print("📰 [DEBUG] Loading news data...")
        
        try:
            # Disable SSL warnings for web scraping
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            print("🔒 [DEBUG] SSL warnings disabled for web scraping")
            
            # Use existing scraping functions (SSL handling is done in the scraping functions)
            print("📰 [DEBUG] Scraping Bloomberg news...")
            bloomberg_news = bloomberg_com()
            print(f"📰 [DEBUG] Retrieved {len(bloomberg_news) if bloomberg_news is not None else 0} Bloomberg headlines")
            
            self._news_cache = {
                'bloomberg': bloomberg_news,
                'timestamp': datetime.now(timezone.utc)
            }
            
            print(f"📰 [DEBUG] News cache updated with {len(bloomberg_news) if bloomberg_news is not None else 0} Bloomberg headlines")
            self.logger.info(f"Loaded news data: {len(bloomberg_news) if bloomberg_news is not None else 0} Bloomberg headlines")
            
        except Exception as e:
            print(f"❌ [DEBUG] Error loading news data: {e}")
            self.logger.error(f"Error loading news data: {e}")
            self._news_cache = {'bloomberg': [], 'timestamp': datetime.now(timezone.utc)}
    
    def _get_current_session(self) -> str:
        """Get current market session."""
        current_hour = datetime.now(timezone.utc).hour
        print(f"⏰ [DEBUG] Current UTC hour: {current_hour}")
        
        if self.sessions['tokyo']['start'] <= current_hour < self.sessions['tokyo']['end']:
            session = 'tokyo'
        elif self.sessions['london']['start'] <= current_hour < self.sessions['london']['end']:
            session = 'london'
        elif self.sessions['new_york']['start'] <= current_hour < self.sessions['new_york']['end']:
            session = 'new_york'
        else:
            session = 'after_hours'
        
        print(f"🌍 [DEBUG] Current market session: {session}")
        return session
    
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
        
        if overlaps:
            print(f"🌍 [DEBUG] Session overlaps detected: {overlaps}")
        else:
            print("🌍 [DEBUG] No session overlaps detected")
        
        return overlaps
    
    async def _get_relevant_events(self, pair: str) -> List[Dict[str, Any]]:
        """Get economic calendar events relevant to the pair."""
        print(f"📅 [DEBUG] Getting relevant events for {pair}...")
        
        if not self._calendar_cache:
            print("📅 [DEBUG] Calendar cache empty, loading data...")
            await self._load_calendar_data()
        
        # Extract currency codes from pair
        base_currency = pair.split('_')[0]
        quote_currency = pair.split('_')[1]
        print(f"💱 [DEBUG] Looking for events affecting {base_currency} or {quote_currency}")
        
        relevant_events = []
        current_time = datetime.now(timezone.utc)
        print(f"⏰ [DEBUG] Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        for i, event in enumerate(self._calendar_cache):
            # Check if event is within next 24 hours
            event_time = event.get('date')
            if not event_time:
                continue
            
            if isinstance(event_time, str):
                try:
                    event_time = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                except:
                    continue
            
            # Ensure event_time has timezone info
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
            
            time_diff = event_time - current_time
            if timedelta(hours=-2) <= time_diff <= timedelta(hours=24):
                # Check if event affects the currencies in our pair
                symbol = event.get('symbol', '').upper()
                country = event.get('country', '').lower()
                event_name = event.get('event', '').lower()
                category = event.get('category', '').lower()
                
                # Multi-layered relevance check
                is_relevant = False
                relevance_reasons = []
                
                # 1. Symbol-based matching
                if self._symbol_affects_currency(symbol, base_currency, quote_currency):
                    is_relevant = True
                    relevance_reasons.append(f"symbol-{symbol}")
                
                # 2. Country-based matching  
                if self._country_affects_currency(country, base_currency, quote_currency):
                    is_relevant = True
                    relevance_reasons.append(f"country-{country}")
                
                # 3. Event name keyword matching
                if self._event_name_affects_currency(event_name, base_currency, quote_currency):
                    is_relevant = True
                    relevance_reasons.append(f"event-keyword")
                
                # 4. Category-based relevance scoring
                relevance_score = self._calculate_category_relevance_score(category, base_currency, quote_currency)
                if relevance_score > 0.3:  # Threshold for relevance
                    is_relevant = True
                    relevance_reasons.append(f"category-{category}")
                
                if is_relevant:
                    # Add relevance metadata to event
                    event_copy = event.copy()
                    event_copy['relevance_score'] = relevance_score
                    event_copy['relevance_reasons'] = relevance_reasons
                    
                    relevant_events.append(event_copy)
                    print(f"📅 [DEBUG] Relevant event {i+1}: {event.get('event', 'Unknown')} ({country}) - {event_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    print(f"📊 [DEBUG] Relevance reasons: {', '.join(relevance_reasons)} (score: {relevance_score:.2f})")
        
        print(f"📊 [DEBUG] Found {len(relevant_events)} relevant events for {pair}")
        return relevant_events
    
    def _country_affects_currency(self, country: str, base_currency: str, quote_currency: str) -> bool:
        """Check if a country's events affect the currencies in our pair."""
        # Comprehensive country-currency mapping
        country_currency_map = {
            # Major currencies
            'united states': 'USD',
            'usa': 'USD',
            'us': 'USD',
            'america': 'USD',
            'eurozone': 'EUR',
            'euro area': 'EUR',
            'euro zone': 'EUR',
            'european union': 'EUR',
            'eu': 'EUR',
            'germany': 'EUR',
            'france': 'EUR',
            'italy': 'EUR',
            'spain': 'EUR',
            'netherlands': 'EUR',
            'belgium': 'EUR',
            'austria': 'EUR',
            'finland': 'EUR',
            'ireland': 'EUR',
            'portugal': 'EUR',
            'greece': 'EUR',
            'luxembourg': 'EUR',
            'slovenia': 'EUR',
            'slovakia': 'EUR',
            'estonia': 'EUR',
            'latvia': 'EUR',
            'lithuania': 'EUR',
            'malta': 'EUR',
            'cyprus': 'EUR',
            'united kingdom': 'GBP',
            'uk': 'GBP',
            'britain': 'GBP',
            'england': 'GBP',
            'scotland': 'GBP',
            'wales': 'GBP',
            'northern ireland': 'GBP',
            'japan': 'JPY',
            'australia': 'AUD',
            'new zealand': 'NZD',
            'canada': 'CAD',
            'switzerland': 'CHF',
            # Additional major currencies
            'china': 'CNY',
            'hong kong': 'HKD',
            'singapore': 'SGD',
            'south korea': 'KRW',
            'korea': 'KRW',
            'india': 'INR',
            'brazil': 'BRL',
            'mexico': 'MXN',
            'russia': 'RUB',
            'south africa': 'ZAR',
            'norway': 'NOK',
            'sweden': 'SEK',
            'denmark': 'DKK',
            'poland': 'PLN',
            'czech republic': 'CZK',
            'hungary': 'HUF',
            'turkey': 'TRY',
            'israel': 'ILS',
            'thailand': 'THB',
            'malaysia': 'MYR',
            'indonesia': 'IDR',
            'philippines': 'PHP',
            'taiwan': 'TWD',
            'chile': 'CLP',
            'colombia': 'COP',
            'peru': 'PEN',
            'argentina': 'ARS',
            'uruguay': 'UYU',
            'egypt': 'EGP',
            'saudi arabia': 'SAR',
            'uae': 'AED',
            'kuwait': 'KWD',
            'qatar': 'QAR',
            'bahrain': 'BHD',
            'oman': 'OMR'
        }
        
        affected_currency = country_currency_map.get(country.lower())
        affects = affected_currency in [base_currency, quote_currency]
        
        if affects:
            print(f"🌍 [DEBUG] Country {country} affects currency {affected_currency}")
        
        return affects
    
    def _symbol_affects_currency(self, symbol: str, base_currency: str, quote_currency: str) -> bool:
        """Check if an economic symbol affects the currencies in our pair."""
        if not symbol:
            return False
            
        # Comprehensive symbol-currency mapping
        symbol_currency_map = {
            # US indicators
            'GDP CQOQ': 'USD',
            'GDP YQOQ': 'USD', 
            'GDP': 'USD',
            'USPCPIYOY': 'USD',
            'USCPIYOY': 'USD',
            'CPI': 'USD',
            'USRETAILSALESMM': 'USD',
            'USNFP': 'USD',
            'NFP': 'USD',
            'USUNR': 'USD',
            'UNEMPLOYMENT': 'USD',
            'USINDPROYMM': 'USD',
            'USISM': 'USD',
            'USCFNAIMM': 'USD',
            'USJOBOPENINGS': 'USD',
            'USJOBQUITS': 'USD',
            'USPPI': 'USD',
            'USHOUSINGSTARTS': 'USD',
            'USBUILDINGPERMITS': 'USD',
            'USPERSONALINCOMEMM': 'USD',
            'USPERSONALSPENDMM': 'USD',
            'USCONSUMERSENTIMENT': 'USD',
            'USCONSUMERCONFIDENCE': 'USD',
            'USDURABLEGOODS': 'USD',
            'UNITEDSTADURGOOORD': 'USD',
            'FEDRATE': 'USD',
            'FOMC': 'USD',
            
            # Euro area indicators
            'GRGDPYOY': 'EUR',
            'EURGDP': 'EUR',
            'EURCPI': 'EUR',
            'EURRETAILSALES': 'EUR',
            'EURUNEMPLOYMENT': 'EUR',
            'EURISM': 'EUR',
            'EURSENTIX': 'EUR',
            'EURZEW': 'EUR',
            'EURPPI': 'EUR',
            'EURTRADEBALMM': 'EUR',
            'GRIFPBUS': 'EUR',  # Germany IFO Business Climate
            'GRCCI': 'EUR',     # Germany GFK Consumer Confidence
            'GRMANPMI': 'EUR',
            'GRRETAILSALESMM': 'EUR',
            'GRINDPROYMM': 'EUR',
            'EURINTRATE': 'EUR',
            'ECB': 'EUR',
            
            # UK indicators
            'UKGDP': 'GBP',
            'UKCPI': 'GBP',
            'UKRETAILSALES': 'GBP',
            'UKUNEMPLOYMENT': 'GBP',
            'UKMANPMI': 'GBP',
            'UKSERVICESPMI': 'GBP',
            'UKCONSTRUCTIONPMI': 'GBP',
            'UKRIGHTNOW': 'GBP',
            'UKBOE': 'GBP',
            'BOE': 'GBP',
            'UKINTRATE': 'GBP',
            
            # Japan indicators
            'JNGDP': 'JPY',
            'JNCPI': 'JPY',
            'JNRETAILSALES': 'JPY',
            'JNUNEMPLOYMENT': 'JPY',
            'JNMANPMI': 'JPY',
            'JNINDPRO': 'JPY',
            'JNTANKAN': 'JPY',
            'JNMACHINEORDERS': 'JPY',
            'JNHOUSINGSTARTS': 'JPY',
            'BOJ': 'JPY',
            'JNINTRATE': 'JPY',
            
            # Australia indicators
            'AUGDP': 'AUD',
            'AUCPI': 'AUD',
            'AURETAILSALES': 'AUD',
            'AUUNEMPLOYMENT': 'AUD',
            'AUMANPMI': 'AUD',
            'AUSERVICESPMI': 'AUD',
            'AUCOMBANK': 'AUD',
            'AUHOUSECREDIT': 'AUD',
            'AUHPI': 'AUD',
            'RBA': 'AUD',
            'AUINTRATE': 'AUD',
            
            # Canada indicators
            'CAGDP': 'CAD',
            'CACPI': 'CAD',
            'CARETAILSALES': 'CAD',
            'CAUNEMPR': 'CAD',
            'CAMANPMI': 'CAD',
            'CAHOUSINGSTARTS': 'CAD',
            'CAHPI': 'CAD',
            'CABOC': 'CAD',
            'BOC': 'CAD',
            'CAINTRATE': 'CAD',
            
            # Switzerland indicators
            'SZGDP': 'CHF',
            'SZCPI': 'CHF',
            'SZRETAILSALES': 'CHF',
            'SZUNEMPLOYMENT': 'CHF',
            'SZMANPMI': 'CHF',
            'SZNB': 'CHF',
            'SNB': 'CHF',
            'SZINTRATE': 'CHF',
            
            # New Zealand indicators
            'NZGDP': 'NZD',
            'NZCPI': 'NZD',
            'NZRETAILSALES': 'NZD',
            'NZUNEMPLOYMENT': 'NZD',
            'NZMANPMI': 'NZD',
            'NZHPI': 'NZD',
            'RBNZ': 'NZD',
            'NZINTRATE': 'NZD'
        }
        
        # Check exact symbol match
        affected_currency = symbol_currency_map.get(symbol)
        if affected_currency and affected_currency in [base_currency, quote_currency]:
            print(f"📊 [DEBUG] Symbol {symbol} affects currency {affected_currency}")
            return True
        
        # Check partial symbol match (for variations)
        for symbol_key, currency in symbol_currency_map.items():
            if (symbol_key in symbol or symbol in symbol_key) and currency in [base_currency, quote_currency]:
                print(f"📊 [DEBUG] Symbol {symbol} (partial match with {symbol_key}) affects currency {currency}")
                return True
        
        return False
    
    def _event_name_affects_currency(self, event_name: str, base_currency: str, quote_currency: str) -> bool:
        """Check if event name contains keywords that affect the currencies."""
        if not event_name:
            return False
        
        # Currency-specific keywords in event names
        currency_keywords = {
            'USD': [
                'fed', 'federal reserve', 'fomc', 'powell', 'yellen', 'bernanke',
                'nonfarm', 'payrolls', 'unemployment', 'jobless', 'employment',
                'cpi', 'inflation', 'ppi', 'pce', 'gdp', 'retail sales',
                'ism', 'philadelphia fed', 'ny fed', 'chicago fed',
                'durable goods', 'factory orders', 'industrial production',
                'consumer confidence', 'consumer sentiment', 'michigan',
                'existing home sales', 'new home sales', 'housing starts',
                'building permits', 'personal income', 'personal spending',
                'trade balance', 'current account', 'treasury', 'dollar'
            ],
            'EUR': [
                'ecb', 'european central bank', 'draghi', 'lagarde', 'trichet',
                'eurozone', 'euro area', 'german', 'germany', 'france', 'italy',
                'ifo', 'zew', 'pmi', 'sentix', 'euro', 'bundesbank',
                'buba', 'french', 'italian', 'spanish', 'dutch'
            ],
            'GBP': [
                'boe', 'bank of england', 'carney', 'bailey', 'king',
                'uk', 'britain', 'british', 'england', 'pound', 'sterling',
                'brexit', 'ons', 'rightmove', 'nationwide'
            ],
            'JPY': [
                'boj', 'bank of japan', 'kuroda', 'ueda', 'tankan',
                'japan', 'japanese', 'yen', 'nikkei', 'topix'
            ],
            'AUD': [
                'rba', 'reserve bank australia', 'lowe', 'stevens',
                'australia', 'australian', 'aussie', 'aud'
            ],
            'CAD': [
                'boc', 'bank of canada', 'poloz', 'macklem',
                'canada', 'canadian', 'loonie', 'cad'
            ],
            'CHF': [
                'snb', 'swiss national bank', 'jordan', 'hildebrand',
                'switzerland', 'swiss', 'franc', 'chf'
            ],
            'NZD': [
                'rbnz', 'reserve bank new zealand', 'orr', 'wheeler',
                'new zealand', 'kiwi', 'nzd'
            ]
        }
        
        event_lower = event_name.lower()
        
        for currency in [base_currency, quote_currency]:
            if currency in currency_keywords:
                for keyword in currency_keywords[currency]:
                    if keyword in event_lower:
                        print(f"📊 [DEBUG] Event '{event_name}' contains keyword '{keyword}' affecting {currency}")
                        return True
        
        return False
    
    def _calculate_category_relevance_score(self, category: str, base_currency: str, quote_currency: str) -> float:
        """Calculate relevance score based on event category."""
        if not category:
            return 0.0
        
        category_lower = category.lower()
        
        # High-impact categories (most relevant for forex)
        high_impact_categories = {
            'interest rate': 0.9,
            'central bank': 0.9,
            'monetary policy': 0.9,
            'gdp': 0.8,
            'gdp growth rate': 0.8,
            'inflation': 0.8,
            'employment': 0.8,
            'unemployment': 0.7,
            'cpi': 0.8,
            'ppi': 0.7,
            'retail sales': 0.7,
            'consumer confidence': 0.6,
            'business confidence': 0.6,
            'manufacturing': 0.6,
            'pmi': 0.6,
            'trade balance': 0.6,
            'current account': 0.6,
            'government budget': 0.5,
            'housing': 0.5,
            'industrial production': 0.6,
            'consumer price index': 0.8,
            'producer price index': 0.7
        }
        
        # Medium-impact categories
        medium_impact_categories = {
            'consumer spending': 0.5,
            'business investment': 0.5,
            'government spending': 0.4,
            'exports': 0.5,
            'imports': 0.5,
            'wages': 0.5,
            'productivity': 0.4,
            'credit': 0.4,
            'money supply': 0.4,
            'banking': 0.4,
            'stock market': 0.3,
            'commodity prices': 0.4
        }
        
        # Low-impact categories
        low_impact_categories = {
            'weather': 0.1,
            'tourism': 0.2,
            'agriculture': 0.2,
            'energy': 0.3,
            'technology': 0.2,
            'healthcare': 0.1,
            'education': 0.1,
            'sports': 0.0,
            'entertainment': 0.0
        }
        
        # Check for exact category matches
        for category_dict, base_score in [(high_impact_categories, 1.0), 
                                         (medium_impact_categories, 0.6), 
                                         (low_impact_categories, 0.3)]:
            for cat_key, score in category_dict.items():
                if cat_key in category_lower:
                    print(f"📊 [DEBUG] Category '{category}' matched '{cat_key}' with score {score:.2f}")
                    return score * base_score
        
        # Default score for unknown categories
        return 0.2
    
    def _filter_high_impact_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter for high-impact events."""
        print("🚨 [DEBUG] Filtering for high-impact events...")
        
        high_impact = []
        
        for event in events:
            event_name = event.get('event', '').upper()
            category = event.get('category', '').upper()
            
            # Check if event is high impact
            for impact_event in self.high_impact_events:
                if impact_event.upper() in event_name or impact_event.upper() in category:
                    high_impact.append(event)
                    print(f"🚨 [DEBUG] High-impact event found: {event_name}")
                    break
        
        print(f"🚨 [DEBUG] Found {len(high_impact)} high-impact events")
        return high_impact
    
    async def _get_enhanced_sentiment(self, pair: str, calendar_events: List[Dict[str, Any]], 
                                    technical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get enhanced multi-source sentiment analysis for the pair."""
        print(f"📰 [DEBUG] Getting enhanced sentiment for {pair}...")
        
        if not self._news_cache:
            print("📰 [DEBUG] News cache empty, loading data...")
            await self._load_news_data()
        
        # Extract currency codes
        base_currency = pair.split('_')[0]
        quote_currency = pair.split('_')[1]
        print(f"💱 [DEBUG] Looking for news about {base_currency} or {quote_currency}")
        
        # Get current session info
        current_session = self._get_current_session()
        session_overlap = self._get_session_overlap()
        
        sentiment_data = {
            'overall_sentiment': 0.0,
            'bloomberg_sentiment': 0.0,
            'calendar_sentiment': 0.0,
            'session_sentiment': 0.0,
            'technical_sentiment': 0.0,
            'relevant_headlines': [],
            'sentiment_score': 0.0,
            'sentiment_breakdown': {}
        }
        
        # 1. Bloomberg/Reuters Analysis (40% weight)
        print("📰 [DEBUG] === BLOOMBERG SENTIMENT ANALYSIS ===")
        bloomberg_headlines = self._news_cache.get('bloomberg', [])
        print(f"📰 [DEBUG] Analyzing {len(bloomberg_headlines) if bloomberg_headlines else 0} Bloomberg headlines")
        relevant_bloomberg = []
        
        if bloomberg_headlines:
            for i, headline in enumerate(bloomberg_headlines):
                if isinstance(headline, dict):
                    title = headline.get('headline', '').upper()  # Use 'headline' key
                    if base_currency in title or quote_currency in title:
                        relevant_bloomberg.append(headline)
                        # Enhanced sentiment analysis based on keywords
                        sentiment = self._analyze_headline_sentiment(title)
                        sentiment_data['bloomberg_sentiment'] += sentiment
                        print(f"📰 [DEBUG] Relevant Bloomberg headline {i+1}: {title[:50]}... (sentiment: {sentiment:.3f})")
        
        # Calculate average Bloomberg sentiment
        if relevant_bloomberg:
            sentiment_data['bloomberg_sentiment'] /= len(relevant_bloomberg)
            print(f"📰 [DEBUG] Average Bloomberg sentiment: {sentiment_data['bloomberg_sentiment']:.3f}")
        
        # 2. Economic Calendar Sentiment (30% weight)
        print("📊 [DEBUG] === CALENDAR SENTIMENT ANALYSIS ===")
        sentiment_data['calendar_sentiment'] = self._analyze_calendar_sentiment(calendar_events)
        
        # 3. Market Session Sentiment (20% weight)
        print("🌍 [DEBUG] === SESSION SENTIMENT ANALYSIS ===")
        sentiment_data['session_sentiment'] = self._analyze_session_sentiment(current_session, session_overlap)
        
        # 4. Technical Sentiment (10% weight)
        print("📈 [DEBUG] === TECHNICAL SENTIMENT ANALYSIS ===")
        sentiment_data['technical_sentiment'] = self._analyze_technical_sentiment(technical_data)
        
        # Calculate weighted overall sentiment
        sentiment_data['overall_sentiment'] = (
            sentiment_data['bloomberg_sentiment'] * 0.4 +
            sentiment_data['calendar_sentiment'] * 0.3 +
            sentiment_data['session_sentiment'] * 0.2 +
            sentiment_data['technical_sentiment'] * 0.1
        )
        
        sentiment_data['relevant_headlines'] = relevant_bloomberg
        sentiment_data['sentiment_score'] = sentiment_data['overall_sentiment']
        
        # Create sentiment breakdown for transparency
        sentiment_data['sentiment_breakdown'] = {
            'bloomberg_weighted': sentiment_data['bloomberg_sentiment'] * 0.4,
            'calendar_weighted': sentiment_data['calendar_sentiment'] * 0.3,
            'session_weighted': sentiment_data['session_sentiment'] * 0.2,
            'technical_weighted': sentiment_data['technical_sentiment'] * 0.1
        }
        
        print(f"📊 [DEBUG] === ENHANCED SENTIMENT SUMMARY ===")
        print(f"📰 Bloomberg (40%): {sentiment_data['bloomberg_sentiment']:.3f} → {sentiment_data['sentiment_breakdown']['bloomberg_weighted']:.3f}")
        print(f"📊 Calendar (30%): {sentiment_data['calendar_sentiment']:.3f} → {sentiment_data['sentiment_breakdown']['calendar_weighted']:.3f}")
        print(f"🌍 Session (20%): {sentiment_data['session_sentiment']:.3f} → {sentiment_data['sentiment_breakdown']['session_weighted']:.3f}")
        print(f"📈 Technical (10%): {sentiment_data['technical_sentiment']:.3f} → {sentiment_data['sentiment_breakdown']['technical_weighted']:.3f}")
        print(f"📊 Overall Sentiment: {sentiment_data['overall_sentiment']:.3f}")
        print(f"📰 [DEBUG] Found {len(relevant_bloomberg)} relevant headlines")
        
        return sentiment_data
    
    def _analyze_headline_sentiment(self, headline: str) -> float:
        """Enhanced sentiment analysis based on keywords."""
        positive_words = ['BULLISH', 'GAIN', 'RISE', 'UP', 'STRONG', 'POSITIVE', 'BUY', 'SURGE', 'RALLY', 'BOOM', 'RECOVERY']
        negative_words = ['BEARISH', 'DROP', 'FALL', 'DOWN', 'WEAK', 'NEGATIVE', 'SELL', 'CRASH', 'PLUNGE', 'DECLINE', 'SLUMP']
        
        headline_upper = headline.upper()
        
        positive_count = sum(1 for word in positive_words if word in headline_upper)
        negative_count = sum(1 for word in negative_words if word in headline_upper)
        
        if positive_count == 0 and negative_count == 0:
            sentiment = 0.0
        elif positive_count > negative_count:
            sentiment = 0.3
        elif negative_count > positive_count:
            sentiment = -0.3
        else:
            sentiment = 0.0
        
        print(f"📰 [DEBUG] Headline sentiment: {sentiment:.3f} (positive: {positive_count}, negative: {negative_count})")
        return sentiment

    def _analyze_calendar_sentiment(self, calendar_events: List[Dict[str, Any]]) -> float:
        """Analyze sentiment from economic calendar events."""
        print("📊 [DEBUG] Analyzing calendar sentiment...")
        
        sentiment_score = 0.0
        valid_events = 0
        
        for event in calendar_events:
            # Analyze forecast vs previous
            forecast = event.get('forecast', '')
            previous = event.get('previous', '')
            
            if forecast and previous:
                try:
                    # Clean up values (remove % and convert to float)
                    forecast_clean = forecast.replace('%', '').replace(',', '')
                    previous_clean = previous.replace('%', '').replace(',', '')
                    
                    forecast_val = float(forecast_clean)
                    previous_val = float(previous_clean)
                    
                    # Positive sentiment if forecast > previous
                    if forecast_val > previous_val:
                        sentiment_score += 0.1
                        print(f"📊 [DEBUG] Positive forecast: {forecast} > {previous}")
                    elif forecast_val < previous_val:
                        sentiment_score -= 0.1
                        print(f"📊 [DEBUG] Negative forecast: {forecast} < {previous}")
                    else:
                        print(f"📊 [DEBUG] Neutral forecast: {forecast} = {previous}")
                    
                    valid_events += 1
                except (ValueError, TypeError) as e:
                    print(f"⚠️ [DEBUG] Could not parse forecast/previous: {forecast}/{previous} - {e}")
                    continue
        
        if valid_events > 0:
            final_sentiment = sentiment_score / valid_events
            print(f"📊 [DEBUG] Calendar sentiment: {final_sentiment:.3f} (from {valid_events} events)")
            return final_sentiment
        else:
            print("📊 [DEBUG] No valid calendar events for sentiment analysis")
            return 0.0

    def _analyze_session_sentiment(self, current_session: str, session_overlap: List[str]) -> float:
        """Analyze sentiment based on market sessions."""
        print(f"🌍 [DEBUG] Analyzing session sentiment for {current_session}...")
        
        session_sentiment = 0.0
        
        # Session quality scoring
        if current_session == 'london':
            session_sentiment += 0.2  # High liquidity
            print("🌍 [DEBUG] London session: +0.2 (high liquidity)")
        elif current_session == 'new_york':
            session_sentiment += 0.15  # Good liquidity
            print("🌍 [DEBUG] New York session: +0.15 (good liquidity)")
        elif current_session == 'tokyo':
            session_sentiment += 0.05  # Lower liquidity
            print("🌍 [DEBUG] Tokyo session: +0.05 (lower liquidity)")
        else:
            print("🌍 [DEBUG] After hours session: +0.0 (low liquidity)")
        
        # Session overlap bonus
        if session_overlap:
            overlap_bonus = 0.1 * len(session_overlap)
            session_sentiment += overlap_bonus
            print(f"🌍 [DEBUG] Session overlap bonus: +{overlap_bonus:.3f} ({len(session_overlap)} overlaps)")
        
        print(f"🌍 [DEBUG] Session sentiment: {session_sentiment:.3f}")
        return session_sentiment

    def _analyze_technical_sentiment(self, technical_data: Dict[str, Any]) -> float:
        """Analyze sentiment from technical indicators."""
        print("📈 [DEBUG] Analyzing technical sentiment...")
        
        sentiment_score = 0.0
        
        # RSI sentiment
        rsi = technical_data.get('rsi', 50)
        if rsi > 70:
            sentiment_score -= 0.1  # Overbought
            print(f"📈 [DEBUG] RSI overbought ({rsi:.2f}): -0.1")
        elif rsi < 30:
            sentiment_score += 0.1  # Oversold
            print(f"📈 [DEBUG] RSI oversold ({rsi:.2f}): +0.1")
        else:
            print(f"📈 [DEBUG] RSI neutral ({rsi:.2f}): 0.0")
        
        # MACD sentiment
        macd = technical_data.get('macd', 0)
        if macd > 0:
            sentiment_score += 0.05  # Bullish
            print(f"📈 [DEBUG] MACD bullish ({macd:.6f}): +0.05")
        else:
            sentiment_score -= 0.05  # Bearish
            print(f"📈 [DEBUG] MACD bearish ({macd:.6f}): -0.05")
        
        # ATR sentiment (volatility)
        atr = technical_data.get('atr', 0)
        if atr > 0.001:  # High volatility
            sentiment_score += 0.05  # More trading opportunities
            print(f"📈 [DEBUG] ATR high volatility ({atr:.6f}): +0.05")
        else:
            print(f"📈 [DEBUG] ATR low volatility ({atr:.6f}): 0.0")
        
        print(f"📈 [DEBUG] Technical sentiment: {sentiment_score:.3f}")
        return sentiment_score
    
    def _analyze_correlations(self, pair: str) -> Dict[str, Any]:
        """Analyze currency correlations."""
        print(f"🔗 [DEBUG] Analyzing correlations for {pair}...")
        
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
                print(f"🔗 [DEBUG] Found in correlation group: {group_name}")
                print(f"🔗 [DEBUG] Correlated pairs: {correlation_data['correlated_pairs']}")
                break
        
        return correlation_data
    
    def _calculate_enhanced_fundamental_score(self, pair: str, calendar_events: List[Dict[str, Any]], 
                                            enhanced_sentiment: Dict[str, Any], current_session: str, 
                                            session_overlap: List[str]) -> float:
        """Calculate enhanced fundamental score (0-1) using multi-source sentiment."""
        print(f"🧮 [DEBUG] Calculating enhanced fundamental score for {pair}...")
        
        score = 0.5  # Neutral starting point
        print(f"📊 [DEBUG] Base score: {score:.3f}")
        
        # Session analysis (already included in enhanced sentiment)
        session_sentiment = enhanced_sentiment.get('session_sentiment', 0.0)
        score += session_sentiment * 0.3  # Session sentiment impact
        print(f"🌍 [DEBUG] Session sentiment impact: +{session_sentiment * 0.3:.3f}")
        
        # Session overlap bonus (additional)
        if session_overlap:
            overlap_bonus = 0.05 * len(session_overlap)
            score += overlap_bonus
            print(f"🌍 [DEBUG] Session overlap bonus: +{overlap_bonus:.3f}")
        
        # Calendar events impact (already included in enhanced sentiment)
        calendar_sentiment = enhanced_sentiment.get('calendar_sentiment', 0.0)
        score += calendar_sentiment * 0.2  # Calendar sentiment impact
        print(f"📅 [DEBUG] Calendar sentiment impact: +{calendar_sentiment * 0.2:.3f}")
        
        # Additional calendar events bonus
        if calendar_events:
            event_bonus = min(0.05, len(calendar_events) * 0.005)
            score += event_bonus
            print(f"📅 [DEBUG] Calendar events bonus: +{event_bonus:.3f}")
        
        # Enhanced sentiment impact
        overall_sentiment = enhanced_sentiment.get('overall_sentiment', 0.0)
        sentiment_bonus = overall_sentiment * 0.2
        score += sentiment_bonus
        print(f"📰 [DEBUG] Enhanced sentiment bonus: +{sentiment_bonus:.3f}")
        
        # Technical sentiment impact
        technical_sentiment = enhanced_sentiment.get('technical_sentiment', 0.0)
        technical_bonus = technical_sentiment * 0.1
        score += technical_bonus
        print(f"📈 [DEBUG] Technical sentiment bonus: +{technical_bonus:.3f}")
        
        # Normalize to 0-1 range
        final_score = max(0.0, min(1.0, score))
        print(f"📊 [DEBUG] Final enhanced fundamental score: {final_score:.3f}")
        
        return final_score
    
    def _should_avoid_trading(self, pair: str, high_impact_events: List[Dict[str, Any]], 
                            news_sentiment: Dict[str, Any], current_session: str) -> bool:
        """Determine if we should avoid trading due to fundamental factors."""
        print(f"🚫 [DEBUG] Checking if should avoid trading {pair}...")
        
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
                    print(f"🚫 [DEBUG] High-impact event within 30 minutes: {event.get('event', 'Unknown')}")
                    return True
        
        # Check for extreme news sentiment
        sentiment_score = abs(news_sentiment.get('sentiment_score', 0.0))
        if sentiment_score > 0.8:  # Very strong sentiment
            print(f"🚫 [DEBUG] Extreme news sentiment: {sentiment_score:.3f}")
            return True
        
        # Check for after-hours trading
        if current_session == 'after_hours':
            print(f"🚫 [DEBUG] After-hours trading session")
            return True
        
        print(f"✅ [DEBUG] No fundamental reasons to avoid trading")
        return False

    def _determine_enhanced_fundamental_bias(self, fundamental_score: float, enhanced_sentiment: Dict[str, Any]) -> str:
        """Determine enhanced fundamental bias based on score and sentiment."""
        print(f"🎯 [DEBUG] Determining enhanced fundamental bias...")
        
        # Get sentiment breakdown
        sentiment_breakdown = enhanced_sentiment.get('sentiment_breakdown', {})
        bloomberg_weighted = sentiment_breakdown.get('bloomberg_weighted', 0)
        calendar_weighted = sentiment_breakdown.get('calendar_weighted', 0)
        session_weighted = sentiment_breakdown.get('session_weighted', 0)
        technical_weighted = sentiment_breakdown.get('technical_weighted', 0)
        
        print(f"📊 [DEBUG] Sentiment breakdown:")
        print(f"   Bloomberg: {bloomberg_weighted:.3f}")
        print(f"   Calendar: {calendar_weighted:.3f}")
        print(f"   Session: {session_weighted:.3f}")
        print(f"   Technical: {technical_weighted:.3f}")
        
        # Determine bias based on fundamental score
        if fundamental_score > 0.7:
            bias = 'STRONG_BULLISH'
            print(f"🎯 [DEBUG] Strong bullish fundamentals (score: {fundamental_score:.3f})")
        elif fundamental_score > 0.6:
            bias = 'BULLISH'
            print(f"🎯 [DEBUG] Bullish fundamentals (score: {fundamental_score:.3f})")
        elif fundamental_score > 0.4:
            bias = 'NEUTRAL'
            print(f"🎯 [DEBUG] Neutral fundamentals (score: {fundamental_score:.3f})")
        elif fundamental_score > 0.3:
            bias = 'BEARISH'
            print(f"🎯 [DEBUG] Bearish fundamentals (score: {fundamental_score:.3f})")
        else:
            bias = 'STRONG_BEARISH'
            print(f"🎯 [DEBUG] Strong bearish fundamentals (score: {fundamental_score:.3f})")
        
        return bias
    
    def _calculate_position_multiplier(self, fundamental_score: float, avoid_trading: bool, 
                                     high_impact_events: List[Dict[str, Any]]) -> float:
        """Calculate position size multiplier based on fundamental factors."""
        print(f"📏 [DEBUG] Calculating position multiplier...")
        
        if avoid_trading:
            print(f"🚫 [DEBUG] Avoid trading flag set, multiplier: 0.0")
            return 0.0  # Don't trade
        
        # Base multiplier
        multiplier = 1.0
        print(f"📏 [DEBUG] Base multiplier: {multiplier}")
        
        # Reduce size near high-impact events
        if high_impact_events:
            multiplier *= 0.5
            print(f"📏 [DEBUG] High-impact events reduction: {multiplier}")
        
        # Adjust based on fundamental score
        if fundamental_score > 0.7:
            multiplier *= 1.2  # Increase size for good conditions
            print(f"📏 [DEBUG] Good conditions boost: {multiplier}")
        elif fundamental_score < 0.3:
            multiplier *= 0.7  # Reduce size for poor conditions
            print(f"📏 [DEBUG] Poor conditions reduction: {multiplier}")
        
        final_multiplier = max(0.0, min(2.0, multiplier))  # Cap between 0 and 2
        print(f"📏 [DEBUG] Final position multiplier: {final_multiplier:.3f}")
        
        return final_multiplier
    
    async def get_market_session_info(self) -> Dict[str, Any]:
        """Get current market session information."""
        print("🌍 [DEBUG] Getting market session info...")
        
        current_session = self._get_current_session()
        session_overlap = self._get_session_overlap()
        
        info = {
            'current_session': current_session,
            'session_overlap': session_overlap,
            'session_quality': 'high' if session_overlap else 'medium',
            'liquidity_level': 'high' if current_session in ['london', 'new_york'] else 'medium'
        }
        
        print(f"🌍 [DEBUG] Session info: {info}")
        return info
    
    async def get_fundamental_summary(self) -> Dict[str, Any]:
        """Get summary of fundamental analysis."""
        print("📊 [DEBUG] Getting fundamental summary...")
        
        summary = {
            'calendar_events_count': len(self._calendar_cache),
            'news_sentiment': self._sentiment_cache,
            'current_session': self._get_current_session(),
            'session_overlap': self._get_session_overlap(),
            'last_update': self._last_update
        }
        
        print(f"📊 [DEBUG] Fundamental summary: {summary}")
        return summary 