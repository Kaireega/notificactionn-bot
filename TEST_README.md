# Trading Bot Component Tests

This directory contains comprehensive test scripts to validate all components of your trading bot with the new balanced settings.

## 📋 Test Scripts Overview

### 1. `validate_config.py`
**Quick configuration validation**
- Validates that balanced settings are properly applied
- Checks key thresholds (60% confidence, 1.8 R/R ratio, etc.)
- Fast execution, no external dependencies

### 2. `test_bot_components.py`
**Comprehensive component testing**
- Tests all major bot components
- Validates risk management, technical analysis, multi-timeframe analysis
- Tests integration between components
- More thorough but takes longer to run

### 3. `run_tests.py`
**Complete test suite runner**
- Runs both configuration validation and component tests
- Provides overall test results
- Recommended for full validation

## 🚀 How to Run Tests

### Quick Configuration Check
```bash
python validate_config.py
```

### Full Component Tests
```bash
python test_bot_components.py
```

### Complete Test Suite (Recommended)
```bash
python run_tests.py
```

## 📊 What the Tests Validate

### Configuration Tests
- ✅ AI confidence threshold (should be 0.6)
- ✅ Risk/reward ratio minimum (should be 1.8)
- ✅ Max trades per day (should be 15)
- ✅ Risk percentage (should be 4.0)
- ✅ Multi-timeframe settings (2 timeframes, 0.65 consensus)
- ✅ Analysis frequency (should be 90 seconds)

### Component Tests
- ✅ **Risk Manager**: Validates trade approval/rejection logic
- ✅ **Technical Analysis**: Tests signal generation and confidence calculation
- ✅ **Multi-Timeframe Analysis**: Tests consensus generation
- ✅ **Exit Criteria**: Tests exit condition evaluation
- ✅ **AI Analysis Layer**: Tests component integration
- ✅ **Integration**: Tests end-to-end workflow

### Market Condition Tests
- ✅ News reactionary markets (70% confidence, 2.0 R/R)
- ✅ Reversal markets (65% confidence, 1.8 R/R)
- ✅ Breakout markets (60% confidence)
- ✅ Ranging markets (70% confidence, ≤1.8 R/R)

## 🎯 Expected Results

### With Balanced Settings (60% confidence, 1.8 R/R):
- **Configuration**: All settings should match balanced values
- **Risk Manager**: Should approve good trades, reject poor ones
- **Technical Analysis**: Should generate signals with proper confidence
- **Multi-Timeframe**: Should find consensus when conditions are met
- **Integration**: Should work end-to-end without errors

### Test Scenarios:
1. **High Quality Trade** (75% confidence, 2.0 R/R) → Should be **APPROVED**
2. **Low Quality Trade** (50% confidence, 1.5 R/R) → Should be **REJECTED**
3. **Market Condition Tests** → Should apply specific rules correctly

## 🔧 Troubleshooting

### Common Issues:

1. **Configuration Mismatch**
   ```
   ❌ AI Confidence Threshold: 0.7 (Expected: 0.6)
   ```
   **Solution**: Update `trading_bot/config/trading_config.yaml` with balanced settings

2. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'trading_bot'
   ```
   **Solution**: Ensure you're running from the project root directory

3. **Component Test Failures**
   ```
   ❌ Risk Manager: FAIL
   ```
   **Solution**: Check that all required files exist and are properly configured

### Debug Mode:
To see detailed error messages, run:
```bash
python -u test_bot_components.py 2>&1 | tee test_output.log
```

## 📈 Performance Expectations

With the balanced settings (60% confidence, 1.8 R/R), you should expect:

- **Trade Frequency**: 8-12 trades per day (vs 2-5 with strict settings)
- **Win Rate**: 60-70% (still good quality)
- **Risk Level**: Low to moderate drawdown
- **Opportunities**: Significantly more trade opportunities

## 🎉 Success Criteria

Tests are successful when:
- ✅ All configuration values match balanced settings
- ✅ Risk manager correctly approves/rejects test trades
- ✅ Technical analysis generates proper signals
- ✅ Multi-timeframe analysis works correctly
- ✅ All components integrate without errors
- ✅ No critical failures in any test

## 📝 Next Steps

After successful tests:
1. **Paper Trading**: Test with real market data in simulation mode
2. **Monitoring**: Watch for actual trade frequency and quality
3. **Adjustment**: Fine-tune thresholds based on real performance
4. **Live Trading**: Gradually move to live trading with small position sizes

## 🆘 Support

If tests fail:
1. Check the error messages for specific issues
2. Verify all configuration files are properly updated
3. Ensure all required dependencies are installed
4. Review the component-specific error logs

The test scripts will help ensure your bot is properly configured and ready for trading with the new balanced settings!
