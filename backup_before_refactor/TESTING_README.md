# Testing & Integration Guide

## 🎯 Overview

This document provides comprehensive guidance for testing the legacy system integration with the new market adaptive bot, including all edge cases and performance requirements.

## 🚨 Critical Issues Identified

### 1. **System Isolation**
- **Problem**: Legacy systems (`bot/`, `stream_bot/`) are completely isolated from the new `market_adaptive_bot/`
- **Impact**: No data sharing, duplicate API calls, inconsistent trading logic
- **Solution**: Implemented `unified_api.py` wrapper

### 2. **Configuration Fragmentation**
- **Problem**: Multiple configuration formats (JSON vs YAML) across systems
- **Impact**: Maintenance overhead, potential configuration conflicts
- **Solution**: Created `config_migrator.py` for unified configuration

### 3. **Missing Test Coverage**
- **Problem**: Limited test coverage, especially for edge cases and integration
- **Impact**: Risk of production failures, difficult debugging
- **Solution**: Comprehensive test suite with 90%+ coverage target

## 🧪 Test Suite Structure

### Core Test Files

#### 1. **Integration Tests** (`tests/test_integration.py`)
- Legacy-new system integration
- API consistency across systems
- Data synchronization
- Configuration migration
- Error recovery mechanisms

#### 2. **Edge Case Tests** (`tests/test_edge_cases.py`)
- Network failures and timeouts
- Data quality issues (missing/corrupted data)
- System resource exhaustion
- Concurrency and race conditions
- Configuration errors
- Extreme market conditions

#### 3. **Performance Tests** (`tests/test_performance.py`)
- Latency requirements (< 100ms for API calls)
- Throughput limits (1000+ operations/second)
- Memory usage monitoring
- CPU efficiency
- Scalability testing

#### 4. **Legacy Tests** (Existing)
- `run_api_tests.py` - Basic API connectivity
- `simulation/guru_tester.py` - Backtesting framework
- `exploration/*.ipynb` - Data analysis tests

## 🚀 Quick Start

### 1. Install Test Dependencies
```bash
pip install -r test_requirements.txt
```

### 2. Run All Tests
```bash
python run_comprehensive_tests.py
```

### 3. Run Specific Test Categories
```bash
# Integration tests only
python run_comprehensive_tests.py --only integration_tests

# Skip performance tests
python run_comprehensive_tests.py --skip performance_tests

# Custom output file
python run_comprehensive_tests.py --output my_test_report.json
```

### 4. Run Individual Test Suites
```bash
# Integration tests
pytest tests/test_integration.py -v

# Edge case tests
pytest tests/test_edge_cases.py -v

# Performance tests
pytest tests/test_performance.py -v
```

## 🔧 Integration Components

### 1. **Unified API Wrapper** (`unified_api.py`)
```python
from unified_api import UnifiedOandaApi

# Initialize with both systems
api = UnifiedOandaApi(use_new_system=True)

# Automatic fallback to legacy system
account = api.get_account_summary()
candles = api.get_candles_df("EUR_USD", count=100)

# Health check both systems
health = api.health_check()
```

### 2. **Configuration Migration** (`config_migrator.py`)
```bash
# Migrate legacy configs to new format
python config_migrator.py

# Dry run to see what would be migrated
python config_migrator.py --dry-run

# Skip validation
python config_migrator.py --no-validate
```

## 📊 Test Coverage Requirements

### Unit Tests: 90% Coverage
- [ ] All API methods (`api/oanda_api.py`)
- [ ] All data processing functions
- [ ] All trading logic functions
- [ ] All configuration management

### Integration Tests: 100% Coverage
- [ ] API integration points
- [ ] Database operations
- [ ] Cross-system communication
- [ ] Configuration migration

### End-to-End Tests: Critical Paths
- [ ] Complete trade lifecycle
- [ ] Data collection pipeline
- [ ] Error recovery scenarios
- [ ] Performance under load

## 🔍 Edge Cases Covered

### 1. **Network Issues**
- [x] API timeout scenarios (2s, 5s, 30s)
- [x] Intermittent connectivity
- [x] Rate limiting responses
- [x] DNS resolution failures

### 2. **Data Quality Issues**
- [x] Missing candle data
- [x] Corrupted price data
- [x] Out-of-order timestamps
- [x] Invalid data types

### 3. **System Resource Issues**
- [x] Memory exhaustion
- [x] Disk space issues
- [x] CPU overload
- [x] File descriptor limits

### 4. **Concurrency Issues**
- [x] Multiple trade requests
- [x] Simultaneous data updates
- [x] Race conditions
- [x] Deadlock prevention

### 5. **Configuration Issues**
- [x] Invalid settings
- [x] Missing configuration files
- [x] Configuration conflicts
- [x] Environment variable issues

### 6. **Market Conditions**
- [x] High volatility periods
- [x] Low liquidity scenarios
- [x] Market gaps and jumps
- [x] Extreme price movements

## 📈 Performance Benchmarks

### Latency Requirements
- **API Calls**: < 100ms average
- **Cache Hits**: < 10ms
- **Database Queries**: < 50ms
- **Trade Execution**: < 200ms

### Throughput Requirements
- **Data Processing**: 1000+ candles/second
- **Concurrent Users**: 10+ simultaneous
- **Memory Usage**: < 200MB under load
- **CPU Usage**: < 50% average

### Scalability Requirements
- **Data Size**: Linear scaling up to 1M records
- **Concurrent Operations**: Linear scaling up to 100 users
- **Time Complexity**: O(n) for data processing

## 🛠️ Test Environment Setup

### Required Services
```bash
# MongoDB (for data storage)
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Redis (for caching)
docker run -d -p 6379:6379 --name redis redis:latest

# PostgreSQL (optional, for new system)
docker run -d -p 5432:5432 --name postgres postgres:latest
```

### Environment Variables
```bash
# API Configuration
export OANDA_API_KEY="your_api_key"
export OANDA_ACCOUNT_ID="your_account_id"
export OANDA_URL="https://api-fxpractice.oanda.com/v3"

# Database Configuration
export MONGODB_URI="mongodb://localhost:27017/trading_bot"
export REDIS_URL="redis://localhost:6379/0"

# Test Configuration
export TEST_MODE="true"
export TEST_TIMEOUT="300"
```

## 📋 Test Execution Checklist

### Pre-Test Setup
- [ ] Install all dependencies
- [ ] Start required services (MongoDB, Redis)
- [ ] Set environment variables
- [ ] Verify API credentials
- [ ] Clear test databases

### Test Execution
- [ ] Run unit tests first
- [ ] Run integration tests
- [ ] Run edge case tests
- [ ] Run performance tests
- [ ] Generate coverage report

### Post-Test Validation
- [ ] Review test results
- [ ] Check for memory leaks
- [ ] Verify data integrity
- [ ] Analyze performance metrics
- [ ] Document any failures

## 🚨 Common Issues & Solutions

### 1. **Import Errors**
```bash
# Add project root to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 2. **Database Connection Issues**
```bash
# Check MongoDB status
docker ps | grep mongodb

# Check Redis status
docker ps | grep redis

# Test connections
python -c "from db.db import DataDB; d = DataDB(); d.test_connection()"
```

### 3. **API Rate Limiting**
```bash
# Use test API credentials
export OANDA_URL="https://api-fxpractice.oanda.com/v3"

# Implement rate limiting in tests
time.sleep(0.1)  # 100ms between API calls
```

### 4. **Memory Issues**
```bash
# Monitor memory usage
python -m memory_profiler tests/test_performance.py

# Check for memory leaks
python -c "import gc; gc.collect(); print(gc.get_count())"
```

## 📊 Monitoring & Reporting

### Test Reports
- **Location**: `test_report.json`
- **Format**: JSON with detailed results
- **Includes**: Pass/fail status, duration, errors, recommendations

### Performance Metrics
- **Latency**: Average response times
- **Throughput**: Operations per second
- **Memory**: Peak and average usage
- **CPU**: Usage percentage

### Coverage Reports
```bash
# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

## 🔄 Continuous Integration

### GitHub Actions Example
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r test_requirements.txt
          pip install -r main_req.txt
      - name: Run tests
        run: python run_comprehensive_tests.py
      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_report.json
```

## 📞 Support & Troubleshooting

### Getting Help
1. Check the test logs in `test_report.json`
2. Review the integration analysis in `integration_analysis.md`
3. Run individual test suites to isolate issues
4. Check system requirements and dependencies

### Common Debugging Commands
```bash
# Run with verbose output
pytest -v -s tests/test_integration.py

# Run specific test
pytest tests/test_integration.py::TestUnifiedApiIntegration::test_legacy_api_fallback

# Debug with pdb
pytest --pdb tests/test_edge_cases.py

# Profile performance
python -m cProfile -o profile.stats run_comprehensive_tests.py
```

## 🎯 Next Steps

### Phase 1: Immediate Actions
1. [ ] Run comprehensive test suite
2. [ ] Fix critical integration issues
3. [ ] Migrate configurations
4. [ ] Implement unified API wrapper

### Phase 2: Enhancement
1. [ ] Add more edge case tests
2. [ ] Implement retry mechanisms
3. [ ] Add performance monitoring
4. [ ] Create automated deployment

### Phase 3: Optimization
1. [ ] Optimize performance bottlenecks
2. [ ] Implement advanced caching
3. [ ] Add real-time monitoring
4. [ ] Create disaster recovery procedures

---

**Note**: This testing framework ensures robust integration between legacy and new systems while maintaining high performance and reliability standards. 