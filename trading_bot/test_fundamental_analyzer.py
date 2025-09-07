#!/usr/bin/env python3
"""
Test script for the fixed fundamental analyzer.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from trading_bot.src.core.fundamental_analyzer import FundamentalAnalyzer
from trading_bot.src.utils.config import Config
from trading_bot.src.core.models import MarketContext, MarketCondition


async def test_fundamental_analyzer():
    """Test the fundamental analyzer with various scenarios."""
    print("🧪 Testing Fundamental Analyzer...")
    
    # Initialize config and analyzer
    config = Config()
    analyzer = FundamentalAnalyzer(config)
    
    # Test 1: Basic initialization
    print("\n✅ Test 1: Initialization")
    print(f"   - Cache duration: {analyzer._cache_duration}")
    print(f"   - Session times: {analyzer.sessions}")
    print(f"   - Country currency map: {len(analyzer.country_currency_map)} entries")
    print(f"   - Sentiment keywords: {len(analyzer.sentiment_keywords['positive']['strong'])} strong positive")
    
    # Test 2: Session detection
    print("\n✅ Test 2: Session Detection")
    current_session = analyzer._get_current_session()
    session_overlap = analyzer._get_session_overlap()
    print(f"   - Current session: {current_session}")
    print(f"   - Session overlaps: {session_overlap}")
    
    # Test 3: Currency relevance checking
    print("\n✅ Test 3: Currency Relevance")
    test_pairs = ['EUR_USD', 'GBP_JPY', 'AUD_CAD']
    for pair in test_pairs:
        base, quote = pair.split('_')
        print(f"   - {pair}: Base={base}, Quote={quote}")
        
        # Test country mapping
        test_country = 'united states'
        affects = analyzer._country_affects_currency(test_country, base, quote)
        print(f"     {test_country} affects {pair}: {affects}")
        
        # Test event mapping
        test_event = 'FEDERAL RESERVE MEETING'
        affects = analyzer._event_affects_currency(test_event, base, quote)
        print(f"     '{test_event}' affects {pair}: {affects}")
    
    # Test 4: Sentiment analysis
    print("\n✅ Test 4: Sentiment Analysis")
    test_headlines = [
        "USD SURGES ON STRONG ECONOMIC DATA",
        "EUR PLUNGES ON WEAK INFLATION REPORT",
        "GBP STABLE AHEAD OF BOE DECISION",
        "MIXED SIGNALS FOR JPY AS MARKET VOLATILE"
    ]
    
    for headline in test_headlines:
        sentiment = analyzer._analyze_headline_sentiment(headline)
        print(f"   - '{headline}': {sentiment:.3f}")
    
    # Test 5: Fundamental analysis (if data available)
    print("\n✅ Test 5: Fundamental Analysis")
    market_context = MarketContext(
        condition=MarketCondition.NORMAL,
        volatility=0.02,
        trend_strength=0.6,
        news_sentiment=0.5
    )
    
    try:
        result = await analyzer.analyze_fundamentals('EUR_USD', market_context)
        print(f"   - Sentiment score: {result['sentiment_score']:.3f}")
        print(f"   - Fundamental bias: {result['fundamental_bias']}")
        print(f"   - Fundamental score: {result['fundamental_score']:.3f}")
        print(f"   - Avoid trading: {result['avoid_trading']}")
        print(f"   - Position multiplier: {result['position_multiplier']:.3f}")
        print(f"   - Current session: {result['current_session']}")
        print(f"   - Session overlap: {result['session_overlap']}")
        print(f"   - Economic events: {len(result['economic_events'])}")
        print(f"   - High impact events: {len(result['high_impact_events'])}")
    except Exception as e:
        print(f"   - Error in analysis: {e}")
    
    # Test 6: Cache management
    print("\n✅ Test 6: Cache Management")
    print(f"   - Cache valid: {analyzer._is_cache_valid()}")
    print(f"   - Last update: {analyzer._last_update}")
    
    # Test 7: Position multiplier calculation
    print("\n✅ Test 7: Position Multiplier")
    test_scenarios = [
        (0.8, False, []),      # Good conditions, no events
        (0.3, False, []),      # Poor conditions, no events
        (0.5, False, [{'event': 'NFP'}]),  # Neutral, one high impact
        (0.5, True, []),       # Avoid trading
    ]
    
    for score, avoid, events in test_scenarios:
        multiplier = analyzer._calculate_position_multiplier(score, avoid, events)
        print(f"   - Score={score}, Avoid={avoid}, Events={len(events)}: Multiplier={multiplier:.3f}")
    
    print("\n🎉 Fundamental Analyzer Tests Completed!")


if __name__ == "__main__":
    asyncio.run(test_fundamental_analyzer())


