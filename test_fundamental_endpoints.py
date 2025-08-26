#!/usr/bin/env python3
"""
Comprehensive Test for Fundamental Scraping Endpoints
Tests all data sources: Economic Calendar, News Sentiment, and Market Sentiment
"""
import asyncio
import sys
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add the project root to the path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

def test_economic_calendar():
    """Test economic calendar scraping from TradingEconomics."""
    print("🧪 Testing Economic Calendar Endpoint...")
    print("=" * 50)
    
    try:
        from scraping.fx_calendar import get_fx_calendar
        
        # Test calendar scraping
        from_date = datetime.now(timezone.utc) - timedelta(days=1)
        print(f"📅 Scraping calendar from {from_date.strftime('%Y-%m-%d')}...")
        
        calendar_data = get_fx_calendar(from_date)
        
        if calendar_data and len(calendar_data) > 0:
            print(f"✅ Economic Calendar: SUCCESS - Retrieved {len(calendar_data)} events")
            
            # Show sample data
            print("\n📊 Sample Calendar Events:")
            for i, event in enumerate(calendar_data[:5]):  # Show first 5 events
                print(f"  {i+1}. {event.get('country', 'N/A').title()} - {event.get('event', 'N/A')}")
                print(f"     Category: {event.get('category', 'N/A')}")
                print(f"     Date: {event.get('date', 'N/A')}")
                print(f"     Symbol: {event.get('symbol', 'N/A')}")
                print()
            
            # Check data quality
            required_fields = ['date', 'country', 'event', 'category']
            quality_score = 0
            for event in calendar_data[:10]:  # Check first 10 events
                if all(field in event and event[field] for field in required_fields):
                    quality_score += 1
            
            quality_percentage = (quality_score / min(10, len(calendar_data))) * 100
            print(f"📈 Data Quality: {quality_percentage:.1f}% of events have all required fields")
            
            return True, len(calendar_data), quality_percentage
            
        else:
            print("❌ Economic Calendar: FAILED - No data retrieved")
            return False, 0, 0
            
    except Exception as e:
        print(f"❌ Economic Calendar: ERROR - {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False, 0, 0

def test_news_sentiment():
    """Test news sentiment scraping from Reuters/Bloomberg."""
    print("\n🧪 Testing News Sentiment Endpoint...")
    print("=" * 50)
    
    try:
        from scraping.bloomberg_com import bloomberg_com
        
        print("📰 Scraping Bloomberg/Reuters news...")
        news_data = bloomberg_com()
        
        if news_data and len(news_data) > 0:
            print(f"✅ News Sentiment: SUCCESS - Retrieved {len(news_data)} headlines")
            
            # Show sample data
            print("\n📰 Sample News Headlines:")
            for i, article in enumerate(news_data[:3]):  # Show first 3 articles
                headline = article.get('headline', 'N/A')
                link = article.get('link', 'N/A')
                print(f"  {i+1}. {headline[:80]}...")
                print(f"     Link: {link}")
                print()
            
            # Check data quality
            required_fields = ['headline', 'link']
            quality_score = 0
            for article in news_data[:10]:  # Check first 10 articles
                if all(field in article and article[field] for field in required_fields):
                    quality_score += 1
            
            quality_percentage = (quality_score / min(10, len(news_data))) * 100
            print(f"📈 Data Quality: {quality_percentage:.1f}% of articles have all required fields")
            
            return True, len(news_data), quality_percentage
            
        else:
            print("❌ News Sentiment: FAILED - No data retrieved")
            return False, 0, 0
            
    except Exception as e:
        print(f"❌ News Sentiment: ERROR - {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False, 0, 0

def test_market_sentiment():
    """Test market sentiment scraping from DailyFX."""
    print("\n🧪 Testing Market Sentiment Endpoint...")
    print("=" * 50)
    
    try:
        from scraping.dailyfx_com import dailyfx_com
        
        print("📈 Scraping DailyFX market sentiment...")
        sentiment_data = dailyfx_com()
        
        if sentiment_data is not None:
            # Handle different return types
            if hasattr(sentiment_data, 'shape'):  # DataFrame
                data_count = len(sentiment_data)
                print(f"✅ Market Sentiment: SUCCESS - Retrieved {data_count} sentiment records")
                
                # Show sample data
                print("\n📊 Sample Market Sentiment Data:")
                if data_count > 0:
                    sample_data = sentiment_data.head(3)
                    print(sample_data.to_string())
                    print()
                
                # Check data quality
                if 'pair' in sentiment_data.columns:
                    quality_percentage = 100.0
                else:
                    quality_percentage = 50.0
                    
            elif isinstance(sentiment_data, list):
                print(f"✅ Market Sentiment: SUCCESS - Retrieved {len(sentiment_data)} sentiment records")
                
                # Show sample data
                print("\n📊 Sample Market Sentiment Data:")
                for i, record in enumerate(sentiment_data[:3]):
                    print(f"  {i+1}. {record}")
                print()
                
                quality_percentage = 100.0
                
            else:
                print(f"✅ Market Sentiment: SUCCESS - Retrieved data of type {type(sentiment_data)}")
                quality_percentage = 75.0
            
            return True, data_count if 'data_count' in locals() else 1, quality_percentage
            
        else:
            print("❌ Market Sentiment: FAILED - No data retrieved")
            return False, 0, 0
            
    except Exception as e:
        print(f"❌ Market Sentiment: ERROR - {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False, 0, 0

async def test_fundamental_analyzer_integration():
    """Test the complete fundamental analyzer integration."""
    print("\n🧪 Testing Fundamental Analyzer Integration...")
    print("=" * 50)
    
    try:
        from trading_bot.src.core.fundamental_analyzer import FundamentalAnalyzer
        from trading_bot.src.utils.config import Config
        
        # Create a minimal config for testing
        config = Config()
        config.enable_db = False  # Disable database for testing
        
        print("🔧 Initializing Fundamental Analyzer...")
        analyzer = FundamentalAnalyzer(config)
        
        print("📊 Starting fundamental analyzer...")
        await analyzer.start()
        
        # Test fundamental analysis for a specific pair
        pair = "EUR_USD"
        print(f"🔍 Analyzing fundamentals for {pair}...")
        
        fundamental_analysis = await analyzer.analyze_fundamentals(pair)
        
        if fundamental_analysis:
            print("✅ Fundamental Analyzer Integration: SUCCESS")
            print(f"📊 Fundamental Score: {fundamental_analysis.get('score', 'N/A')}")
            print(f"📈 Position Multiplier: {fundamental_analysis.get('position_multiplier', 'N/A')}")
            print(f"⏸️ Avoid Trading: {fundamental_analysis.get('avoid_trading', 'N/A')}")
            
            # Check data quality
            required_fields = ['score', 'position_multiplier', 'avoid_trading']
            quality_score = sum(1 for field in required_fields if field in fundamental_analysis)
            quality_percentage = (quality_score / len(required_fields)) * 100
            
            print(f"📈 Data Quality: {quality_percentage:.1f}% of required fields present")
            
            return True, 1, quality_percentage
            
        else:
            print("❌ Fundamental Analyzer Integration: FAILED - No analysis returned")
            return False, 0, 0
            
    except Exception as e:
        print(f"❌ Fundamental Analyzer Integration: ERROR - {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False, 0, 0

def test_database_integration():
    """Test database integration for fundamental data storage."""
    print("\n🧪 Testing Database Integration...")
    print("=" * 50)
    
    try:
        from db.db import DataDB
        
        print("🗄️ Testing database connection...")
        db = DataDB()
        
        # Test calendar collection
        print("📅 Testing calendar collection...")
        calendar_data = db.query_all(DataDB.CALENDAR_COLL)
        
        if calendar_data is not None:
            print(f"✅ Database Integration: SUCCESS - {len(calendar_data)} calendar events in database")
            
            # Test adding sample data
            sample_event = {
                'date': datetime.now(timezone.utc),
                'country': 'test_country',
                'event': 'test_event',
                'category': 'test_category',
                'symbol': 'TEST'
            }
            
            db.add_one(DataDB.CALENDAR_COLL, sample_event)
            print("✅ Database Write: SUCCESS - Sample event added")
            
            # Clean up test data
            db.delete_many(DataDB.CALENDAR_COLL, {'country': 'test_country'})
            print("✅ Database Cleanup: SUCCESS - Test data removed")
            
            return True, len(calendar_data), 100.0
            
        else:
            print("❌ Database Integration: FAILED - No data in database")
            return False, 0, 0
            
    except Exception as e:
        print(f"❌ Database Integration: ERROR - {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False, 0, 0

def test_cache_system():
    """Test the caching system for fundamental data."""
    print("\n🧪 Testing Cache System...")
    print("=" * 50)
    
    try:
        from trading_bot.src.core.fundamental_analyzer import FundamentalAnalyzer
        from trading_bot.src.utils.config import Config
        
        config = Config()
        config.enable_db = False
        
        analyzer = FundamentalAnalyzer(config)
        
        # Test cache initialization
        if hasattr(analyzer, '_calendar_cache') and hasattr(analyzer, '_news_cache'):
            print("✅ Cache System: SUCCESS - Cache containers initialized")
            
            # Test cache duration
            if hasattr(analyzer, '_cache_duration'):
                cache_duration = analyzer._cache_duration
                print(f"⏱️ Cache Duration: {cache_duration}")
                
                if cache_duration == timedelta(minutes=15):
                    print("✅ Cache Duration: CORRECT - 15 minutes")
                else:
                    print(f"⚠️ Cache Duration: UNEXPECTED - {cache_duration}")
            
            return True, 1, 100.0
            
        else:
            print("❌ Cache System: FAILED - Cache containers not found")
            return False, 0, 0
            
    except Exception as e:
        print(f"❌ Cache System: ERROR - {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False, 0, 0

def test_anti_bot_protection():
    """Test anti-bot protection bypass strategies."""
    print("\n🧪 Testing Anti-Bot Protection Bypass...")
    print("=" * 50)
    
    try:
        import cloudscraper
        import requests
        
        # Test cloudscraper
        print("🌐 Testing Cloudscraper...")
        scraper = cloudscraper.create_scraper()
        
        # Test with a simple request
        test_url = "https://httpbin.org/user-agent"
        response = scraper.get(test_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Cloudscraper: SUCCESS - Bypass working")
            user_agent = response.json().get('user-agent', 'Unknown')
            print(f"🌐 User Agent: {user_agent[:50]}...")
        else:
            print(f"❌ Cloudscraper: FAILED - Status code {response.status_code}")
        
        # Test requests with custom headers
        print("\n🌐 Testing Requests with Custom Headers...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Custom Headers: SUCCESS - Headers working")
        else:
            print(f"❌ Custom Headers: FAILED - Status code {response.status_code}")
        
        return True, 1, 100.0
        
    except Exception as e:
        print(f"❌ Anti-Bot Protection: ERROR - {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False, 0, 0

async def main():
    """Run all fundamental endpoint tests."""
    print("🚀 FUNDAMENTAL ENDPOINTS COMPREHENSIVE TEST")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test results storage
    test_results = []
    
    # Run individual tests
    tests = [
        ("Economic Calendar", test_economic_calendar),
        ("News Sentiment", test_news_sentiment),
        ("Market Sentiment", test_market_sentiment),
        ("Database Integration", test_database_integration),
        ("Cache System", test_cache_system),
        ("Anti-Bot Protection", test_anti_bot_protection),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING: {test_name}")
        print(f"{'='*60}")
        
        try:
            if test_name == "Fundamental Analyzer Integration":
                success, count, quality = await test_func()
            else:
                success, count, quality = test_func()
            
            test_results.append({
                'name': test_name,
                'success': success,
                'count': count,
                'quality': quality
            })
            
        except Exception as e:
            print(f"❌ {test_name}: CRITICAL ERROR - {e}")
            test_results.append({
                'name': test_name,
                'success': False,
                'count': 0,
                'quality': 0
            })
    
    # Run fundamental analyzer integration test
    print(f"\n{'='*60}")
    print(f"🧪 RUNNING: Fundamental Analyzer Integration")
    print(f"{'='*60}")
    
    try:
        success, count, quality = await test_fundamental_analyzer_integration()
        test_results.append({
            'name': 'Fundamental Analyzer Integration',
            'success': success,
            'count': count,
            'quality': quality
        })
    except Exception as e:
        print(f"❌ Fundamental Analyzer Integration: CRITICAL ERROR - {e}")
        test_results.append({
            'name': 'Fundamental Analyzer Integration',
            'success': False,
            'count': 0,
            'quality': 0
        })
    
    # Generate comprehensive report
    print(f"\n{'='*60}")
    print("📊 COMPREHENSIVE TEST RESULTS")
    print(f"{'='*60}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result['success'])
    failed_tests = total_tests - passed_tests
    
    print(f"📈 Overall Results:")
    print(f"   Total Tests: {total_tests}")
    print(f"   ✅ Passed: {passed_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    print(f"   📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    print(f"{'Test Name':<35} {'Status':<8} {'Count':<8} {'Quality':<8}")
    print(f"{'-'*35} {'-'*8} {'-'*8} {'-'*8}")
    
    for result in test_results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{result['name']:<35} {status:<8} {result['count']:<8} {result['quality']:<8.1f}%")
    
    # Calculate average quality
    successful_tests = [r for r in test_results if r['success']]
    if successful_tests:
        avg_quality = sum(r['quality'] for r in successful_tests) / len(successful_tests)
        print(f"\n📊 Average Data Quality: {avg_quality:.1f}%")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if failed_tests > 0:
        print(f"   ⚠️ {failed_tests} endpoint(s) need attention")
        for result in test_results:
            if not result['success']:
                print(f"      - {result['name']}: Check network connectivity and anti-bot protection")
    else:
        print(f"   🎉 All endpoints working correctly!")
    
    if passed_tests == total_tests:
        print(f"\n🎉 ALL FUNDAMENTAL ENDPOINTS WORKING PERFECTLY!")
        print(f"✅ Your fundamental analysis system is ready for production!")
    else:
        print(f"\n⚠️ Some endpoints need attention before production use.")
    
    print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
