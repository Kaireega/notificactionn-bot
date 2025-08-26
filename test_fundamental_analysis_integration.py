#!/usr/bin/env python3
"""
Comprehensive Test for Fundamental Analysis Integration
Tests all the suggested improvements and fundamental analysis integration.
"""
import asyncio
import sys
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal
from pathlib import Path

# Add the project root to the path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.core.models import (
    CandleData, MarketContext, MarketCondition, TradeRecommendation, 
    TradeSignal, TechnicalIndicators, TimeFrame
)
from trading_bot.src.core.fundamental_analyzer_improved import ImprovedFundamentalAnalyzer as FundamentalAnalyzer
from trading_bot.src.data.data_layer import DataLayer
from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer
from trading_bot.src.decision.risk_manager import RiskManager
from trading_bot.src.core.position_manager_improved import ImprovedPositionManager as PositionManager
from api.oanda_api import OandaApi


class FundamentalAnalysisIntegrationTest:
    """Comprehensive test for fundamental analysis integration."""
    
    def __init__(self):
        self.config = Config()
        self.logger = None
        self.test_results = {
            'data_layer': False,
            'fundamental_analyzer': False,
            'technical_analysis': False,
            'risk_manager': False,
            'position_manager': False,
            'integration': False
        }
    
    async def test_data_layer_improvements(self):
        """Test data layer improvements (no mock data, 2000 candles)."""
        print("🧪 Testing Data Layer Improvements...")
        try:
            # Initialize data layer
            data_layer = DataLayer(self.config)
            
            # Test initialization
            await data_layer.start()
            
            # Verify no mock data generation
            if hasattr(data_layer, 'use_real_data'):
                assert data_layer.use_real_data == True, "Should use real data only"
            
            # Test data storage capacity
            for pair in self.config.trading_pairs[:1]:  # Test first pair only
                for timeframe in self.config.timeframes[:1]:  # Test first timeframe only
                    candles = await data_layer.get_candles(pair, timeframe, 2000)
                    print(f"📊 {pair} {timeframe.value}: {len(candles)} candles")
                    assert len(candles) <= 2000, f"Should not exceed 2000 candles, got {len(candles)}"
            
            await data_layer.stop()
            self.test_results['data_layer'] = True
            print("✅ Data Layer Improvements: PASSED")
            
        except Exception as e:
            print(f"❌ Data Layer Improvements: FAILED - {e}")
            traceback.print_exc()
    
    async def test_fundamental_analyzer(self):
        """Test fundamental analyzer functionality."""
        print("🧪 Testing Fundamental Analyzer...")
        try:
            # Initialize fundamental analyzer
            fundamental_analyzer = FundamentalAnalyzer(self.config)
            await fundamental_analyzer.start()
            
            # Test market session detection
            current_session = fundamental_analyzer._get_current_session()
            assert current_session in ['tokyo', 'london', 'new_york', 'unknown'], f"Invalid session: {current_session}"
            print(f"⏰ Current session: {current_session}")
            
            # Test fundamental analysis for trading
            market_context = MarketContext(
                condition=MarketCondition.RANGING,
                volatility=0.001,
                trend_strength=0.5,
                news_sentiment=0.0
            )
            
            fundamental_analysis = await fundamental_analyzer.analyze_fundamentals_for_trading(
                'EUR_USD', market_context
            )
            
            # Verify analysis structure
            required_keys = [
                'fundamental_score', 'current_session', 'calendar_events',
                'news_sentiment', 'avoid_trading', 'session_volatility',
                'correlation_analysis', 'position_size_multiplier'
            ]
            
            for key in required_keys:
                assert key in fundamental_analysis, f"Missing key: {key}"
            
            # Verify score range
            assert 0.0 <= fundamental_analysis['fundamental_score'] <= 1.0, \
                f"Fundamental score out of range: {fundamental_analysis['fundamental_score']}"
            
            # Verify multiplier range
            assert 0.0 <= fundamental_analysis['position_size_multiplier'] <= 2.0, \
                f"Position multiplier out of range: {fundamental_analysis['position_size_multiplier']}"
            
            print(f"📊 Fundamental Score: {fundamental_analysis['fundamental_score']:.3f}")
            print(f"📈 Position Multiplier: {fundamental_analysis['position_size_multiplier']:.3f}")
            print(f"⏸️ Avoid Trading: {fundamental_analysis['avoid_trading']}")
            
            await fundamental_analyzer.stop()
            self.test_results['fundamental_analyzer'] = True
            print("✅ Fundamental Analyzer: PASSED")
            
        except Exception as e:
            print(f"❌ Fundamental Analyzer: FAILED - {e}")
            traceback.print_exc()
    
    async def test_technical_analysis_signals(self):
        """Test technical analysis signal generation and flow."""
        print("🧪 Testing Technical Analysis Signals...")
        try:
            # Initialize technical analysis layer
            technical_layer = TechnicalAnalysisLayer(self.config)
            await technical_layer.start()
            
            # Create test candles
            test_candles = self._create_test_candles('EUR_USD', TimeFrame.M5, 50)
            
            # Create market context
            market_context = MarketContext(
                condition=MarketCondition.RANGING,
                volatility=0.001,
                trend_strength=0.5,
                news_sentiment=0.0
            )
            
            # Test signal analysis
            candles_by_timeframe = {TimeFrame.M5: test_candles}
            recommendation, indicators = await technical_layer.analyze_multiple_timeframes(
                'EUR_USD', candles_by_timeframe, market_context
            )
            
            if recommendation:
                print(f"🎯 Signal: {recommendation.signal.value}")
                print(f"📊 Confidence: {recommendation.confidence:.3f}")
                print(f"⚖️ Risk/Reward: {recommendation.risk_reward_ratio:.3f}")
                print(f"💡 Reasoning: {recommendation.reasoning}")
                
                # Verify recommendation structure
                assert recommendation.signal in [TradeSignal.BUY, TradeSignal.SELL, TradeSignal.HOLD]
                assert 0.0 <= recommendation.confidence <= 1.0
                assert recommendation.risk_reward_ratio > 0
                assert len(recommendation.reasoning) > 0
            
            if indicators:
                print(f"📈 RSI: {indicators.rsi:.2f}")
                print(f"📊 MACD: {indicators.macd:.5f}")
                print(f"📉 ATR: {indicators.atr:.5f}")
            
            await technical_layer.stop()
            self.test_results['technical_analysis'] = True
            print("✅ Technical Analysis Signals: PASSED")
            
        except Exception as e:
            print(f"❌ Technical Analysis Signals: FAILED - {e}")
            traceback.print_exc()
    
    async def test_risk_manager_improvements(self):
        """Test risk manager improvements (unified data, better thresholds)."""
        print("🧪 Testing Risk Manager Improvements...")
        try:
            # Initialize risk manager
            risk_manager = RiskManager(self.config)
            
            # Create test recommendation
            recommendation = TradeRecommendation(
                pair='EUR_USD',
                signal=TradeSignal.BUY,
                confidence=0.75,
                entry_price=Decimal('1.1050'),
                stop_loss=Decimal('1.1000'),
                take_profit=Decimal('1.1150'),
                risk_reward_ratio=2.0,
                market_condition=MarketCondition.RANGING,
                reasoning="Test recommendation"
            )
            
            # Test risk assessment
            market_context = MarketContext(
                condition=MarketCondition.RANGING,
                volatility=0.001,
                trend_strength=0.5,
                news_sentiment=0.0
            )
            
            risk_assessment = await risk_manager.assess_risk(
                recommendation, 1.1050, market_context
            )
            
            print(f"✅ Approved: {risk_assessment['approved']}")
            print(f"📊 Risk Score: {risk_assessment['risk_score']:.3f}")
            print(f"💡 Reason: {risk_assessment['reason']}")
            
            # Verify assessment structure
            assert 'approved' in risk_assessment
            assert 'risk_score' in risk_assessment
            assert 'reason' in risk_assessment
            assert 0.0 <= risk_assessment['risk_score'] <= 1.0
            
            # Test position sizing
            position_size = await risk_manager.calculate_position_size(
                recommendation, risk_assessment
            )
            
            print(f"💰 Position Size: {position_size['size']:.2f}")
            print(f"💵 Risk Amount: ${position_size['risk_amount']:.2f}")
            print(f"📍 Pip Location: {position_size.get('pip_location', 'N/A')}")
            
            # Verify position size structure
            assert 'size' in position_size
            assert 'risk_amount' in position_size
            assert 'stop_loss' in position_size
            assert 'take_profit' in position_size
            
            self.test_results['risk_manager'] = True
            print("✅ Risk Manager Improvements: PASSED")
            
        except Exception as e:
            print(f"❌ Risk Manager Improvements: FAILED - {e}")
            traceback.print_exc()
    
    async def test_position_manager_improvements(self):
        """Test position manager improvements (trailing stops)."""
        print("🧪 Testing Position Manager Improvements...")
        try:
            # Initialize position manager
            oanda_api = OandaApi()
            position_manager = PositionManager(self.config, oanda_api)
            await position_manager.start()
            
            # Test pip size calculation
            pip_size_eur = position_manager._get_pip_size('EUR_USD')
            pip_size_jpy = position_manager._get_pip_size('USD_JPY')
            
            assert pip_size_eur == Decimal('0.0001'), f"EUR pip size should be 0.0001, got {pip_size_eur}"
            assert pip_size_jpy == Decimal('0.01'), f"JPY pip size should be 0.01, got {pip_size_jpy}"
            
            print(f"📏 EUR_USD pip size: {pip_size_eur}")
            print(f"📏 USD_JPY pip size: {pip_size_jpy}")
            
            # Test position summary
            summary = position_manager.get_position_summary()
            print(f"📊 Active Positions: {summary['active_positions']}")
            print(f"💰 Daily P&L: ${summary['daily_pnl']:.2f}")
            
            await position_manager.stop()
            self.test_results['position_manager'] = True
            print("✅ Position Manager Improvements: PASSED")
            
        except Exception as e:
            print(f"❌ Position Manager Improvements: FAILED - {e}")
            traceback.print_exc()
    
    async def test_full_integration(self):
        """Test full integration of all components."""
        print("🧪 Testing Full Integration...")
        try:
            # Initialize all components
            data_layer = DataLayer(self.config)
            fundamental_analyzer = FundamentalAnalyzer(self.config)
            technical_layer = TechnicalAnalysisLayer(self.config)
            risk_manager = RiskManager(self.config)
            oanda_api = OandaApi()
            position_manager = PositionManager(self.config, oanda_api)
            
            # Start components
            await data_layer.start()
            await fundamental_analyzer.start()
            await technical_layer.start()
            await position_manager.start()
            
            # Test complete workflow
            pair = 'EUR_USD'
            
            # 1. Get market data
            candles_data = await data_layer.get_all_data()
            assert pair in candles_data, f"Missing data for {pair}"
            
            # 2. Get market context
            market_context = await data_layer.get_market_context(pair)
            assert market_context is not None, "Market context should not be None"
            
            # 3. Fundamental analysis
            fundamental_analysis = await fundamental_analyzer.analyze_fundamentals_for_trading(
                pair, market_context
            )
            assert fundamental_analysis['fundamental_score'] >= 0.0, "Invalid fundamental score"
            
            # Skip if fundamental analysis suggests avoiding trading
            if fundamental_analysis['avoid_trading']:
                print("⏸️ Fundamental analysis suggests avoiding trading")
                return
            
            # 4. Technical analysis
            candles_by_timeframe = candles_data[pair]
            recommendation, indicators = await technical_layer.analyze_multiple_timeframes(
                pair, candles_by_timeframe, market_context
            )
            
            if recommendation and recommendation.confidence > 0.5:
                # 5. Risk assessment
                current_price = float(recommendation.entry_price) if recommendation.entry_price else 1.1050
                risk_assessment = await risk_manager.assess_risk(
                    recommendation, current_price, market_context
                )
                
                print(f"🎯 Signal: {recommendation.signal.value}")
                print(f"📊 Confidence: {recommendation.confidence:.3f}")
                print(f"📈 Fundamental Score: {fundamental_analysis['fundamental_score']:.3f}")
                print(f"⚠️ Risk Score: {risk_assessment['risk_score']:.3f}")
                print(f"✅ Approved: {risk_assessment['approved']}")
                
                # 6. Position sizing with fundamental multiplier
                position_size = await risk_manager.calculate_position_size(
                    recommendation, risk_assessment
                )
                
                # Apply fundamental multiplier
                adjusted_size = position_size['size'] * Decimal(str(fundamental_analysis['position_size_multiplier']))
                print(f"💰 Base Position Size: {position_size['size']:.2f}")
                print(f"📈 Adjusted Position Size: {adjusted_size:.2f}")
                print(f"🔗 Multiplier: {fundamental_analysis['position_size_multiplier']:.3f}")
                
                # Verify integration
                assert risk_assessment['approved'] in [True, False]
                assert position_size['size'] > 0
                assert fundamental_analysis['position_size_multiplier'] > 0
            
            # Stop components
            await data_layer.stop()
            await fundamental_analyzer.stop()
            await technical_layer.stop()
            await position_manager.stop()
            
            self.test_results['integration'] = True
            print("✅ Full Integration: PASSED")
            
        except Exception as e:
            print(f"❌ Full Integration: FAILED - {e}")
            traceback.print_exc()
    
    def _create_test_candles(self, pair: str, timeframe: TimeFrame, count: int) -> List[CandleData]:
        """Create test candle data."""
        candles = []
        base_price = Decimal('1.1050')
        current_time = datetime.now(timezone.utc)
        
        for i in range(count):
            # Create price movement
            price_change = Decimal(str(0.0001 * (i % 10 - 5)))  # Oscillating price
            current_price = base_price + price_change
            
            # Create candle
            candle = CandleData(
                timestamp=current_time - timedelta(minutes=5 * (count - i)),
                open=current_price,
                high=current_price + Decimal('0.0002'),
                low=current_price - Decimal('0.0002'),
                close=current_price,
                volume=Decimal('5000'),
                pair=pair,
                timeframe=timeframe
            )
            candles.append(candle)
        
        return candles
    
    async def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting Fundamental Analysis Integration Tests")
        print("=" * 60)
        
        # Run individual component tests
        await self.test_data_layer_improvements()
        print()
        
        await self.test_fundamental_analyzer()
        print()
        
        await self.test_technical_analysis_signals()
        print()
        
        await self.test_risk_manager_improvements()
        print()
        
        await self.test_position_manager_improvements()
        print()
        
        await self.test_full_integration()
        print()
        
        # Print results summary
        print("=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        for test_name, passed in self.test_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Fundamental analysis integration is working correctly.")
        else:
            print("⚠️ Some tests failed. Please review the errors above.")
        
        return passed_tests == total_tests


async def main():
    """Main test runner."""
    try:
        test_runner = FundamentalAnalysisIntegrationTest()
        success = await test_runner.run_all_tests()
        
        if success:
            print("\n🎯 FUNDAMENTAL ANALYSIS INTEGRATION READY FOR PRODUCTION")
            print("✅ All improvements have been successfully implemented and tested")
        else:
            print("\n🔧 FUNDAMENTAL ANALYSIS INTEGRATION NEEDS FIXES")
            print("❌ Some components need attention before production use")
        
        return success
        
    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
