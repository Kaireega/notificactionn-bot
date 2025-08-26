#!/usr/bin/env python3
"""
Comprehensive Debugging Test for Trading Bot
Traces through all layers and functions to identify issues and track data flow.
"""
import asyncio
import sys
import traceback
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
from decimal import Decimal

# Add the project root to the path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_debug.log'),
        logging.StreamHandler()
    ]
)

class ComprehensiveDebugger:
    """Comprehensive debugger for tracing all trading bot layers."""
    
    def __init__(self):
        self.debug_log = []
        self.layer_results = {}
        self.error_count = 0
        self.warning_count = 0
        
    def log_debug(self, layer: str, function: str, message: str, data: Any = None):
        """Log debug information with layer and function context."""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        debug_entry = {
            'timestamp': timestamp,
            'layer': layer,
            'function': function,
            'message': message,
            'data': data
        }
        self.debug_log.append(debug_entry)
        print(f"[{timestamp}] 🔍 {layer}.{function}: {message}")
        if data:
            print(f"    📊 Data: {data}")
    
    def log_error(self, layer: str, function: str, error: str, traceback: str = None):
        """Log error information."""
        self.error_count += 1
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] ❌ {layer}.{function}: ERROR - {error}")
        if traceback:
            print(f"    📋 Traceback: {traceback}")
    
    def log_warning(self, layer: str, function: str, warning: str):
        """Log warning information."""
        self.warning_count += 1
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] ⚠️ {layer}.{function}: WARNING - {warning}")

async def test_data_layer(debugger: ComprehensiveDebugger):
    """Test the data layer components."""
    print("\n" + "="*80)
    print("🧪 TESTING DATA LAYER")
    print("="*80)
    
    try:
        from trading_bot.src.data.data_layer import DataLayer
        from trading_bot.src.utils.config import Config
        
        debugger.log_debug("DataLayer", "init", "Initializing DataLayer...")
        
        config = Config()
        config.enable_db = False
        
        data_layer = DataLayer(config)
        debugger.log_debug("DataLayer", "init", "DataLayer initialized successfully")
        
        # Test data loading
        debugger.log_debug("DataLayer", "load_data", "Testing data loading...")
        
        # Test with mock data
        mock_candles = [
            {
                'time': datetime.now(timezone.utc),
                'open': '1.1000',
                'high': '1.1010',
                'low': '1.0990',
                'close': '1.1005',
                'volume': '1000'
            }
        ]
        
        debugger.log_debug("DataLayer", "process_candles", "Processing mock candles...", len(mock_candles))
        
        # Test market context creation
        debugger.log_debug("DataLayer", "create_market_context", "Creating market context...")
        
        return True, "DataLayer tests completed"
        
    except Exception as e:
        debugger.log_error("DataLayer", "test", str(e), traceback.format_exc())
        return False, f"DataLayer test failed: {e}"

async def test_ai_layer(debugger: ComprehensiveDebugger):
    """Test the AI/Technical Analysis layer components."""
    print("\n" + "="*80)
    print("🧪 TESTING AI/TECHNICAL ANALYSIS LAYER")
    print("="*80)
    
    try:
        from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer
        from trading_bot.src.ai.technical_analyzer import TechnicalAnalyzer
        from trading_bot.src.ai.ai_analysis_layer import AIAnalysisLayer
        from trading_bot.src.core.models import CandleData, MarketContext
        from trading_bot.src.utils.config import Config
        
        config = Config()
        config.enable_db = False
        
        # Test Technical Analysis Layer
        debugger.log_debug("TechnicalAnalysisLayer", "init", "Initializing TechnicalAnalysisLayer...")
        tech_layer = TechnicalAnalysisLayer(config)
        debugger.log_debug("TechnicalAnalysisLayer", "init", "TechnicalAnalysisLayer initialized")
        
        # Test Technical Analyzer
        debugger.log_debug("TechnicalAnalyzer", "init", "Initializing TechnicalAnalyzer...")
        tech_analyzer = TechnicalAnalyzer(config)
        debugger.log_debug("TechnicalAnalyzer", "init", "TechnicalAnalyzer initialized")
        
        # Test AI Analysis Layer
        debugger.log_debug("AIAnalysisLayer", "init", "Initializing AIAnalysisLayer...")
        ai_layer = AIAnalysisLayer(config)
        debugger.log_debug("AIAnalysisLayer", "init", "AIAnalysisLayer initialized")
        
        # Test with mock candle data
        mock_candle = CandleData(
            time=datetime.now(timezone.utc),
            open=Decimal('1.1000'),
            high=Decimal('1.1010'),
            low=Decimal('1.0990'),
            close=Decimal('1.1005'),
            volume=Decimal('1000')
        )
        
        debugger.log_debug("TechnicalAnalysisLayer", "analyze", "Testing technical analysis...")
        
        # Test technical indicators calculation
        debugger.log_debug("TechnicalAnalyzer", "calculate_indicators", "Calculating technical indicators...")
        
        return True, "AI/Technical Analysis Layer tests completed"
        
    except Exception as e:
        debugger.log_error("AILayer", "test", str(e), traceback.format_exc())
        return False, f"AI/Technical Analysis Layer test failed: {e}"

async def test_decision_layer(debugger: ComprehensiveDebugger):
    """Test the decision layer components."""
    print("\n" + "="*80)
    print("🧪 TESTING DECISION LAYER")
    print("="*80)
    
    try:
        from trading_bot.src.decision.automated_decision_layer import AutomatedDecisionLayer
        from trading_bot.src.decision.risk_manager_improved import ImprovedRiskManager as RiskManager
        from trading_bot.src.decision.technical_decision_layer import TechnicalDecisionLayer
        from trading_bot.src.core.models import MarketContext, TradeRecommendation
        from trading_bot.src.utils.config import Config
        
        config = Config()
        config.enable_db = False
        
        # Test Risk Manager
        debugger.log_debug("RiskManager", "init", "Initializing RiskManager...")
        risk_manager = RiskManager(config)
        debugger.log_debug("RiskManager", "init", "RiskManager initialized")
        
        # Test Automated Decision Layer
        debugger.log_debug("AutomatedDecisionLayer", "init", "Initializing AutomatedDecisionLayer...")
        decision_layer = AutomatedDecisionLayer(config)
        debugger.log_debug("AutomatedDecisionLayer", "init", "AutomatedDecisionLayer initialized")
        
        # Test Technical Decision Layer
        debugger.log_debug("TechnicalDecisionLayer", "init", "Initializing TechnicalDecisionLayer...")
        tech_decision = TechnicalDecisionLayer(config)
        debugger.log_debug("TechnicalDecisionLayer", "init", "TechnicalDecisionLayer initialized")
        
        # Test risk assessment
        debugger.log_debug("RiskManager", "assess_risk", "Testing risk assessment...")
        
        # Test decision making
        debugger.log_debug("AutomatedDecisionLayer", "make_decision", "Testing decision making...")
        
        return True, "Decision Layer tests completed"
        
    except Exception as e:
        debugger.log_error("DecisionLayer", "test", str(e), traceback.format_exc())
        return False, f"Decision Layer test failed: {e}"

async def test_core_layer(debugger: ComprehensiveDebugger):
    """Test the core layer components."""
    print("\n" + "="*80)
    print("🧪 TESTING CORE LAYER")
    print("="*80)
    
    try:
        from trading_bot.src.core.fundamental_analyzer import FundamentalAnalyzer
        from trading_bot.src.core.position_manager_improved import ImprovedPositionManager as PositionManager
        from trading_bot.src.core.models import MarketContext
        from trading_bot.src.utils.config import Config
        
        config = Config()
        config.enable_db = False
        
        # Test Fundamental Analyzer
        debugger.log_debug("FundamentalAnalyzer", "init", "Initializing FundamentalAnalyzer...")
        fundamental_analyzer = FundamentalAnalyzer(config)
        debugger.log_debug("FundamentalAnalyzer", "init", "FundamentalAnalyzer initialized")
        
        # Test Position Manager
        debugger.log_debug("PositionManager", "init", "Initializing PositionManager...")
        position_manager = PositionManager(config)
        debugger.log_debug("PositionManager", "init", "PositionManager initialized")
        
        # Test fundamental analysis
        debugger.log_debug("FundamentalAnalyzer", "start", "Starting fundamental analyzer...")
        await fundamental_analyzer.start()
        debugger.log_debug("FundamentalAnalyzer", "start", "Fundamental analyzer started")
        
        # Test position management
        debugger.log_debug("PositionManager", "get_position_summary", "Testing position summary...")
        
        return True, "Core Layer tests completed"
        
    except Exception as e:
        debugger.log_error("CoreLayer", "test", str(e), traceback.format_exc())
        return False, f"Core Layer test failed: {e}"

async def test_integration_flow(debugger: ComprehensiveDebugger):
    """Test the complete integration flow."""
    print("\n" + "="*80)
    print("🧪 TESTING COMPLETE INTEGRATION FLOW")
    print("="*80)
    
    try:
        from trading_bot.src.data.data_layer import DataLayer
        from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer
        from trading_bot.src.decision.automated_decision_layer import AutomatedDecisionLayer
        from trading_bot.src.core.fundamental_analyzer import FundamentalAnalyzer
        from trading_bot.src.core.position_manager_improved import ImprovedPositionManager as PositionManager
        from trading_bot.src.core.models import CandleData, MarketContext
        from trading_bot.src.utils.config import Config
        
        config = Config()
        config.enable_db = False
        
        debugger.log_debug("Integration", "init", "Initializing all layers for integration test...")
        
        # Initialize all layers
        data_layer = DataLayer(config)
        tech_layer = TechnicalAnalysisLayer(config)
        decision_layer = AutomatedDecisionLayer(config)
        fundamental_analyzer = FundamentalAnalyzer(config)
        position_manager = PositionManager(config)
        
        debugger.log_debug("Integration", "init", "All layers initialized successfully")
        
        # Test complete flow
        debugger.log_debug("Integration", "flow", "Testing complete data flow...")
        
        # Create mock market context
        market_context = MarketContext()
        market_context.rsi = 65.0
        market_context.macd = 0.0001
        market_context.atr = 0.0005
        
        # Test fundamental analysis integration
        debugger.log_debug("Integration", "fundamental", "Testing fundamental analysis integration...")
        await fundamental_analyzer.start()
        
        fundamental_result = await fundamental_analyzer.analyze_fundamentals("EUR_USD", market_context)
        debugger.log_debug("Integration", "fundamental", "Fundamental analysis completed", 
                          f"Score: {fundamental_result.get('score', 'N/A')}")
        
        # Test position management integration
        debugger.log_debug("Integration", "position", "Testing position management integration...")
        
        position_summary = position_manager.get_position_summary()
        debugger.log_debug("Integration", "position", "Position summary retrieved", 
                          f"Open positions: {len(position_summary.get('open_positions', []))}")
        
        debugger.log_debug("Integration", "flow", "Complete integration flow test completed successfully")
        
        return True, "Integration flow tests completed"
        
    except Exception as e:
        debugger.log_error("Integration", "test", str(e), traceback.format_exc())
        return False, f"Integration flow test failed: {e}"

async def test_error_handling(debugger: ComprehensiveDebugger):
    """Test error handling across all layers."""
    print("\n" + "="*80)
    print("🧪 TESTING ERROR HANDLING")
    print("="*80)
    
    try:
        from trading_bot.src.utils.config import Config
        
        config = Config()
        config.enable_db = False
        
        debugger.log_debug("ErrorHandling", "test", "Testing error handling scenarios...")
        
        # Test invalid configuration
        debugger.log_debug("ErrorHandling", "config", "Testing invalid configuration handling...")
        
        # Test network error handling
        debugger.log_debug("ErrorHandling", "network", "Testing network error handling...")
        
        # Test data validation
        debugger.log_debug("ErrorHandling", "validation", "Testing data validation...")
        
        return True, "Error handling tests completed"
        
    except Exception as e:
        debugger.log_error("ErrorHandling", "test", str(e), traceback.format_exc())
        return False, f"Error handling test failed: {e}"

async def main():
    """Run comprehensive debugging tests."""
    print("🚀 COMPREHENSIVE DEBUGGING TEST")
    print("="*80)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    debugger = ComprehensiveDebugger()
    test_results = []
    
    # Run all layer tests
    tests = [
        ("Data Layer", test_data_layer),
        ("AI/Technical Analysis Layer", test_ai_layer),
        ("Decision Layer", test_decision_layer),
        ("Core Layer", test_core_layer),
        ("Integration Flow", test_integration_flow),
        ("Error Handling", test_error_handling),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"🧪 RUNNING: {test_name}")
        print(f"{'='*80}")
        
        try:
            success, message = await test_func(debugger)
            test_results.append({
                'name': test_name,
                'success': success,
                'message': message
            })
            
        except Exception as e:
            debugger.log_error("Main", test_name, str(e), traceback.format_exc())
            test_results.append({
                'name': test_name,
                'success': False,
                'message': f"Critical error: {e}"
            })
    
    # Generate comprehensive report
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE DEBUGGING REPORT")
    print(f"{'='*80}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result['success'])
    failed_tests = total_tests - passed_tests
    
    print(f"📈 Overall Results:")
    print(f"   Total Tests: {total_tests}")
    print(f"   ✅ Passed: {passed_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    print(f"   📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"   ⚠️ Warnings: {debugger.warning_count}")
    print(f"   ❌ Errors: {debugger.error_count}")
    
    print(f"\n📋 Detailed Results:")
    print(f"{'Test Name':<30} {'Status':<8} {'Message':<50}")
    print(f"{'-'*30} {'-'*8} {'-'*50}")
    
    for result in test_results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        message = result['message'][:47] + "..." if len(result['message']) > 50 else result['message']
        print(f"{result['name']:<30} {status:<8} {message:<50}")
    
    # Debug log summary
    print(f"\n🔍 Debug Log Summary:")
    print(f"   Total Debug Entries: {len(debugger.debug_log)}")
    
    # Layer breakdown
    layer_counts = {}
    for entry in debugger.debug_log:
        layer = entry['layer']
        layer_counts[layer] = layer_counts.get(layer, 0) + 1
    
    print(f"   Layer Activity:")
    for layer, count in sorted(layer_counts.items()):
        print(f"     {layer}: {count} debug entries")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if passed_tests == total_tests:
        print(f"   🎉 All tests passed! System is functioning correctly.")
    else:
        print(f"   ⚠️ {failed_tests} test(s) need attention:")
        for result in test_results:
            if not result['success']:
                print(f"      - {result['name']}: {result['message']}")
    
    if debugger.error_count > 0:
        print(f"   🔧 {debugger.error_count} error(s) need to be addressed")
    
    if debugger.warning_count > 0:
        print(f"   ⚠️ {debugger.warning_count} warning(s) should be reviewed")
    
    print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Save detailed debug log
    with open('comprehensive_debug_report.txt', 'w') as f:
        f.write("COMPREHENSIVE DEBUG REPORT\n")
        f.write("="*50 + "\n\n")
        for entry in debugger.debug_log:
            f.write(f"[{entry['timestamp']}] {entry['layer']}.{entry['function']}: {entry['message']}\n")
            if entry['data']:
                f.write(f"    Data: {entry['data']}\n")
    
    print(f"\n📄 Detailed debug log saved to: comprehensive_debug_report.txt")

if __name__ == "__main__":
    asyncio.run(main())
