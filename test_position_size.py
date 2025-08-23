#!/usr/bin/env python3
"""
Test script to debug position size calculation.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
from decimal import Decimal
import pandas as pd

# Add the project root to the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.core.models import TimeFrame, CandleData, MarketContext, MarketCondition, TradeRecommendation, TradeSignal
from trading_bot.src.decision.risk_manager import RiskManager
from infrastructure.instrument_collection import InstrumentCollection


async def test_position_size():
    """Test position size calculation."""
    
    print("🔍 Testing Position Size Calculation")
    print("=" * 50)
    
    # Load configuration
    config = Config()
    
    # Test instrument loading
    print("📊 Step 1: Loading Instruments")
    print("-" * 30)
    
    try:
        ic = InstrumentCollection()
        ic.LoadInstrumentsDB()
        
        print(f"   ✅ Instruments loaded: {len(ic.instruments_dict)} instruments")
        
        # Check if EUR_USD is available
        eur_usd_instrument = ic.instruments_dict.get("EUR_USD")
        if eur_usd_instrument:
            print(f"   ✅ EUR_USD instrument found")
            print(f"   - Pip Location: {eur_usd_instrument.pipLocation}")
            print(f"   - Display Name: {eur_usd_instrument.displayName}")
        else:
            print(f"   ❌ EUR_USD instrument NOT found")
            
    except Exception as e:
        print(f"   ❌ Error loading instruments: {e}")
        return
    
    # Create a test recommendation
    print("\n📊 Step 2: Creating Test Recommendation")
    print("-" * 30)
    
    recommendation = TradeRecommendation(
        pair="EUR_USD",
        signal=TradeSignal.SELL,
        entry_price=Decimal("1.134815"),
        stop_loss=Decimal("1.135400"),
        take_profit=Decimal("1.133643"),
        confidence=0.8,
        market_condition=MarketCondition.BREAKOUT,
        reasoning="Test recommendation",
        risk_reward_ratio=2.0
    )
    
    print(f"   ✅ Test recommendation created")
    print(f"   - Entry Price: {recommendation.entry_price}")
    print(f"   - Stop Loss: {recommendation.stop_loss}")
    print(f"   - Take Profit: {recommendation.take_profit}")
    
    # Test position size calculation
    print("\n📊 Step 3: Testing Position Size Calculation")
    print("-" * 30)
    
    try:
        risk_manager = RiskManager(config)
        
        # Create a mock risk assessment
        risk_assessment = {
            'approved': True,
            'reason': 'Test assessment',
            'score': 0.8
        }
        
        # Calculate position size
        position_result = await risk_manager.calculate_position_size(recommendation, risk_assessment)
        
        print(f"   ✅ Position size calculation completed")
        print(f"   - Size: {position_result['size']}")
        print(f"   - Risk Amount: {position_result['risk_amount']}")
        print(f"   - Stop Loss: {position_result['stop_loss']}")
        print(f"   - Take Profit: {position_result['take_profit']}")
        
        if position_result['size'] > 0:
            print(f"   🎉 SUCCESS: Position size > 0")
        else:
            print(f"   ❌ ISSUE: Position size = 0")
            
    except Exception as e:
        print(f"   ❌ Error calculating position size: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🔍 POSITION SIZE TEST SUMMARY")
    print("=" * 50)


async def main():
    """Main function."""
    try:
        await test_position_size()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

