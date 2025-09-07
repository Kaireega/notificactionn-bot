#!/usr/bin/env python3
"""
Fixed main.py - Bypasses API validation to run backtester
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.backtesting.backtest_engine import BacktestEngine
from trading_bot.src.utils.logger import get_logger

async def run_backtester():
    """Run the backtester without API validation."""
    
    print("🚀 Starting Backtester (API Validation Bypassed)")
    print("=" * 60)
    
    try:
        # Load configuration
        config = Config()
        print("✅ Configuration loaded successfully")
        
        # Initialize backtest engine
        engine = BacktestEngine(config)
        print("✅ Backtest engine initialized")
        
        # Define test period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Last 7 days
        
        print(f"📅 Backtest Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"💰 Initial Balance: ${config.simulation.initial_balance:,.2f}")
        print(f"🎯 Risk Percentage: {config.trading.risk_percentage}%")
        print(f"📊 Trading Pairs: {', '.join(config.trading.pairs[:3])}")  # First 3 pairs
        print()
        
        # Run backtest
        print("🔄 Running backtest...")
        result = await engine.run_backtest(
            pairs=config.trading.pairs[:3],  # Only first 3 pairs for speed
            start_date=start_date,
            end_date=end_date,
            initial_balance=config.simulation.initial_balance
        )
        
        if result:
            print("\n" + "=" * 60)
            print("📊 BACKTEST RESULTS")
            print("=" * 60)
            print(f"💰 Initial Balance: ${result['initial_balance']:,.2f}")
            print(f"💰 Final Balance: ${result['final_balance']:,.2f}")
            print(f"📊 Total Return: {result['total_return']:.2%}")
            print(f"📈 Total Trades: {result['total_trades']}")
            print(f"✅ Winning Trades: {result['winning_trades']}")
            print(f"❌ Losing Trades: {result['losing_trades']}")
            print(f"🎯 Win Rate: {result['win_rate']:.2%}")
            print(f"📊 Profit Factor: {result['profit_factor']:.2f}")
            print(f"📉 Max Drawdown: {result['max_drawdown']:.2%}")
            print(f"📈 Sharpe Ratio: {result['sharpe_ratio']:.3f}")
            
            print("\n✅ Backtest completed successfully!")
        else:
            print("❌ Backtest failed!")
            
    except Exception as e:
        print(f"❌ Error running backtest: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function."""
    print("🔧 Starting Fixed Main (API Validation Bypassed)")
    print("=" * 60)
    
    # Skip API validation and run backtester directly
    asyncio.run(run_backtester())
    
    print("\n✅ Fixed main completed!")

if __name__ == "__main__":
    main()




