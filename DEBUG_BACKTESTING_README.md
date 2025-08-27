# Debug Backtesting System

## Overview

The Debug Backtesting System provides comprehensive debugging and analysis capabilities for the trading bot's backtesting functionality. It offers extensive logging, detailed trade analysis, performance tracking, and debugging tools to help identify issues and optimize trading strategies.

## Features

### 🔍 Comprehensive Debugging
- **Detailed Logging**: Every step of the backtesting process is logged with timestamps
- **Error Tracking**: All errors and warnings are captured and categorized
- **Performance Timing**: Detailed timing analysis for each component
- **Signal Analysis**: Track signal generation, filtering, and execution

### 📊 Enhanced Analytics
- **Performance Metrics**: Standard metrics plus advanced risk analysis
- **Risk Management**: Comprehensive risk checks and analysis
- **Trade Analysis**: Detailed breakdown by currency pair, signal type, and timeframe
- **Drawdown Analysis**: Maximum drawdown calculation and analysis

### 📈 Visualization
- **Equity Curves**: Visual representation of account balance over time
- **Drawdown Charts**: Graphical analysis of drawdown periods
- **Trade Distribution**: Histogram of trade P&L distribution
- **Performance Charts**: Breakdown by pair and signal type

### 📄 Reporting
- **JSON Reports**: Comprehensive reports in JSON format
- **Debug Logs**: Detailed logs with different verbosity levels
- **Data Quality Reports**: Validation of historical data quality
- **Analysis Reports**: Performance, risk, and signal analysis

## Components

### 1. DebugBacktestEngine
The core debugging engine that extends the standard backtesting functionality with comprehensive logging and analysis.

**Key Features:**
- Enhanced trade records with debugging information
- Performance timing for each component
- Risk check validation
- Signal tracking and analysis
- Memory usage monitoring

### 2. DebugBacktestingRunner
A comprehensive runner that orchestrates the entire debug backtesting process.

**Key Features:**
- Historical data loading and validation
- Comprehensive analysis generation
- Chart generation
- Report creation
- Command-line interface

### 3. DebugBacktestingTester
A test suite for validating the debug backtesting functionality.

**Key Features:**
- Mock data generation
- Performance testing
- Risk analysis testing
- Signal analysis testing

## Usage

### Basic Usage

```python
from trading_bot.src.backtesting.debug_backtest_engine import DebugBacktestEngine
from trading_bot.src.utils.config import Config

# Create debug engine
config = Config()
debug_engine = DebugBacktestEngine(config, debug_level="DETAILED")

# Run debug backtest
result = await debug_engine.run_backtest(
    historical_data=historical_data,
    start_date=start_date,
    end_date=end_date,
    parameters=parameters
)

# Generate debug report
report_file = debug_engine.generate_debug_report(result, "debug_reports")
```

### Command Line Usage

```bash
# Run comprehensive debug backtest
python run_debug_backtesting.py --debug-level DETAILED --pairs EUR_USD GBP_USD --timeframes M5 M15 H1 --days 90

# Run with custom parameters
python run_debug_backtesting.py --debug-level VERBOSE --no-charts --no-reports

# Test the system
python test_debug_backtesting.py
```

### Debug Levels

- **BASIC**: Minimal logging, essential information only
- **DETAILED**: Comprehensive logging with performance metrics
- **VERBOSE**: Maximum logging including all signal details

## Output Structure

The debug backtesting system creates the following directory structure:

```
debug_output/
├── logs/                    # Debug log files
├── reports/                 # JSON reports
│   ├── debug_report_*.json
│   └── comprehensive_analysis.json
├── charts/                  # Generated charts
│   ├── equity_curve.png
│   ├── drawdown.png
│   ├── trade_distribution.png
│   ├── performance_by_pair.png
│   ├── signal_analysis.png
│   └── risk_analysis.png
└── data/                    # Data quality reports
    └── data_quality_report.json
```

## Debug Metrics

### Performance Metrics
- **Total Return**: Overall percentage return
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Sharpe Ratio**: Risk-adjusted return measure
- **Max Drawdown**: Maximum peak-to-trough decline
- **Average Trade Duration**: Average time per trade

### Debug Metrics
- **Total Signals Generated**: Number of trading signals created
- **Signals Acted Upon**: Number of signals that resulted in trades
- **Signals Ignored**: Number of signals filtered out
- **Risk Checks Passed/Failed**: Risk management validation results
- **Performance Timing**: Time spent in each component

### Risk Metrics
- **Value at Risk (VaR)**: 95% and 99% confidence levels
- **Conditional VaR (CVaR)**: Expected shortfall
- **Consecutive Losses**: Maximum consecutive losing trades
- **Drawdown Severity**: Risk level assessment
- **Recovery Factor**: Return relative to maximum drawdown

## Analysis Features

### Performance Analysis
- Overall performance metrics
- Trade-by-trade analysis
- Performance breakdown by currency pair
- Performance breakdown by signal type
- Consecutive wins/losses analysis

### Risk Analysis
- Drawdown analysis and severity assessment
- Risk metrics calculation (VaR, CVaR)
- Consecutive losses risk assessment
- Risk check pass rate analysis

### Signal Analysis
- Signal generation efficiency
- Signal quality assessment
- Performance timing breakdown
- Signal-to-trade ratio analysis

## Configuration

### Debug Engine Configuration

```python
# Debug level options
debug_level = "DETAILED"  # BASIC, DETAILED, VERBOSE

# Performance timing
enable_timing = True

# Logging options
log_to_file = True
log_to_console = True
log_level = "DEBUG"
```

### Backtest Parameters

```python
parameters = {
    # Technical analysis parameters
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'macd_signal_threshold': 0.0001,
    'bollinger_threshold': 0.1,
    'atr_multiplier': 2.0,
    'min_signal_strength': 0.5,
    
    # Risk management parameters
    'risk_percentage': 1.0,
    'max_daily_loss': 5.0,
    'max_open_trades': 3
}
```

## Troubleshooting

### Common Issues

1. **Memory Usage**: Large datasets may cause memory issues
   - Solution: Reduce the number of pairs or timeframes
   - Use shorter date ranges for testing

2. **Performance**: Slow execution with large datasets
   - Solution: Use BASIC debug level for large tests
   - Disable chart generation for faster execution

3. **Data Quality Issues**: Missing or invalid data
   - Check the data quality report in `debug_output/data/`
   - Verify API connectivity and data availability

### Debug Tips

1. **Start Small**: Begin with a small dataset and short time period
2. **Check Logs**: Review debug logs for detailed information
3. **Validate Data**: Ensure historical data quality before running tests
4. **Monitor Resources**: Watch memory and CPU usage during execution

## Integration

The debug backtesting system integrates seamlessly with the existing trading bot infrastructure:

- **Config System**: Uses the same configuration as the main bot
- **API Integration**: Leverages existing OANDA API integration
- **Model Compatibility**: Works with existing data models and structures
- **Component Reuse**: Reuses technical analysis and decision-making components

## Future Enhancements

### Planned Features
- **Real-time Debugging**: Live debugging during live trading
- **Machine Learning Integration**: ML-based signal analysis
- **Advanced Visualization**: Interactive charts and dashboards
- **Performance Optimization**: Parallel processing for large datasets
- **Custom Metrics**: User-defined performance metrics

### Extensibility
The system is designed to be easily extensible:
- Add new debug metrics
- Create custom analysis functions
- Implement new visualization types
- Integrate with external analysis tools

## Support

For issues and questions:
1. Check the debug logs for detailed error information
2. Review the data quality reports
3. Test with smaller datasets first
4. Verify configuration settings

## License

This debug backtesting system is part of the trading bot project and follows the same licensing terms.
