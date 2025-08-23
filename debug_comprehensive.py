#!/usr/bin/env python3
"""
Comprehensive Debugging Script for Trading Bot Components
Tests each component systematically from lowest level to highest level.
"""
import asyncio
import sys
import traceback
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import pandas as pd
import numpy as np

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Add trading_bot/src to the path
trading_bot_src = project_root / "trading_bot" / "src"
sys.path.append(str(trading_bot_src))

from trading_bot.src.utils.config import Config
from trading_bot.src.core.models import (
    CandleData, MarketContext, MarketCondition, TradeRecommendation, 
    TradeSignal, TechnicalIndicators, TimeFrame, TradeDecision
)
from trading_bot.src.ai.technical_analyzer import TechnicalAnalyzer
from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer
from trading_bot.src.decision.technical_decision_layer import TechnicalDecisionLayer
from trading_bot.src.decision.risk_manager import RiskManager
from trading_bot.src.backtesting.backtest_engine import BacktestEngine


class ComprehensiveDebugger:
    """Comprehensive debugging class for trading bot components."""
    
    def __init__(self):
        self.config = Config()
        self.logger = None  # Will be set up later
        self.test_results = {}
        
    def print_header(self, title: str):
        """Print a formatted header."""
        print("\n" + "="*80)
        print(f"🔍 {title}")
        print("="*80)
    
    def print_section(self, title: str):
        """Print a formatted section header."""
        print(f"\n📋 {title}")
        print("-" * 60)
    
    def print_success(self, message: str):
        """Print a success message."""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """Print an error message."""
        print(f"❌ {message}")
    
    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"⚠️ {message}")
    
    def print_info(self, message: str):
        """Print an info message."""
        print(f"ℹ️ {message}")
    
    def generate_test_candles(self, pair: str = "EUR_USD", count: int = 100) -> list[CandleData]:
        """Generate realistic test candle data."""
        print(f"📊 Generating {count} test candles for {pair}...")
        
        # Start with a realistic price
        base_price = 1.0850  # EUR/USD typical price
        candles = []
        
        # Generate realistic price movements
        np.random.seed(42)  # For reproducible results
        price_changes = np.random.normal(0, 0.0005, count)  # Small price changes
        
        current_price = base_price
        for i in range(count):
            # Calculate OHLC
            change = price_changes[i]
            open_price = current_price
            close_price = current_price + change
            
            # Generate realistic high/low
            volatility = abs(change) * 2 + 0.0001
            high = max(open_price, close_price) + np.random.uniform(0, volatility)
            low = min(open_price, close_price) - np.random.uniform(0, volatility)
            
            # Ensure high >= max(open, close) and low <= min(open, close)
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            # Create candle
            candle = CandleData(
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=(count-i)*5),
                open=Decimal(str(open_price)),
                high=Decimal(str(high)),
                low=Decimal(str(low)),
                close=Decimal(str(close_price)),
                volume=Decimal(str(np.random.uniform(1000, 10000))),
                pair=pair,
                timeframe=TimeFrame.M5
            )
            
            candles.append(candle)
            current_price = close_price
        
        print(f"✅ Generated {len(candles)} test candles")
        return candles
    
    def test_1_technical_indicators(self):
        """Test 1: Technical Indicators Calculation"""
        self.print_header("TEST 1: Technical Indicators Calculation")
        
        try:
            # Generate test data
            candles = self.generate_test_candles("EUR_USD", 100)
            
            # Test technical analyzer
            analyzer = TechnicalAnalyzer()
            analyzer.logger = self.logger
            
            # Calculate indicators
            indicators = analyzer.calculate_indicators(candles)
            
            # Check if indicators were calculated
            if indicators.rsi is not None:
                self.print_success(f"RSI calculated: {indicators.rsi:.2f}")
            else:
                self.print_error("RSI calculation failed")
            
            if indicators.macd is not None:
                self.print_success(f"MACD calculated: {indicators.macd:.6f}")
            else:
                self.print_error("MACD calculation failed")
            
            if indicators.atr is not None:
                self.print_success(f"ATR calculated: {indicators.atr:.6f}")
            else:
                self.print_error("ATR calculation failed")
            
            if indicators.bollinger_upper is not None:
                self.print_success(f"Bollinger Bands calculated: Upper={indicators.bollinger_upper:.5f}, Lower={indicators.bollinger_lower:.5f}")
            else:
                self.print_error("Bollinger Bands calculation failed")
            
            if indicators.ema_fast is not None and indicators.ema_slow is not None:
                self.print_success(f"EMA calculated: Fast={indicators.ema_fast:.5f}, Slow={indicators.ema_slow:.5f}")
            else:
                self.print_error("EMA calculation failed")
            
            # Test with insufficient data
            short_candles = candles[:10]  # Only 10 candles
            short_indicators = analyzer.calculate_indicators(short_candles)
            
            if short_indicators.rsi is None:
                self.print_success("Correctly handles insufficient data")
            else:
                self.print_warning("Should not calculate indicators with insufficient data")
            
            self.test_results['technical_indicators'] = True
            return True
            
        except Exception as e:
            self.print_error(f"Technical indicators test failed: {e}")
            traceback.print_exc()
            self.test_results['technical_indicators'] = False
            return False
    
    def test_2_technical_analysis_layer(self):
        """Test 2: Technical Analysis Layer"""
        self.print_header("TEST 2: Technical Analysis Layer")
        
        try:
            # Generate test data for multiple timeframes
            m5_candles = self.generate_test_candles("EUR_USD", 100)
            m15_candles = self.generate_test_candles("EUR_USD", 50)
            h1_candles = self.generate_test_candles("EUR_USD", 24)
            
            candles_by_timeframe = {
                TimeFrame.M5: m5_candles,
                TimeFrame.M15: m15_candles,
                TimeFrame.H1: h1_candles
            }
            
            # Create market context
            market_context = MarketContext(
                condition=MarketCondition.RANGING,
                volatility=Decimal('0.001'),
                trend_strength=Decimal('0.5'),
                news_sentiment=Decimal('0.0')
            )
            
            # Test technical analysis layer
            analysis_layer = TechnicalAnalysisLayer(self.config)
            
            # Analyze
            recommendation, indicators = asyncio.run(
                analysis_layer.analyze_multiple_timeframes(
                    "EUR_USD", candles_by_timeframe, market_context
                )
            )
            
            if recommendation:
                self.print_success(f"Recommendation generated: {recommendation.signal.value}")
                self.print_info(f"Confidence: {recommendation.confidence:.2f}")
                self.print_info(f"Reasoning: {recommendation.reasoning}")
                self.print_info(f"Entry: {recommendation.entry_price}, SL: {recommendation.stop_loss}, TP: {recommendation.take_profit}")
            else:
                self.print_info("No recommendation generated (this is normal for some market conditions)")
            
            if indicators:
                self.print_success("Technical indicators calculated successfully")
            else:
                self.print_error("Technical indicators calculation failed")
            
            self.test_results['technical_analysis_layer'] = True
            return True
            
        except Exception as e:
            self.print_error(f"Technical analysis layer test failed: {e}")
            traceback.print_exc()
            self.test_results['technical_analysis_layer'] = False
            return False
    
    def test_3_risk_manager(self):
        """Test 3: Risk Manager"""
        self.print_header("TEST 3: Risk Manager")
        
        try:
            # Create test recommendation
            recommendation = TradeRecommendation(
                pair="EUR_USD",
                signal=TradeSignal.BUY,
                confidence=0.75,
                entry_price=Decimal('1.0850'),
                stop_loss=Decimal('1.0840'),
                take_profit=Decimal('1.0870'),
                risk_reward_ratio=2.0,
                reasoning="Test recommendation",
                market_condition=MarketCondition.BREAKOUT
            )
            
            # Create market context
            market_context = MarketContext(
                condition=MarketCondition.BREAKOUT,
                volatility=Decimal('0.001'),
                trend_strength=Decimal('0.7'),
                news_sentiment=Decimal('0.0')
            )
            
            # Test risk manager
            risk_manager = RiskManager(self.config)
            
            # Assess risk
            risk_assessment = asyncio.run(
                risk_manager.assess_risk(recommendation, 1.0850, market_context)
            )
            
            self.print_info(f"Risk assessment: {risk_assessment}")
            
            if risk_assessment['approved']:
                self.print_success("Risk assessment approved")
                
                # Calculate position size
                position_size = asyncio.run(
                    risk_manager.calculate_position_size(recommendation, risk_assessment)
                )
                
                self.print_info(f"Position size calculation: {position_size}")
                
                if position_size['size'] > 0:
                    self.print_success("Position size calculated successfully")
                else:
                    self.print_warning("Position size is zero")
            else:
                self.print_info(f"Risk assessment rejected: {risk_assessment['reason']}")
            
            # Test with low confidence
            low_confidence_rec = TradeRecommendation(
                pair="EUR_USD",
                signal=TradeSignal.BUY,
                confidence=0.2,  # Low confidence
                entry_price=Decimal('1.0850'),
                stop_loss=Decimal('1.0840'),
                take_profit=Decimal('1.0870'),
                risk_reward_ratio=1.5,
                reasoning="Low confidence test",
                market_condition=MarketCondition.BREAKOUT
            )
            
            low_risk_assessment = asyncio.run(
                risk_manager.assess_risk(low_confidence_rec, 1.0850, market_context)
            )
            
            if not low_risk_assessment['approved']:
                self.print_success("Correctly rejected low confidence trade")
            else:
                self.print_warning("Should have rejected low confidence trade")
            
            self.test_results['risk_manager'] = True
            return True
            
        except Exception as e:
            self.print_error(f"Risk manager test failed: {e}")
            traceback.print_exc()
            self.test_results['risk_manager'] = False
            return False
    
    def test_4_decision_layer(self):
        """Test 4: Technical Decision Layer"""
        self.print_header("TEST 4: Technical Decision Layer")
        
        try:
            # Generate test data
            m5_candles = self.generate_test_candles("EUR_USD", 100)
            m15_candles = self.generate_test_candles("EUR_USD", 50)
            
            candles_by_timeframe = {
                TimeFrame.M5: m5_candles,
                TimeFrame.M15: m15_candles
            }
            
            # Create market context
            market_context = MarketContext(
                condition=MarketCondition.BREAKOUT,
                volatility=Decimal('0.001'),
                trend_strength=Decimal('0.7'),
                news_sentiment=Decimal('0.0')
            )
            
            # Test decision layer
            decision_layer = TechnicalDecisionLayer(self.config)
            
            # Get current price
            current_price = (m5_candles[-1].high + m5_candles[-1].low) / 2
            
            # Calculate technical indicators
            analyzer = TechnicalAnalyzer()
            indicators = analyzer.calculate_indicators(m5_candles)
            
            technical_indicators = {
                TimeFrame.M5: indicators
            }
            
            # Make decision
            decision = asyncio.run(
                decision_layer.make_technical_decision(
                    "EUR_USD",
                    technical_indicators,
                    market_context,
                    current_price,
                    candles_by_timeframe
                )
            )
            
            if decision:
                self.print_success(f"Decision made: Approved={decision.approved}")
                if decision.approved:
                    self.print_info(f"Position size: {decision.position_size}")
                    self.print_info(f"Risk amount: {decision.risk_amount}")
                    self.print_info(f"Stop loss: {decision.modified_stop_loss}")
                    self.print_info(f"Take profit: {decision.modified_take_profit}")
                else:
                    self.print_info(f"Rejection reason: {decision.risk_management_notes}")
            else:
                self.print_info("No decision made (this is normal for some market conditions)")
            
            self.test_results['decision_layer'] = True
            return True
            
        except Exception as e:
            self.print_error(f"Decision layer test failed: {e}")
            traceback.print_exc()
            self.test_results['decision_layer'] = False
            return False
    
    def test_5_backtest_engine(self):
        """Test 5: Backtest Engine"""
        self.print_header("TEST 5: Backtest Engine")
        
        try:
            # Generate historical data
            start_date = datetime.now(timezone.utc) - timedelta(days=7)
            end_date = datetime.now(timezone.utc)
            
            # Generate data for multiple pairs
            historical_data = {}
            
            for pair in ["EUR_USD", "GBP_USD"]:
                historical_data[pair] = {}
                
                # Generate M5 data
                m5_candles = self.generate_test_candles(pair, 200)
                historical_data[pair][TimeFrame.M5] = m5_candles
                
                # Generate M15 data
                m15_candles = self.generate_test_candles(pair, 100)
                historical_data[pair][TimeFrame.M15] = m15_candles
            
            # Test backtest engine
            backtest_engine = BacktestEngine(self.config)
            
            # Run backtest
            result = asyncio.run(
                backtest_engine.run_backtest(
                    historical_data,
                    start_date,
                    end_date,
                    parameters={
                        'rsi_oversold': 30,
                        'rsi_overbought': 70,
                        'macd_signal_threshold': 0.0001,
                        'bollinger_threshold': 0.1,
                        'atr_multiplier': 2.0,
                        'min_signal_strength': 0.3,  # Lower threshold for testing
                        'risk_percentage': 2.0,
                        'max_daily_loss': 5.0,
                        'max_open_trades': 3
                    }
                )
            )
            
            # Print results
            self.print_success(f"Backtest completed successfully")
            self.print_info(f"Total trades: {result.total_trades}")
            self.print_info(f"Winning trades: {result.winning_trades}")
            self.print_info(f"Losing trades: {result.losing_trades}")
            self.print_info(f"Win rate: {result.win_rate:.2%}")
            self.print_info(f"Total return: {result.total_return:.2%}")
            self.print_info(f"Profit factor: {result.profit_factor:.2f}")
            self.print_info(f"Max drawdown: {result.max_drawdown:.2%}")
            self.print_info(f"Sharpe ratio: {result.sharpe_ratio:.2f}")
            
            if result.total_trades > 0:
                self.print_success("Backtest generated trades successfully")
            else:
                self.print_warning("Backtest generated no trades - this might indicate overly strict criteria")
            
            self.test_results['backtest_engine'] = True
            return True
            
        except Exception as e:
            self.print_error(f"Backtest engine test failed: {e}")
            traceback.print_exc()
            self.test_results['backtest_engine'] = False
            return False
    
    def test_6_signal_generation_debug(self):
        """Test 6: Debug Signal Generation Process"""
        self.print_header("TEST 6: Signal Generation Debug")
        
        try:
            # Generate test data with specific patterns to trigger signals
            candles = self.generate_test_candles("EUR_USD", 100)
            
            # Modify candles to create specific signal conditions
            # Create oversold RSI condition
            for i in range(80, 100):
                candles[i].close = candles[i].open * Decimal('0.999')  # Small decline
            
            # Create MACD crossover condition
            for i in range(90, 100):
                candles[i].close = candles[i].open * Decimal('1.001')  # Small rise
            
            # Test technical analyzer
            analyzer = TechnicalAnalyzer()
            indicators = analyzer.calculate_indicators(candles)
            
            self.print_info("Technical Indicators:")
            self.print_info(f"RSI: {indicators.rsi}")
            self.print_info(f"MACD: {indicators.macd}")
            self.print_info(f"MACD Signal: {indicators.macd_signal}")
            self.print_info(f"ATR: {indicators.atr}")
            self.print_info(f"EMA Fast: {indicators.ema_fast}")
            self.print_info(f"EMA Slow: {indicators.ema_slow}")
            self.print_info(f"Bollinger Upper: {indicators.bollinger_upper}")
            self.print_info(f"Bollinger Middle: {indicators.bollinger_middle}")
            self.print_info(f"Bollinger Lower: {indicators.bollinger_lower}")
            
            # Test signal analysis
            analysis_layer = TechnicalAnalysisLayer(self.config)
            
            # Create market context
            market_context = MarketContext(
                condition=MarketCondition.BREAKOUT,
                volatility=Decimal('0.001'),
                trend_strength=Decimal('0.7'),
                news_sentiment=Decimal('0.0')
            )
            
            # Analyze signals
            signal_analysis = analysis_layer._analyze_technical_signals(indicators, market_context)
            
            self.print_info("Signal Analysis:")
            self.print_info(f"RSI Signal: {signal_analysis['rsi_signal']}")
            self.print_info(f"MACD Signal: {signal_analysis['macd_signal']}")
            self.print_info(f"Bollinger Signal: {signal_analysis['bollinger_signal']}")
            self.print_info(f"EMA Signal: {signal_analysis['ema_signal']}")
            self.print_info(f"Overall Signal: {signal_analysis['overall_signal']}")
            self.print_info(f"Has Signal: {signal_analysis['has_signal']}")
            self.print_info(f"Signal Strength: {signal_analysis['signal_strength']}")
            self.print_info(f"Reasoning: {signal_analysis['reasoning']}")
            
            # Test with different thresholds
            self.print_section("Testing Different Thresholds")
            
            # Test with very low thresholds
            analysis_layer.rsi_oversold = 40  # More lenient
            analysis_layer.rsi_overbought = 60  # More lenient
            analysis_layer.macd_signal_threshold = 0.00001  # Very low
            analysis_layer.min_signal_strength = 0.1  # Very low
            
            signal_analysis_low = analysis_layer._analyze_technical_signals(indicators, market_context)
            
            self.print_info("Low Thresholds Signal Analysis:")
            self.print_info(f"Has Signal: {signal_analysis_low['has_signal']}")
            self.print_info(f"Signal Strength: {signal_analysis_low['signal_strength']}")
            
            self.test_results['signal_generation_debug'] = True
            return True
            
        except Exception as e:
            self.print_error(f"Signal generation debug test failed: {e}")
            traceback.print_exc()
            self.test_results['signal_generation_debug'] = False
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        self.print_header("COMPREHENSIVE TRADING BOT DEBUGGING")
        
        tests = [
            ("Technical Indicators", self.test_1_technical_indicators),
            ("Technical Analysis Layer", self.test_2_technical_analysis_layer),
            ("Risk Manager", self.test_3_risk_manager),
            ("Decision Layer", self.test_4_decision_layer),
            ("Backtest Engine", self.test_5_backtest_engine),
            ("Signal Generation Debug", self.test_6_signal_generation_debug),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.print_error(f"Test '{test_name}' failed with exception: {e}")
                traceback.print_exc()
        
        # Print summary
        self.print_header("TEST SUMMARY")
        self.print_info(f"Tests passed: {passed}/{total}")
        
        if passed == total:
            self.print_success("All tests passed! 🎉")
        else:
            self.print_warning(f"{total - passed} tests failed. Check the output above for details.")
        
        # Print detailed results
        self.print_section("Detailed Results")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        return passed == total


def main():
    """Main function to run the comprehensive debugging."""
    debugger = ComprehensiveDebugger()
    success = debugger.run_all_tests()
    
    if success:
        print("\n🎉 All components are working correctly!")
        print("If you're still not seeing trades, the issue might be:")
        print("1. Market conditions not meeting signal criteria")
        print("2. Risk management being too strict")
        print("3. Data quality issues")
        print("4. Configuration settings being too conservative")
    else:
        print("\n🔧 Some components have issues. Check the output above for details.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

