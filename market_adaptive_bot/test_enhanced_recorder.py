#!/usr/bin/env python3
"""
Test script for Enhanced Excel Trade Recorder
"""
import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.models import (
    TradeRecommendation, TradeDecision, MarketContext, 
    TechnicalIndicators, CandleData, TimeFrame, MarketCondition,
    TradeSignal
)
from utils.config import Config
from ai.technical_analyzer import TechnicalAnalyzer
from decision.enhanced_excel_trade_recorder import EnhancedExcelTradeRecorder


async def test_enhanced_recorder():
    """Test the enhanced Excel trade recorder."""
    
    print("🧪 Testing Enhanced Excel Trade Recorder...")
    
    try:
        # Initialize config
        config = Config()
        
        # Initialize components
        recorder = EnhancedExcelTradeRecorder(config)
        technical_analyzer = TechnicalAnalyzer()
        
        # Create test data
        market_context = MarketContext(
            condition=MarketCondition.BREAKOUT,
            volatility=0.02,
            trend_strength=0.8,
            key_levels={"support": 1.2000, "resistance": 1.2200}
        )
        
        # Calculate technical indicators using the existing technicals/indicators.py
        indicators = technical_analyzer.calculate_indicators(candles)
        
        # Create candles
        candles = [
            CandleData(
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                open=Decimal("1.2150"),
                high=Decimal("1.2160"),
                low=Decimal("1.2140"),
                close=Decimal("1.2155"),
                volume=Decimal("1000"),
                pair="EUR_USD",
                timeframe=TimeFrame.M5
            )
            for i in range(20, 0, -1)
        ]
        
        # Create trade recommendation
        recommendation = TradeRecommendation(
            pair="EUR_USD",
            signal=TradeSignal.BUY,
            entry_price=Decimal("1.2155"),
            stop_loss=Decimal("1.2130"),
            take_profit=Decimal("1.2180"),
            confidence=0.85,
            market_condition=MarketCondition.BREAKOUT,
            reasoning="Strong breakout signal with RSI confirmation",
            risk_reward_ratio=2.5,
            estimated_hold_time=timedelta(hours=2)
        )
        
        # Create trade decision
        decision = TradeDecision(
            recommendation=recommendation,
            approved=True,
            position_size=Decimal("10000"),
            risk_amount=Decimal("250"),
            modified_stop_loss=Decimal("1.2130"),
            modified_take_profit=Decimal("1.2180"),
            risk_management_notes="Position size calculated based on 1% risk per trade",
            timestamp=datetime.utcnow()
        )
        
        # Test data
        technical_indicators = {TimeFrame.M5: indicators}
        candles_by_timeframe = {TimeFrame.M5: candles}
        ai_outputs = {
            "prompt": "Analyze EUR_USD for breakout opportunities",
            "raw_response": "Strong buy signal detected",
            "parsed_data": {"signal": "buy", "confidence": 0.85},
            "confidence": 0.85,
            "signal": "buy",
            "reasoning": "Strong breakout signal with RSI confirmation",
            "market_condition": "breakout",
            "entry_price": 1.2155,
            "stop_loss": 1.2130,
            "take_profit": 1.2180,
            "risk_reward_ratio": 2.5,
            "estimated_hold_time_minutes": 120,
            "model": "gpt-4",
            "temperature": 0.3,
            "max_tokens": 1000
        }
        multi_timeframe_analysis = {
            TimeFrame.M5: {
                "signal_type": "buy",
                "signal_strength": 0.85,
                "trend_direction": 0.8,
                "momentum": 0.7,
                "volatility": 0.02,
                "technical_score": 0.85,
                "entry_price": 1.2155,
                "stop_loss": 1.2130,
                "take_profit": 1.2180,
                "risk_reward_ratio": 2.5,
                "confidence": 0.85,
                "weight": 0.25
            }
        }
        risk_assessment = {
            "approved": True,
            "reason": "All risk checks passed",
            "position_size": {"size": 10000, "risk_amount": 250},
            "daily_loss_check": True,
            "correlation_check": True,
            "max_trades_check": True,
            "volatility_check": True,
            "market_hours_check": True,
            "notes": "Position size calculated based on 1% risk per trade"
        }
        raw_data = {
            "timeframe": "M5",
            "candle_count": 20,
            "price_data": [1.2155] * 20,
            "volume_data": [1000] * 20,
            "market_context_raw": market_context.__dict__,
            "technical_analysis_raw": indicators.__dict__,
            "news_data": [],
            "economic_data": [],
            "sentiment_data": {}
        }
        
        # Record the trade
        recorder.record_complete_trade_decision(
            decision=decision,
            market_context=market_context,
            technical_indicators=technical_indicators,
            candles_by_timeframe=candles_by_timeframe,
            ai_outputs=ai_outputs,
            multi_timeframe_analysis=multi_timeframe_analysis,
            risk_assessment=risk_assessment,
            raw_data=raw_data
        )
        
        # Force write to Excel
        recorder._write_to_excel()
        
        print("✅ Enhanced Excel Trade Recorder test completed successfully!")
        print(f"📊 Excel file created at: {recorder.excel_file}")
        print("📋 The file contains 7 sheets with comprehensive trade data:")
        print("   • Trades - Final trade decisions")
        print("   • Market_Conditions - Market context")
        print("   • Technical_Indicators - All technical indicators")
        print("   • AI_Outputs - Complete AI prompts and responses")
        print("   • Multi_Timeframe_Analysis - Multi-timeframe analysis")
        print("   • Risk_Assessment - Risk management decisions")
        print("   • Raw_Data - Raw market data")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_enhanced_recorder()) 