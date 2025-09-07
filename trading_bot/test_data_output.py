#!/usr/bin/env python3
"""
Comprehensive test script to verify data output from scraping functions and fundamental analyzer.
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add the project root to the path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from scraping.bloomberg_com import bloomberg_com
from scraping.dailyfx_com import dailyfx_com
from scraping.fx_calendar import get_fx_calendar
from trading_bot.src.core.fundamental_analyzer import FundamentalAnalyzer
from trading_bot.src.utils.config import Config
from trading_bot.src.core.models import MarketContext, MarketCondition


def test_scraping_functions():
    """Test individual scraping functions and their output."""
    print("🔍 Testing Scraping Functions...")
    
    # Test 1: Bloomberg/Reuters scraping
    print("\n📰 Test 1: Bloomberg/Reuters Scraping")
    try:
        bloomberg_data = bloomberg_com()
        print(f"   - Type: {type(bloomberg_data)}")
        print(f"   - Length: {len(bloomberg_data)}")
        
        if bloomberg_data:
            print(f"   - First item type: {type(bloomberg_data[0])}")
            print(f"   - First item keys: {list(bloomberg_data[0].keys()) if isinstance(bloomberg_data[0], dict) else 'N/A'}")
            if isinstance(bloomberg_data[0], dict):
                print(f"   - Sample headline: {bloomberg_data[0].get('headline', 'N/A')[:50]}...")
        else:
            print("   - ⚠️ No data returned")
            
    except Exception as e:
        print(f"   - ❌ Error: {e}")
    
    # Test 2: DailyFX scraping
    print("\n📊 Test 2: DailyFX Scraping")
    try:
        dailyfx_data = dailyfx_com()
        print(f"   - Type: {type(dailyfx_data)}")
        
        if isinstance(dailyfx_data, dict):
            print(f"   - Keys: {list(dailyfx_data.keys())}")
            print(f"   - Sentiment score: {dailyfx_data.get('sentiment', 'N/A')}")
            print(f"   - Data length: {len(dailyfx_data.get('data', []))}")
            
            if dailyfx_data.get('data'):
                print(f"   - First pair data: {dailyfx_data['data'][0] if dailyfx_data['data'] else 'N/A'}")
        else:
            print(f"   - ⚠️ Unexpected type: {type(dailyfx_data)}")
            print(f"   - Content: {dailyfx_data}")
            
    except Exception as e:
        print(f"   - ❌ Error: {e}")
    
    # Test 3: FX Calendar scraping
    print("\n📅 Test 3: FX Calendar Scraping")
    try:
        from_date = datetime.now(timezone.utc) - timedelta(days=1)
        calendar_data = get_fx_calendar(from_date)
        print(f"   - Type: {type(calendar_data)}")
        print(f"   - Length: {len(calendar_data)}")
        
        if calendar_data:
            print(f"   - First item type: {type(calendar_data[0])}")
            print(f"   - First item keys: {list(calendar_data[0].keys()) if isinstance(calendar_data[0], dict) else 'N/A'}")
            if isinstance(calendar_data[0], dict):
                sample_event = calendar_data[0]
                print(f"   - Sample event: {sample_event.get('event', 'N/A')}")
                print(f"   - Sample country: {sample_event.get('country', 'N/A')}")
                print(f"   - Sample date: {sample_event.get('date', 'N/A')}")
        else:
            print("   - ⚠️ No calendar data returned")
            
    except Exception as e:
        print(f"   - ❌ Error: {e}")


async def test_fundamental_analyzer_data():
    """Test the fundamental analyzer with real data flow."""
    print("\n🧠 Testing Fundamental Analyzer Data Flow...")
    
    # Initialize analyzer
    config = Config()
    analyzer = FundamentalAnalyzer(config)
    
    # Test 1: Load calendar data
    print("\n📅 Test 1: Calendar Data Loading")
    try:
        await analyzer._load_calendar_data()
        print(f"   - Calendar cache type: {type(analyzer._calendar_cache)}")
        print(f"   - Calendar cache length: {len(analyzer._calendar_cache)}")
        
        if analyzer._calendar_cache:
            print(f"   - First event: {analyzer._calendar_cache[0] if analyzer._calendar_cache else 'N/A'}")
        else:
            print("   - ⚠️ No calendar data loaded")
            
    except Exception as e:
        print(f"   - ❌ Error: {e}")
    
    # Test 2: Load news data
    print("\n📰 Test 2: News Data Loading")
    try:
        await analyzer._load_news_data()
        print(f"   - News cache type: {type(analyzer._news_cache)}")
        print(f"   - News cache keys: {list(analyzer._news_cache.keys())}")
        
        bloomberg_data = analyzer._news_cache.get('bloomberg', [])
        dailyfx_data = analyzer._news_cache.get('dailyfx', {})
        
        print(f"   - Bloomberg data length: {len(bloomberg_data)}")
        print(f"   - DailyFX data type: {type(dailyfx_data)}")
        
        if isinstance(dailyfx_data, dict):
            print(f"   - DailyFX sentiment: {dailyfx_data.get('sentiment', 'N/A')}")
            print(f"   - DailyFX data length: {len(dailyfx_data.get('data', []))}")
            
    except Exception as e:
        print(f"   - ❌ Error: {e}")
    
    # Test 3: Get relevant events
    print("\n🎯 Test 3: Relevant Events Detection")
    try:
        test_pairs = ['EUR_USD', 'GBP_JPY', 'USD_CAD']
        for pair in test_pairs:
            events = await analyzer._get_relevant_events(pair)
            print(f"   - {pair}: {len(events)} relevant events")
            
            if events:
                print(f"     Sample event: {events[0].get('event', 'N/A')}")
                print(f"     Sample country: {events[0].get('country', 'N/A')}")
                
    except Exception as e:
        print(f"   - ❌ Error: {e}")
    
    # Test 4: News sentiment analysis
    print("\n📊 Test 4: News Sentiment Analysis")
    try:
        test_pairs = ['EUR_USD', 'GBP_JPY']
        for pair in test_pairs:
            sentiment = await analyzer._get_news_sentiment(pair)
            print(f"   - {pair}:")
            print(f"     Overall sentiment: {sentiment.get('overall_sentiment', 'N/A')}")
            print(f"     Bloomberg sentiment: {sentiment.get('bloomberg_sentiment', 'N/A')}")
            print(f"     DailyFX sentiment: {sentiment.get('dailyfx_sentiment', 'N/A')}")
            print(f"     Relevant headlines: {len(sentiment.get('relevant_headlines', []))}")
            
    except Exception as e:
        print(f"   - ❌ Error: {e}")
    
    # Test 5: Full fundamental analysis
    print("\n🔬 Test 5: Full Fundamental Analysis")
    try:
        market_context = MarketContext(
            condition=MarketCondition.UNKNOWN,  # Fixed: Use UNKNOWN instead of NORMAL
            volatility=0.02,
            trend_strength=0.6,
            news_sentiment=0.5
        )
        
        result = await analyzer.analyze_fundamentals('EUR_USD', market_context)
        
        print("   - Analysis Results:")
        for key, value in result.items():
            if key == 'analysis_timestamp':
                print(f"     {key}: {value}")
            elif isinstance(value, (list, dict)):
                print(f"     {key}: {type(value).__name__} with {len(value)} items")
            else:
                print(f"     {key}: {value}")
                
    except Exception as e:
        print(f"   - ❌ Error: {e}")


def test_data_validation():
    """Test data validation and error handling."""
    print("\n✅ Testing Data Validation...")
    
    # Test 1: Empty data handling
    print("\n🔍 Test 1: Empty Data Handling")
    try:
        # Test with empty calendar cache
        config = Config()
        analyzer = FundamentalAnalyzer(config)
        analyzer._calendar_cache = []
        
        # This should not crash
        sentiment_score = analyzer._calculate_sentiment_score([], {})
        print(f"   - Empty data sentiment score: {sentiment_score}")
        
    except Exception as e:
        print(f"   - ❌ Error with empty data: {e}")
    
    # Test 2: Invalid data handling
    print("\n🔍 Test 2: Invalid Data Handling")
    try:
        # Test with malformed data
        invalid_events = [{'event': None}, {'event': ''}, {'invalid_key': 'value'}]
        sentiment_score = analyzer._calculate_sentiment_score(invalid_events, {})
        print(f"   - Invalid data sentiment score: {sentiment_score}")
        
    except Exception as e:
        print(f"   - ❌ Error with invalid data: {e}")


async def main():
    """Run all tests."""
    print("🚀 Starting Comprehensive Data Output Tests...")
    print("=" * 60)
    
    # Test scraping functions
    test_scraping_functions()
    
    # Test fundamental analyzer data flow
    await test_fundamental_analyzer_data()
    
    # Test data validation
    test_data_validation()
    
    print("\n" + "=" * 60)
    print("🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
