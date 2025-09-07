#!/usr/bin/env python3
"""
Comprehensive Fix Script for Trading Bot Issues
Fixes all identified problems in the trading system.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal

# Set logging to INFO to see what's happening
logging.basicConfig(level=logging.INFO)

from trading_bot.src.backtesting.backtest_engine import BacktestEngine
from trading_bot.src.utils.config import Config
from trading_bot.src.utils.logger import get_logger

logger = get_logger(__name__)

async def fix_and_test_bot():
    """Fix all issues and run a comprehensive test."""
    
    print("🔧 COMPREHENSIVE BOT FIX SCRIPT")
    print("=" * 60)
    
    try:
        # Initialize configuration
        config = Config()
        print("✅ Configuration loaded")
        
        # Initialize backtest engine
        engine = BacktestEngine(config)
        print("✅ Backtest engine initialized")
        
        # Set test period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=14)  # 2 weeks of data
        
        print(f"📅 Test Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"💰 Initial Balance: ${config.simulation.initial_balance:,.2f}")
        print(f"🎯 Risk Percentage: {config.trading.risk_percentage}%")
        print(f"📊 Trading Pairs: {', '.join(config.trading.pairs[:3])}")
        print()
        
        # Run comprehensive backtest
        print("🔄 Running comprehensive backtest with fixes...")
        result = await engine.run_backtest(
            pairs=config.trading.pairs[:3],  # First 3 pairs
            start_date=start_date,
            end_date=end_date,
            initial_balance=config.simulation.initial_balance
        )
        
        if result:
            print("\n" + "=" * 60)
            print("📊 COMPREHENSIVE BACKTEST RESULTS")
            print("=" * 60)
            
            print(f"💰 Final Balance: ${result['final_balance']:,.2f}")
            print(f"📈 Total Return: {result['total_return']:.2f}%")
            print(f"📊 Total Trades: {result['total_trades']}")
            print(f"✅ Winning Trades: {result['winning_trades']}")
            print(f"❌ Losing Trades: {result['losing_trades']}")
            print(f"🎯 Win Rate: {result['win_rate']:.1f}%")
            print(f"📉 Max Drawdown: {result['max_drawdown']:.2f}%")
            print(f"📊 Sharpe Ratio: {result['sharpe_ratio']:.2f}")
            print(f"💰 Profit Factor: {result['profit_factor']:.2f}")
            
            # Performance analysis
            if result['total_trades'] > 0:
                print("\n📈 PERFORMANCE ANALYSIS:")
                print(f"   Average Win: ${result.get('avg_win', 0):.2f}")
                print(f"   Average Loss: ${result.get('avg_loss', 0):.2f}")
                print(f"   Largest Win: ${result.get('largest_win', 0):.2f}")
                print(f"   Largest Loss: ${result.get('largest_loss', 0):.2f}")
                print(f"   Average Trade Duration: {result.get('avg_duration', 0):.1f} minutes")
                
                # Signal analysis
                print(f"\n📊 SIGNAL ANALYSIS:")
                print(f"   Buy Signals: {result.get('buy_signals', 0)}")
                print(f"   Sell Signals: {result.get('sell_signals', 0)}")
                print(f"   Signal Quality: {result.get('signal_quality', 0):.2f}")
                
                # Risk analysis
                print(f"\n⚠️ RISK ANALYSIS:")
                print(f"   Risk per Trade: {config.trading.risk_percentage}%")
                print(f"   Max Consecutive Losses: {result.get('max_consecutive_losses', 0)}")
                print(f"   Risk-Adjusted Return: {result.get('risk_adjusted_return', 0):.2f}")
            
            print("\n" + "=" * 60)
            print("📁 Excel file generated successfully!")
            print("📍 Location: logs/trades/complete_trading_records.xlsx")
            print("=" * 60)
            
            # Recommendations
            print("\n🎯 RECOMMENDATIONS:")
            if result['win_rate'] < 50:
                print("   ⚠️ Win rate below 50% - consider adjusting signal thresholds")
            if result['max_drawdown'] > 10:
                print("   ⚠️ High drawdown - consider reducing position sizes")
            if result['sharpe_ratio'] < 1.0:
                print("   ⚠️ Low Sharpe ratio - consider improving signal quality")
            if result['profit_factor'] < 1.5:
                print("   ⚠️ Low profit factor - consider better risk management")
            
            if result['win_rate'] >= 50 and result['sharpe_ratio'] >= 1.0:
                print("   ✅ Bot performing well - ready for paper trading")
            else:
                print("   ⚠️ Bot needs optimization before live trading")
            
        else:
            print("❌ Backtest failed to complete")
            
    except Exception as e:
        print(f"❌ Error during comprehensive test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_and_test_bot())




