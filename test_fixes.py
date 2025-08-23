#!/usr/bin/env python3
"""
Simple test script to verify the fixes work correctly.
"""
import asyncio
import sys
from pathlib import Path

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
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import numpy as np


def generate_test_candles(pair: str = "EUR_USD", count: int = 100) -> list[CandleData]:
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


async def test_fixed_components():
    """Test the fixed components."""
    print("🔧 Testing Fixed Components")
    print("=" * 50)
    
    # Initialize config
    config = Config()
    
    # Generate test data
    candles = generate_test_candles("EUR_USD", 100)
    
    # Test 1: Technical Analysis Layer
    print("\n1. Testing Technical Analysis Layer...")
    analysis_layer = TechnicalAnalysisLayer(config)
    
    candles_by_timeframe = {
        TimeFrame.M5: candles
    }
    
    market_context = MarketContext(
        condition=MarketCondition.BREAKOUT,
        volatility=Decimal('0.001'),
        trend_strength=Decimal('0.7'),
        news_sentiment=Decimal('0.0')
    )
    
    recommendation, indicators = await analysis_layer.analyze_multiple_timeframes(
        "EUR_USD", candles_by_timeframe, market_context
    )
    
    if recommendation:
        print(f"✅ Recommendation generated: {recommendation.signal.value}")
        print(f"   Confidence: {recommendation.confidence:.2f}")
        print(f"   Entry: {recommendation.entry_price}")
        print(f"   SL: {recommendation.stop_loss}")
        print(f"   TP: {recommendation.take_profit}")
    else:
        print("❌ No recommendation generated")
        return False
    
    # Test 2: Risk Manager
    print("\n2. Testing Risk Manager...")
    risk_manager = RiskManager(config)
    
    current_price = float(recommendation.entry_price)
    risk_assessment = await risk_manager.assess_risk(recommendation, current_price, market_context)
    
    print(f"Risk assessment: {risk_assessment}")
    
    if risk_assessment['approved']:
        print("✅ Risk assessment approved")
        
        # Calculate position size
        position_size = await risk_manager.calculate_position_size(recommendation, risk_assessment)
        print(f"Position size: {position_size}")
    else:
        print(f"❌ Risk assessment rejected: {risk_assessment['reason']}")
        return False
    
    # Test 3: Decision Layer
    print("\n3. Testing Decision Layer...")
    decision_layer = TechnicalDecisionLayer(config)
    
    technical_indicators = {
        TimeFrame.M5: indicators
    }
    
    decision = await decision_layer.make_technical_decision(
        "EUR_USD",
        technical_indicators,
        market_context,
        Decimal(str(current_price)),
        candles_by_timeframe
    )
    
    if decision and decision.approved:
        print("✅ Decision approved")
        print(f"   Position size: {decision.position_size}")
        print(f"   Risk amount: {decision.risk_amount}")
    else:
        print("❌ Decision rejected")
        if decision:
            print(f"   Reason: {decision.risk_management_notes}")
        return False
    
    # Test 4: Backtest Engine
    print("\n4. Testing Backtest Engine...")
    backtest_engine = BacktestEngine(config)
    
    # Generate historical data
    start_date = datetime.now(timezone.utc) - timedelta(days=1)
    end_date = datetime.now(timezone.utc)
    
    historical_data = {
        "EUR_USD": {
            TimeFrame.M5: candles
        }
    }
    
    result = await backtest_engine.run_backtest(
        historical_data,
        start_date,
        end_date,
        parameters={
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_signal_threshold': 0.0001,
            'bollinger_threshold': 0.1,
            'atr_multiplier': 2.0,
            'min_signal_strength': 0.2,  # Very lenient
            'risk_percentage': 2.0,
            'max_daily_loss': 5.0,
            'max_open_trades': 3
        }
    )
    
    print(f"✅ Backtest completed")
    print(f"   Total trades: {result.total_trades}")
    print(f"   Win rate: {result.win_rate:.2%}")
    print(f"   Total return: {result.total_return:.2%}")
    
    if result.total_trades > 0:
        print("🎉 SUCCESS: Bot is now generating trades!")
        return True
    else:
        print("⚠️ No trades generated - may need further tuning")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_fixed_components())
    
    if success:
        print("\n🎉 All fixes working correctly!")
        print("The bot should now be able to generate trades in both backtesting and live sessions.")
    else:
        print("\n🔧 Some issues remain. Check the output above for details.")
    
    sys.exit(0 if success else 1)

