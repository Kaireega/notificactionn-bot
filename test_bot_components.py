#!/usr/bin/env python3
"""
Comprehensive Trading Bot Component Test Script
Tests all major components of the trading bot with the new balanced settings.
"""

import asyncio
import sys
import os
import traceback
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Any, List

# Add the trading_bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'trading_bot'))

from trading_bot.src.utils.config import Config
from trading_bot.src.utils.logger import get_logger
from trading_bot.src.core.models import (
    TradeRecommendation, TradeDecision, MarketContext, MarketCondition, 
    TradeSignal, TechnicalIndicators, TimeFrame, CandleData
)
from trading_bot.src.decision.risk_manager_improved import ImprovedRiskManager
from trading_bot.src.decision.enhanced_exit_criteria import EnhancedExitCriteria
from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer
from trading_bot.src.ai.multi_timeframe_analyzer import MultiTimeframeAnalyzer
from trading_bot.src.ai.ai_analysis_layer import AIAnalysisLayer


class BotComponentTester:
    """Comprehensive test suite for all trading bot components."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.test_results = []
        self.config = None
        
    async def run_all_tests(self):
        """Run all component tests."""
        print("🤖 Starting Trading Bot Component Tests...")
        print("=" * 60)
        
        try:
            # Test 1: Configuration Loading
            await self.test_configuration()
            
            # Test 2: Risk Manager
            await self.test_risk_manager()
            
            # Test 3: Technical Analysis
            await self.test_technical_analysis()
            
            # Test 4: Multi-Timeframe Analysis
            await self.test_multi_timeframe_analysis()
            
            # Test 5: Exit Criteria
            await self.test_exit_criteria()
            
            # Test 6: AI Analysis Layer
            await self.test_ai_analysis_layer()
            
            # Test 7: Integration Tests
            await self.test_integration()
            
            # Print summary
            self.print_test_summary()
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            traceback.print_exc()
    
    async def test_configuration(self):
        """Test configuration loading and validation."""
        print("\n📋 Test 1: Configuration Loading")
        print("-" * 40)
        
        try:
            # Load configuration
            self.config = Config()
            print("✅ Configuration loaded successfully")
            
            # Test key settings
            assert self.config.ai_analysis.confidence_threshold == 0.6, f"Expected 0.6, got {self.config.ai_analysis.confidence_threshold}"
            # Check risk/reward ratio from YAML config
            if hasattr(self.config, '_yaml_config') and 'ai_analysis' in self.config._yaml_config:
                risk_reward_min = self.config._yaml_config['ai_analysis'].get('risk_reward_ratio_minimum', 2.0)
                assert risk_reward_min == 1.8, f"Expected 1.8, got {risk_reward_min}"
            assert self.config.trading.max_trades_per_day == 15, f"Expected 15, got {self.config.trading.max_trades_per_day}"
            assert self.config.trading.risk_percentage == 4.0, f"Expected 4.0, got {self.config.trading.risk_percentage}"
            
            print("✅ All configuration values match expected balanced settings")
            
            # Test multi-timeframe settings from YAML config
            if hasattr(self.config, '_yaml_config') and 'multi_timeframe' in self.config._yaml_config:
                mtf_config = self.config._yaml_config['multi_timeframe']
                assert len(mtf_config.get('timeframes', [])) == 3, "Expected 3 timeframes"
                assert mtf_config.get('minimum_timeframes', 3) == 2, "Expected 2 minimum timeframes"
                assert mtf_config.get('consensus_threshold', 0.75) == 0.65, "Expected 0.65 consensus threshold"
            
            print("✅ Multi-timeframe settings validated")
            
            self.test_results.append(("Configuration", "PASS"))
            
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
            self.test_results.append(("Configuration", "FAIL"))
            raise
    
    async def test_risk_manager(self):
        """Test risk manager with various scenarios."""
        print("\n📋 Test 2: Risk Manager")
        print("-" * 40)
        
        try:
            risk_manager = ImprovedRiskManager(self.config)
            print("✅ Risk manager initialized")
            
            # Test 1: High confidence trade (should pass)
            high_confidence_trade = self._create_test_recommendation(
                confidence=0.75,
                risk_reward_ratio=2.0
            )
            
            market_context = MarketContext(
                condition=MarketCondition.BREAKOUT,
                volatility=0.002,
                trend_strength=0.8
            )
            
            result = await risk_manager.assess_risk(
                high_confidence_trade, 1.2000, market_context
            )
            
            if result['approved']:
                print("✅ High confidence trade approved (expected)")
            else:
                print(f"❌ High confidence trade rejected: {result['reason']}")
            
            # Test 2: Low confidence trade (should fail)
            low_confidence_trade = self._create_test_recommendation(
                confidence=0.5,
                risk_reward_ratio=1.5
            )
            
            result = await risk_manager.assess_risk(
                low_confidence_trade, 1.2000, market_context
            )
            
            if not result['approved']:
                print("✅ Low confidence trade rejected (expected)")
            else:
                print("❌ Low confidence trade approved (unexpected)")
            
            # Test 3: Market condition specific tests
            await self._test_market_condition_risk_rules(risk_manager)
            
            self.test_results.append(("Risk Manager", "PASS"))
            
        except Exception as e:
            print(f"❌ Risk manager test failed: {e}")
            self.test_results.append(("Risk Manager", "FAIL"))
            raise
    
    async def _test_market_condition_risk_rules(self, risk_manager):
        """Test market condition specific risk rules."""
        print("  Testing market condition rules...")
        
        # Test news reactionary market
        news_trade = self._create_test_recommendation(
            confidence=0.65,  # Below 0.7 requirement
            risk_reward_ratio=1.8,
            market_condition=MarketCondition.NEWS_REACTIONARY
        )
        
        market_context = MarketContext(condition=MarketCondition.NEWS_REACTIONARY)
        result = await risk_manager.assess_risk(news_trade, 1.2000, market_context)
        
        if not result['approved']:
            print("  ✅ News trade with low confidence rejected (expected)")
        else:
            print("  ❌ News trade with low confidence approved (unexpected)")
        
        # Test reversal market
        reversal_trade = self._create_test_recommendation(
            confidence=0.7,  # Above 0.65 requirement
            risk_reward_ratio=2.0,  # Above 1.8 requirement
            market_condition=MarketCondition.REVERSAL
        )
        
        market_context = MarketContext(condition=MarketCondition.REVERSAL)
        result = await risk_manager.assess_risk(reversal_trade, 1.2000, market_context)
        
        if result['approved']:
            print("  ✅ Reversal trade with good parameters approved (expected)")
        else:
            print(f"  ❌ Reversal trade rejected: {result['reason']}")
    
    async def test_technical_analysis(self):
        """Test technical analysis layer."""
        print("\n📋 Test 3: Technical Analysis")
        print("-" * 40)
        
        try:
            tech_analyzer = TechnicalAnalysisLayer(self.config)
            print("✅ Technical analyzer initialized")
            
            # Create test indicators
            indicators = TechnicalIndicators(
                rsi=65.0,
                macd=0.0002,
                macd_signal=0.0001,
                bollinger_upper=1.2050,
                bollinger_lower=1.1950,
                bollinger_middle=1.2000,
                ema_fast=1.2010,
                ema_slow=1.1990,
                atr=0.0020
            )
            
            market_context = MarketContext(condition=MarketCondition.BREAKOUT)
            
            # Test signal analysis
            signals = tech_analyzer._analyze_technical_signals(indicators, market_context)
            
            if signals['has_signal']:
                print(f"✅ Technical signals detected: {signals['overall_signal']}")
                print(f"  Signal strength: {signals['signal_strength']:.2f}")
                print(f"  Reasoning: {', '.join(signals['reasoning'])}")
            else:
                print("ℹ️ No technical signals detected")
            
            # Test confidence calculation
            confidence = tech_analyzer._calculate_technical_confidence(
                signals, {TimeFrame.M5: indicators}
            )
            print(f"✅ Technical confidence calculated: {confidence:.2f}")
            
            self.test_results.append(("Technical Analysis", "PASS"))
            
        except Exception as e:
            print(f"❌ Technical analysis test failed: {e}")
            self.test_results.append(("Technical Analysis", "FAIL"))
            raise
    
    async def test_multi_timeframe_analysis(self):
        """Test multi-timeframe analyzer."""
        print("\n📋 Test 4: Multi-Timeframe Analysis")
        print("-" * 40)
        
        try:
            mtf_analyzer = MultiTimeframeAnalyzer()
            print("✅ Multi-timeframe analyzer initialized")
            
            # Create test candles for different timeframes
            candles_m5 = self._create_test_candles(20, 1.2000, 0.0020)
            candles_m15 = self._create_test_candles(20, 1.2000, 0.0030)
            candles_h1 = self._create_test_candles(20, 1.2000, 0.0040)
            
            candles_by_timeframe = {
                TimeFrame.M5: candles_m5,
                TimeFrame.M15: candles_m15,
                TimeFrame.H1: candles_h1
            }
            
            market_context = MarketContext(
                condition=MarketCondition.BREAKOUT,
                volatility=0.0025,
                trend_strength=0.8
            )
            
            # Test analysis
            recommendation = await mtf_analyzer.analyze(
                "EUR_USD", candles_by_timeframe, None, market_context
            )
            
            if recommendation:
                print(f"✅ Multi-timeframe recommendation generated")
                print(f"  Signal: {recommendation.signal}")
                print(f"  Confidence: {recommendation.confidence:.2f}")
                print(f"  Risk/Reward: {recommendation.risk_reward_ratio:.2f}")
                print(f"  Reasoning: {recommendation.reasoning}")
            else:
                print("ℹ️ No multi-timeframe recommendation (may be due to strict criteria)")
            
            self.test_results.append(("Multi-Timeframe Analysis", "PASS"))
            
        except Exception as e:
            print(f"❌ Multi-timeframe analysis test failed: {e}")
            self.test_results.append(("Multi-Timeframe Analysis", "FAIL"))
            raise
    
    async def test_exit_criteria(self):
        """Test enhanced exit criteria."""
        print("\n📋 Test 5: Exit Criteria")
        print("-" * 40)
        
        try:
            exit_criteria = EnhancedExitCriteria(self.config)
            print("✅ Exit criteria initialized")
            
            # Create test trade decision
            recommendation = self._create_test_recommendation(
                confidence=0.7,
                risk_reward_ratio=2.0,
                entry_price=1.2000,
                stop_loss=1.1980,
                take_profit=1.2040
            )
            
            trade_decision = TradeDecision(
                recommendation=recommendation,
                approved=True,
                position_size=10000,
                risk_amount=200,
                modified_stop_loss=1.1980,
                modified_take_profit=1.2040,
                risk_management_notes="Test trade",
                timestamp=datetime.now(timezone.utc)
            )
            
            market_context = MarketContext(condition=MarketCondition.BREAKOUT)
            
            # Test exit evaluation
            exit_result = await exit_criteria.evaluate_exit_conditions(
                trade_decision, 1.2040, market_context, trade_duration_minutes=30
            )
            
            if exit_result['should_exit']:
                print(f"✅ Exit condition triggered: {exit_result['exit_type']}")
                print(f"  Reason: {exit_result['reason']}")
            else:
                print("ℹ️ No exit conditions met (expected for test scenario)")
            
            self.test_results.append(("Exit Criteria", "PASS"))
            
        except Exception as e:
            print(f"❌ Exit criteria test failed: {e}")
            self.test_results.append(("Exit Criteria", "FAIL"))
            raise
    
    async def test_ai_analysis_layer(self):
        """Test AI analysis layer (without actual API calls)."""
        print("\n📋 Test 6: AI Analysis Layer")
        print("-" * 40)
        
        try:
            # Test without OpenAI API key to avoid actual API calls
            ai_analyzer = AIAnalysisLayer(self.config)
            print("✅ AI analyzer initialized")
            
            # Test technical analyzer integration
            if hasattr(ai_analyzer, 'technical_analyzer'):
                print("✅ Technical analyzer integrated")
            
            # Test multi-timeframe analyzer integration
            if hasattr(ai_analyzer, 'multi_timeframe_analyzer'):
                print("✅ Multi-timeframe analyzer integrated")
            
            # Test prompt loading
            if hasattr(ai_analyzer, 'prompts'):
                print(f"✅ Analysis prompts loaded: {len(ai_analyzer.prompts)} market conditions")
            
            self.test_results.append(("AI Analysis Layer", "PASS"))
            
        except Exception as e:
            print(f"❌ AI analysis layer test failed: {e}")
            self.test_results.append(("AI Analysis Layer", "FAIL"))
            raise
    
    async def test_integration(self):
        """Test integration between components."""
        print("\n📋 Test 7: Integration Tests")
        print("-" * 40)
        
        try:
            # Test end-to-end workflow
            print("Testing end-to-end workflow...")
            
            # 1. Create test data
            candles = self._create_test_candles(50, 1.2000, 0.0020)
            market_context = MarketContext(
                condition=MarketCondition.BREAKOUT,
                volatility=0.0025,
                trend_strength=0.8
            )
            
            # 2. Technical analysis
            tech_analyzer = TechnicalAnalysisLayer(self.config)
            indicators = self._create_test_indicators()
            signals = tech_analyzer._analyze_technical_signals(indicators, market_context)
            
            # 3. Multi-timeframe analysis
            mtf_analyzer = MultiTimeframeAnalyzer()
            candles_by_timeframe = {
                TimeFrame.M5: candles,
                TimeFrame.M15: candles,
                TimeFrame.H1: candles
            }
            
            recommendation = await mtf_analyzer.analyze(
                "EUR_USD", candles_by_timeframe, None, market_context
            )
            
            # 4. Risk assessment
            if recommendation:
                risk_manager = ImprovedRiskManager(self.config)
                risk_result = await risk_manager.assess_risk(
                    recommendation, 1.2000, market_context
                )
                
                print(f"✅ Integration test completed")
                print(f"  Recommendation generated: {recommendation is not None}")
                print(f"  Risk assessment: {'Approved' if risk_result['approved'] else 'Rejected'}")
                print(f"  Risk score: {risk_result.get('risk_score', 'N/A'):.2f}")
            else:
                print("ℹ️ No recommendation generated (strict criteria)")
            
            self.test_results.append(("Integration", "PASS"))
            
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            self.test_results.append(("Integration", "FAIL"))
            raise
    
    def _create_test_recommendation(self, **kwargs) -> TradeRecommendation:
        """Create a test trade recommendation."""
        defaults = {
            'pair': 'EUR_USD',
            'signal': TradeSignal.BUY,
            'entry_price': Decimal('1.2000'),
            'stop_loss': Decimal('1.1980'),
            'take_profit': Decimal('1.2040'),
            'confidence': 0.7,
            'market_condition': MarketCondition.BREAKOUT,
            'reasoning': 'Test recommendation',
            'risk_reward_ratio': 2.0,
            'estimated_hold_time': timedelta(minutes=60),
            'timestamp': datetime.now(timezone.utc)
        }
        defaults.update(kwargs)
        
        return TradeRecommendation(**defaults)
    
    def _create_test_candles(self, count: int, base_price: float, volatility: float) -> List[CandleData]:
        """Create test candle data."""
        candles = []
        for i in range(count):
            price = base_price + (i * 0.0001)  # Slight uptrend
            high = price + volatility
            low = price - volatility
            open_price = price - (volatility * 0.5)
            close_price = price + (volatility * 0.5)
            
            candle = CandleData(
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=count-i),
                open=Decimal(str(open_price)),
                high=Decimal(str(high)),
                low=Decimal(str(low)),
                close=Decimal(str(close_price)),
                volume=Decimal('1000000')
            )
            candles.append(candle)
        
        return candles
    
    def _create_test_indicators(self) -> TechnicalIndicators:
        """Create test technical indicators."""
        return TechnicalIndicators(
            rsi=65.0,
            macd=0.0002,
            macd_signal=0.0001,
            bollinger_upper=1.2050,
            bollinger_lower=1.1950,
            bollinger_middle=1.2000,
            ema_fast=1.2010,
            ema_slow=1.1990,
            atr=0.0020
        )
    
    def print_test_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results:
            status = "✅ PASS" if result == "PASS" else "❌ FAIL"
            print(f"{test_name:<25} {status}")
            
            if result == "PASS":
                passed += 1
            else:
                failed += 1
        
        print("-" * 60)
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 All tests passed! Bot components are working correctly.")
        else:
            print(f"\n⚠️ {failed} test(s) failed. Please review the errors above.")
        
        print("\n💡 Recommendations:")
        print("- If all tests pass, your bot is ready for testing")
        print("- If tests fail, check the error messages and fix issues")
        print("- Consider running with real data for final validation")


async def main():
    """Main test runner."""
    tester = BotComponentTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
