#!/usr/bin/env python3
"""
Test signal generation logic.
"""
import sys
import os
from pathlib import Path
from decimal import Decimal
import pandas as pd

# Add the project root to the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.core.models import CandleData, TradeSignal, MarketContext, MarketCondition
from trading_bot.src.ai.technical_analyzer import TechnicalAnalyzer


def create_sample_candles():
    """Create sample candle data for testing."""
    candles = []
    base_price = 1.1000
    
    for i in range(100):
        # Create more volatile price movement to trigger signals
        if i < 50:
            # First half: downtrend to trigger oversold
            price_change = -0.0005 - (i * 0.0001)
        else:
            # Second half: uptrend to trigger overbought
            price_change = 0.0005 + ((i - 50) * 0.0001)
        
        current_price = base_price + price_change
        
        candle = CandleData(
            timestamp=pd.Timestamp.now() - pd.Timedelta(minutes=(100-i)*5),
            open=Decimal(str(current_price)),
            high=Decimal(str(current_price + 0.0002)),
            low=Decimal(str(current_price - 0.0002)),
            close=Decimal(str(current_price + price_change * 0.1)),
            volume=Decimal('1000')
        )
        candles.append(candle)
    
    return candles

def test_signal_generation():
    """Test signal generation logic."""
    print("🔧 Testing Signal Generation...")
    
    # Create sample candles
    candles = create_sample_candles()
    print(f"   ✅ Created {len(candles)} sample candles")
    
    # Initialize technical analyzer
    technical_analyzer = TechnicalAnalyzer()
    
    # Calculate indicators
    indicators = technical_analyzer.calculate_indicators(candles)
    print(f"   ✅ Technical indicators calculated")
    print(f"   📊 RSI: {indicators.rsi}")
    print(f"   📊 MACD: {indicators.macd}")
    print(f"   📊 MACD Signal: {indicators.macd_signal}")
    print(f"   📊 Bollinger Upper: {indicators.bollinger_upper}")
    print(f"   📊 Bollinger Lower: {indicators.bollinger_lower}")
    print(f"   📊 Bollinger Middle: {indicators.bollinger_middle}")
    print(f"   📊 EMA Fast: {indicators.ema_fast}")
    print(f"   📊 EMA Slow: {indicators.ema_slow}")
    
    # Test signal generation logic
    rsi_oversold = 30
    rsi_overbought = 70
    macd_signal_threshold = 0.0001
    bollinger_threshold = 0.1
    
    signals = {
        'rsi_signal': None,
        'macd_signal': None,
        'bollinger_signal': None,
        'ema_signal': None,
        'overall_signal': None,
        'has_signal': False,
        'signal_strength': 0.0,
        'reasoning': []
    }
    
    # RSI Analysis
    if indicators.rsi is not None:
        if indicators.rsi < rsi_oversold:
            signals['rsi_signal'] = TradeSignal.BUY
            signals['reasoning'].append(f"RSI oversold ({indicators.rsi:.2f})")
        elif indicators.rsi > rsi_overbought:
            signals['rsi_signal'] = TradeSignal.SELL
            signals['reasoning'].append(f"RSI overbought ({indicators.rsi:.2f})")
    
    # MACD Analysis
    if (indicators.macd is not None and indicators.macd_signal is not None and 
        abs(indicators.macd - indicators.macd_signal) > macd_signal_threshold):
        
        if indicators.macd > indicators.macd_signal:
            signals['macd_signal'] = TradeSignal.BUY
            signals['reasoning'].append("MACD bullish crossover")
        else:
            signals['macd_signal'] = TradeSignal.SELL
            signals['reasoning'].append("MACD bearish crossover")
    
    # Bollinger Bands Analysis
    if (indicators.bollinger_upper is not None and indicators.bollinger_lower is not None and 
        indicators.bollinger_middle is not None):
        
        # Calculate price position relative to bands
        price = indicators.bollinger_middle  # Use middle band as reference
        upper_distance = (indicators.bollinger_upper - price) / price
        lower_distance = (price - indicators.bollinger_lower) / price
        
        if upper_distance < bollinger_threshold:
            signals['bollinger_signal'] = TradeSignal.SELL
            signals['reasoning'].append("Price near upper Bollinger band")
        elif lower_distance < bollinger_threshold:
            signals['bollinger_signal'] = TradeSignal.BUY
            signals['reasoning'].append("Price near lower Bollinger band")
    
    # EMA Analysis
    if (indicators.ema_fast is not None and indicators.ema_slow is not None):
        if indicators.ema_fast > indicators.ema_slow:
            signals['ema_signal'] = TradeSignal.BUY
            signals['reasoning'].append("Fast EMA above slow EMA")
        else:
            signals['ema_signal'] = TradeSignal.SELL
            signals['reasoning'].append("Fast EMA below slow EMA")
    
    # Determine overall signal
    buy_signals = sum(1 for signal in [signals['rsi_signal'], signals['macd_signal'], 
                                     signals['bollinger_signal'], signals['ema_signal']] 
                    if signal == TradeSignal.BUY)
    sell_signals = sum(1 for signal in [signals['rsi_signal'], signals['macd_signal'], 
                                      signals['bollinger_signal'], signals['ema_signal']] 
                     if signal == TradeSignal.SELL)
    
    print(f"   📊 Individual signals:")
    print(f"      RSI: {signals['rsi_signal']}")
    print(f"      MACD: {signals['macd_signal']}")
    print(f"      Bollinger: {signals['bollinger_signal']}")
    print(f"      EMA: {signals['ema_signal']}")
    print(f"   📊 Buy signals: {buy_signals}")
    print(f"   📊 Sell signals: {sell_signals}")
    print(f"   📊 Reasoning: {signals['reasoning']}")
    
    if buy_signals > sell_signals and buy_signals >= 2:
        signals['overall_signal'] = TradeSignal.BUY
        signals['has_signal'] = True
        signals['signal_strength'] = buy_signals / 4.0
        print(f"   ✅ BUY signal generated with strength {signals['signal_strength']:.2f}")
    elif sell_signals > buy_signals and sell_signals >= 2:
        signals['overall_signal'] = TradeSignal.SELL
        signals['has_signal'] = True
        signals['signal_strength'] = sell_signals / 4.0
        print(f"   ✅ SELL signal generated with strength {signals['signal_strength']:.2f}")
    else:
        print(f"   ❌ No signal generated (need at least 2 agreeing signals)")

if __name__ == "__main__":
    test_signal_generation()
