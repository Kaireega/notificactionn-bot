# 🧪 Testing Guide for Market Adaptive Trading Bot

This document provides comprehensive guidance for testing the Market Adaptive Trading Bot, including setup, running tests, writing new tests, and best practices.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Categories](#test-categories)
6. [Edge Cases](#edge-cases)
7. [Mocking and Stubbing](#mocking-and-stubbing)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Continuous Integration](#continuous-integration)

## 🚀 Quick Start

### Installation

```bash
# Install test dependencies
pip install -r test_requirements.txt

# Or install core testing packages only
pip install pytest pytest-asyncio pytest-cov pytest-html pytest-xdist
```

### Basic Test Run

```bash
# Run all tests
python run_tests.py --all

# Run with coverage
python run_tests.py --coverage

# Run specific test file
python run_tests.py --file tests/test_models.py
```

## 📁 Test Structure

```
market_adaptive_bot/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures and configuration
│   ├── test_models.py              # Core data models tests
│   ├── test_ai_analysis_layer.py   # AI analysis tests
│   ├── test_technical_analyzer.py  # Technical analysis tests
│   ├── test_decision_layer.py      # Decision layer tests
│   ├── test_data_layer.py          # Data layer tests
│   ├── test_notification_layer.py  # Notification tests
│   ├── test_risk_manager.py        # Risk management tests
│   └── test_performance_tracker.py # Performance tracking tests
├── run_tests.py                    # Test runner script
├── test_requirements.txt           # Test dependencies
└── TESTING_README.md              # This file
```

## 🏃‍♂️ Running Tests

### Using the Test Runner

```bash
# Run all tests
python run_tests.py --all

# Run specific test categories
python run_tests.py --unit          # Unit tests only
python run_tests.py --integration   # Integration tests only
python run_tests.py --ai            # AI-related tests only
python run_tests.py --risk          # Risk management tests only

# Run with different outputs
python run_tests.py --coverage      # With coverage report
python run_tests.py --html          # With HTML report
python run_tests.py --parallel      # Run in parallel

# Run specific tests
python run_tests.py --file tests/test_models.py
python run_tests.py --class TestModels
python run_tests.py --method test_rsi

# Run special categories
python run_tests.py --edge-cases    # Edge case tests
python run_tests.py --fast          # Fast tests only
python run_tests.py --slow          # Slow tests only

# List available tests
python run_tests.py --list
```

### Using Pytest Directly

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_models.py -v

# Run specific test class
pytest tests/test_models.py::TestModels -v

# Run specific test method
pytest tests/test_models.py::TestModels::test_rsi -v

# Run with markers
pytest tests/ -m "unit" -v
pytest tests/ -m "ai" -v
pytest tests/ -m "not slow" -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Run in parallel
pytest tests/ -n auto --dist=loadfile
```

## ✍️ Writing Tests

### Test File Structure

```python
"""
Comprehensive tests for [module_name] with edge cases and proper mocking.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from [module_path] import [ClassName]
from core.models import [relevant_models]


class Test[ClassName]:
    """Test [ClassName] functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock(spec=Config)
        # Configure mock config...
        return config
    
    @pytest.fixture
    def [class_instance](self, mock_config):
        """Create [ClassName] instance for testing."""
        with patch('[module_path].Dependency'):
            instance = [ClassName](mock_config)
            instance.logger = Mock()
            return instance
    
    def test_[method_name]_success(self, [class_instance]):
        """Test successful [method_name] execution."""
        # Arrange
        # Act
        # Assert
    
    @pytest.mark.asyncio
    async def test_[async_method_name]_success(self, [class_instance]):
        """Test successful async [method_name] execution."""
        # Arrange
        # Act
        # Assert
    
    def test_[method_name]_edge_case(self, [class_instance]):
        """Test [method_name] with edge case data."""
        # Test edge cases
    
    def test_[method_name]_exception_handling(self, [class_instance]):
        """Test [method_name] exception handling."""
        # Test error conditions


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    # Edge case tests...
```

### Test Method Naming Convention

```python
# Success cases
def test_method_name_success(self):
    """Test successful method execution."""

def test_method_name_with_valid_data(self):
    """Test method with valid input data."""

# Error cases
def test_method_name_with_invalid_data(self):
    """Test method with invalid input data."""

def test_method_name_exception_handling(self):
    """Test method exception handling."""

# Edge cases
def test_method_name_with_empty_data(self):
    """Test method with empty data."""

def test_method_name_with_extreme_values(self):
    """Test method with extreme values."""

def test_method_name_with_none_values(self):
    """Test method with None values."""

# Async methods
@pytest.mark.asyncio
async def test_async_method_name_success(self):
    """Test successful async method execution."""
```

### Using Fixtures

```python
@pytest.fixture
def sample_data(self):
    """Create sample data for testing."""
    return {
        "key": "value",
        "number": 42,
        "list": [1, 2, 3]
    }

def test_method_with_fixture(self, sample_data):
    """Test method using fixture data."""
    result = process_data(sample_data)
    assert result is not None
```

### Async Testing

```python
@pytest.mark.asyncio
async def test_async_method(self, mock_instance):
    """Test async method."""
    # Mock async dependencies
    mock_instance.async_dependency = AsyncMock(return_value="result")
    
    # Call async method
    result = await mock_instance.async_method()
    
    # Assert results
    assert result == "expected_result"
    mock_instance.async_dependency.assert_called_once()
```

## 🏷️ Test Categories

### Unit Tests (`@pytest.mark.unit`)

Test individual components in isolation.

```python
@pytest.mark.unit
def test_calculate_rsi(self):
    """Test RSI calculation."""
    data = [1.0, 1.1, 1.2, 1.1, 1.0]
    rsi = calculate_rsi(data, period=14)
    assert 0 <= rsi <= 100
```

### Integration Tests (`@pytest.mark.integration`)

Test component interactions.

```python
@pytest.mark.integration
def test_ai_analysis_with_technical_indicators(self):
    """Test AI analysis with technical indicators."""
    # Test full integration flow
```

### AI Tests (`@pytest.mark.ai`)

Test AI-related functionality.

```python
@pytest.mark.ai
def test_openai_api_call(self):
    """Test OpenAI API integration."""
    # Test AI API calls
```

### Risk Tests (`@pytest.mark.risk`)

Test risk management functionality.

```python
@pytest.mark.risk
def test_position_size_calculation(self):
    """Test position size calculation."""
    # Test risk calculations
```

### Notification Tests (`@pytest.mark.notification`)

Test notification systems.

```python
@pytest.mark.notification
def test_telegram_notification(self):
    """Test Telegram notification sending."""
    # Test notification delivery
```

### Slow Tests (`@pytest.mark.slow`)

Mark tests that take longer to run.

```python
@pytest.mark.slow
def test_large_dataset_processing(self):
    """Test processing large datasets."""
    # Test with large data
```

## 🔍 Edge Cases

### Data Type Edge Cases

```python
def test_with_extreme_values(self):
    """Test with extreme values."""
    # Very large numbers
    large_price = Decimal("999999.999999")
    
    # Very small numbers
    small_price = Decimal("0.000001")
    
    # Zero values
    zero_price = Decimal("0")
    
    # Negative values
    negative_price = Decimal("-1.0")

def test_with_none_values(self):
    """Test with None values."""
    result = process_data(None)
    assert result is not None  # Should handle gracefully

def test_with_empty_data(self):
    """Test with empty data."""
    result = process_data([])
    assert result is not None  # Should handle gracefully
```

### Boundary Conditions

```python
def test_boundary_conditions(self):
    """Test boundary conditions."""
    # Minimum valid values
    min_data = create_minimal_valid_data()
    
    # Maximum valid values
    max_data = create_maximal_valid_data()
    
    # Just below minimum
    below_min = create_below_minimum_data()
    
    # Just above maximum
    above_max = create_above_maximum_data()
```

### Error Conditions

```python
def test_invalid_inputs(self):
    """Test invalid inputs."""
    with pytest.raises(ValueError):
        process_data("invalid_string")
    
    with pytest.raises(TypeError):
        process_data(123)  # Wrong type
    
    with pytest.raises(KeyError):
        process_data({})  # Missing required key
```

## 🎭 Mocking and Stubbing

### Basic Mocking

```python
def test_with_mock(self):
    """Test with mocked dependencies."""
    with patch('module.external_service') as mock_service:
        mock_service.return_value = "mocked_result"
        
        result = function_under_test()
        
        assert result == "expected_result"
        mock_service.assert_called_once()
```

### Async Mocking

```python
@pytest.mark.asyncio
async def test_with_async_mock(self):
    """Test with async mocked dependencies."""
    with patch('module.async_service', new_callable=AsyncMock) as mock_service:
        mock_service.return_value = "mocked_result"
        
        result = await async_function_under_test()
        
        assert result == "expected_result"
        mock_service.assert_called_once()
```

### Mocking External APIs

```python
def test_api_call(self):
    """Test external API calls."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response
        
        result = api_function()
        
        assert result == {"data": "test"}
        mock_get.assert_called_once_with("https://api.example.com/data")
```

### Mocking Configuration

```python
@pytest.fixture
def mock_config(self):
    """Create mock configuration."""
    config = Mock(spec=Config)
    config.api_key = "test_key"
    config.base_url = "https://test.api.com"
    config.timeout = 30
    return config
```

## ✅ Best Practices

### 1. Test Organization

```python
# Good: Clear test organization
class TestDataProcessor:
    def test_process_valid_data(self):
        """Test processing valid data."""
        pass
    
    def test_process_invalid_data(self):
        """Test processing invalid data."""
        pass
    
    def test_process_empty_data(self):
        """Test processing empty data."""
        pass

# Bad: Unorganized tests
def test_something(self):
    """Unclear what is being tested."""
    pass
```

### 2. Descriptive Test Names

```python
# Good: Descriptive test names
def test_calculate_rsi_with_uptrend_data(self):
    """Test RSI calculation with upward trending data."""
    pass

def test_calculate_rsi_with_downtrend_data(self):
    """Test RSI calculation with downward trending data."""
    pass

# Bad: Unclear test names
def test_rsi(self):
    """Test RSI."""
    pass
```

### 3. Arrange-Act-Assert Pattern

```python
def test_method_success(self):
    """Test successful method execution."""
    # Arrange
    input_data = create_test_data()
    expected_result = "expected"
    
    # Act
    result = method_under_test(input_data)
    
    # Assert
    assert result == expected_result
    assert result is not None
    assert isinstance(result, str)
```

### 4. Test Isolation

```python
def test_method_independent(self):
    """Test method in isolation."""
    # Each test should be independent
    # Don't rely on state from other tests
    pass
```

### 5. Meaningful Assertions

```python
def test_with_meaningful_assertions(self):
    """Test with meaningful assertions."""
    result = process_data(test_data)
    
    # Good: Specific assertions
    assert result.status == "success"
    assert result.data is not None
    assert len(result.data) == 5
    assert result.timestamp > datetime.utcnow() - timedelta(seconds=1)
    
    # Bad: Generic assertions
    assert result is not None
```

### 6. Error Testing

```python
def test_error_conditions(self):
    """Test error conditions."""
    # Test specific exceptions
    with pytest.raises(ValueError, match="Invalid input"):
        process_data("invalid")
    
    # Test error handling
    result = process_data_with_error_handling("invalid")
    assert result.error is not None
    assert result.error.code == "INVALID_INPUT"
```

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Add src to path in test files
   sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
   ```

2. **Async Test Issues**
   ```python
   # Use @pytest.mark.asyncio decorator
   @pytest.mark.asyncio
   async def test_async_method(self):
       pass
   ```

3. **Mock Issues**
   ```python
   # Use correct import path for mocking
   with patch('module.submodule.ClassName.method'):
       pass
   ```

4. **Fixture Issues**
   ```python
   # Ensure fixtures are in conftest.py or imported
   # Use proper fixture scope
   @pytest.fixture(scope="session")
   def expensive_fixture():
       pass
   ```

### Debugging Tests

```bash
# Run with verbose output
pytest tests/ -v -s

# Run with debugger
pytest tests/ --pdb

# Run specific failing test
pytest tests/test_file.py::TestClass::test_method -v -s

# Run with coverage to see what's not tested
pytest tests/ --cov=src --cov-report=term-missing
```

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r test_requirements.txt
    
    - name: Run tests
      run: |
        python run_tests.py --coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## 📊 Test Coverage

### Coverage Goals

- **Overall Coverage**: 80% minimum
- **Critical Paths**: 95% minimum
- **Edge Cases**: 70% minimum

### Coverage Commands

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Check coverage threshold
pytest tests/ --cov=src --cov-fail-under=80

# Generate coverage badge
coverage-badge -o coverage.svg
```

## 🎯 Test Examples

### Complete Test Example

```python
"""
Test example for TechnicalAnalyzer.
"""
import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import datetime, timedelta

from ai.technical_analyzer import TechnicalAnalyzer
from core.models import CandleData, TimeFrame


class TestTechnicalAnalyzer:
    """Test TechnicalAnalyzer functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock()
        config.technical_analysis_enabled = True
        config.rsi_period = 14
        return config
    
    @pytest.fixture
    def analyzer(self, mock_config):
        """Create analyzer instance."""
        with patch('ai.technical_analyzer.sys.path.append'):
            analyzer = TechnicalAnalyzer(mock_config)
            analyzer.logger = Mock()
            return analyzer
    
    @pytest.fixture
    def sample_candles(self):
        """Create sample candle data."""
        candles = []
        for i in range(50):
            candle = CandleData(
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                open=Decimal("1.2345"),
                high=Decimal("1.2350"),
                low=Decimal("1.2340"),
                close=Decimal("1.2348"),
                pair="EUR_USD",
                timeframe=TimeFrame.M5
            )
            candles.append(candle)
        return candles
    
    def test_initialization(self, mock_config):
        """Test analyzer initialization."""
        with patch('ai.technical_analyzer.sys.path.append') as mock_append:
            analyzer = TechnicalAnalyzer(mock_config)
            
            assert analyzer.config == mock_config
            assert analyzer.logger is not None
            mock_append.assert_called()
    
    def test_candles_to_dataframe(self, analyzer, sample_candles):
        """Test candle to dataframe conversion."""
        df = analyzer._candles_to_dataframe(sample_candles)
        
        assert len(df) == len(sample_candles)
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
    
    def test_candles_to_dataframe_empty(self, analyzer):
        """Test candle to dataframe with empty data."""
        df = analyzer._candles_to_dataframe([])
        
        assert len(df) == 0
        assert 'open' in df.columns
    
    @patch('ai.technical_analyzer.RSI')
    @patch('ai.technical_analyzer.MACD')
    def test_calculate_indicators_success(self, mock_macd, mock_rsi, analyzer, sample_candles):
        """Test successful indicator calculation."""
        # Mock the technical indicator functions
        mock_df = Mock()
        mock_df.iloc = [Mock()]
        mock_df.iloc[-1] = {
            'RSI_14': 50.0,
            'MACD': 0.001,
            'SIGNAL': 0.002,
            'HIST': -0.001
        }
        
        mock_rsi.return_value = mock_df
        mock_macd.return_value = mock_df
        
        indicators = analyzer.calculate_indicators(sample_candles)
        
        assert indicators.rsi == 50.0
        assert indicators.macd == 0.001
        assert indicators.macd_signal == 0.002
        assert indicators.macd_histogram == -0.001
    
    def test_calculate_indicators_insufficient_data(self, analyzer):
        """Test indicator calculation with insufficient data."""
        # Create only 10 candles (less than 20 required)
        candles = [Mock() for _ in range(10)]
        
        indicators = analyzer.calculate_indicators(candles)
        
        assert indicators.rsi is None
        assert indicators.macd is None
    
    def test_calculate_indicators_exception(self, analyzer, sample_candles):
        """Test indicator calculation with exception."""
        with patch('ai.technical_analyzer.RSI', side_effect=Exception("Test error")):
            indicators = analyzer.calculate_indicators(sample_candles)
            
            assert indicators.rsi is None
            assert indicators.macd is None
            analyzer.logger.error.assert_called()


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def analyzer_edge(self):
        """Create analyzer for edge case testing."""
        config = Mock()
        config.technical_analysis_enabled = True
        
        with patch('ai.technical_analyzer.sys.path.append'):
            analyzer = TechnicalAnalyzer(config)
            analyzer.logger = Mock()
            return analyzer
    
    def test_extreme_price_values(self, analyzer_edge):
        """Test with extreme price values."""
        candles = [CandleData(
            timestamp=datetime.utcnow(),
            open=Decimal("999999.999999"),
            high=Decimal("999999.999999"),
            low=Decimal("0.000001"),
            close=Decimal("999999.999999"),
            pair="EUR_USD"
        )]
        
        df = analyzer_edge._candles_to_dataframe(candles)
        
        assert df['open'].iloc[0] == 999999.999999
        assert df['low'].iloc[0] == 0.000001
    
    def test_zero_price_values(self, analyzer_edge):
        """Test with zero price values."""
        candles = [CandleData(
            timestamp=datetime.utcnow(),
            open=Decimal("0"),
            high=Decimal("0"),
            low=Decimal("0"),
            close=Decimal("0"),
            pair="EUR_USD"
        )]
        
        df = analyzer_edge._candles_to_dataframe(candles)
        
        assert df['open'].iloc[0] == 0.0
        assert df['close'].iloc[0] == 0.0
```

This comprehensive testing guide should help you write, run, and maintain high-quality tests for the Market Adaptive Trading Bot. Remember to follow the best practices and always test edge cases and error conditions! 