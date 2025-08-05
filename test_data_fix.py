#!/usr/bin/env python3
"""
Test script to verify data layer fixes
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "trading_bot" / "src"))

from utils.config import Config
from data.data_layer import DataLayer

async def test_data_layer():
    """Test the data layer to ensure current price is available."""
    print("🧪 Testing Data Layer Fixes...")
    
    try:
        # Load configuration
        config = Config()
        print("✅ Configuration loaded")
        
        # Initialize data layer
        data_layer = DataLayer(config)
        print("✅ Data layer initialized")
        
        # Start data layer
        await data_layer.start()
        print("✅ Data layer started")
        
        # Test current price for each pair
        for pair in config.trading_pairs:
            print(f"\n📊 Testing {pair}...")
            
            # Get current price
            current_price = await data_layer.get_current_price(pair)
            print(f"   Current Price: {current_price}")
            
            # Get candles
            candles = await data_layer.get_candles(pair, config.timeframes[0], 10)
            print(f"   Candles available: {len(candles)}")
            
            # Get market context
            market_context = await data_layer.get_market_context(pair)
            print(f"   Market Condition: {market_context.condition.value}")
            
            if current_price:
                print(f"   ✅ {pair}: Current price available!")
            else:
                print(f"   ❌ {pair}: No current price available")
        
        # Test get_all_pairs_data
        print(f"\n📈 Testing get_all_pairs_data...")
        all_data = await data_layer.get_all_pairs_data()
        
        for pair, data in all_data.items():
            current_price = data.get('current_price')
            candles_count = len(data.get('candles', {}).get(config.timeframes[0].value, []))
            print(f"   {pair}: Price={current_price}, Candles={candles_count}")
        
        print("\n🎉 Data layer test completed!")
        
    except Exception as e:
        print(f"❌ Error testing data layer: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if 'data_layer' in locals():
            await data_layer.stop()
            print("✅ Data layer stopped")

if __name__ == "__main__":
    asyncio.run(test_data_layer()) 