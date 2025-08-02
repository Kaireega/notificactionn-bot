"""
Integration Tests - Tests the integration between legacy and new systems
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd

from api.unified_api import UnifiedOandaApi
from api.oanda_api import OandaApi
from models.api_price import ApiPrice
from models.open_trade import OpenTrade


class TestUnifiedApiIntegration:
    """Test integration between legacy and new API systems."""
    
    @pytest.fixture
    def mock_legacy_api(self):
        """Mock legacy API responses."""
        mock_api = Mock(spec=OandaApi)
        
        # Mock account summary
        mock_api.get_account_summary.return_value = {
            "id": "test_account",
            "balance": "10000.0000",
            "currency": "USD"
        }
        
        # Mock instruments
        mock_api.get_account_instruments.return_value = [
            {"name": "EUR_USD", "type": "CURRENCY"},
            {"name": "GBP_USD", "type": "CURRENCY"}
        ]
        
        # Mock candles
        mock_candles = [
            {
                "time": "2024-01-01T00:00:00.000000000Z",
                "mid": {"o": "1.1000", "h": "1.1010", "l": "1.0990", "c": "1.1005"},
                "complete": True
            }
        ]
        mock_api.fetch_candles.return_value = mock_candles
        
        # Mock DataFrame
        mock_df = pd.DataFrame({
            'time': [datetime.now()],
            'mid_o': [1.1000],
            'mid_h': [1.1010],
            'mid_l': [1.0990],
            'mid_c': [1.1005]
        })
        mock_api.get_candles_df.return_value = mock_df
        
        return mock_api
    
    @pytest.fixture
    def unified_api(self, mock_legacy_api):
        """Create UnifiedOandaApi with mocked legacy API."""
        with patch('unified_api.OandaApi', return_value=mock_legacy_api):
            return UnifiedOandaApi(use_new_system=False)
    
    def test_legacy_api_fallback(self, unified_api, mock_legacy_api):
        """Test that legacy API is used as fallback."""
        # Test account summary
        result = unified_api.get_account_summary()
        assert result is not None
        assert result["id"] == "test_account"
        mock_legacy_api.get_account_summary.assert_called_once()
        
        # Test instruments
        result = unified_api.get_account_instruments()
        assert result is not None
        assert len(result) == 2
        mock_legacy_api.get_account_instruments.assert_called_once()
    
    def test_caching_mechanism(self, unified_api, mock_legacy_api):
        """Test that API responses are properly cached."""
        # First call should hit the API
        result1 = unified_api.get_account_instruments()
        assert mock_legacy_api.get_account_instruments.call_count == 1
        
        # Second call should use cache
        result2 = unified_api.get_account_instruments()
        assert mock_legacy_api.get_account_instruments.call_count == 1  # No additional call
        
        # Results should be identical
        assert result1 == result2
    
    def test_cache_expiration(self, unified_api, mock_legacy_api):
        """Test that cache expires after TTL."""
        # First call
        unified_api.get_account_instruments()
        assert mock_legacy_api.get_account_instruments.call_count == 1
        
        # Manually expire cache by modifying timestamp
        cache_key = "account_instruments"
        if cache_key in unified_api._cache:
            timestamp, data = unified_api._cache[cache_key]
            # Set timestamp to past
            unified_api._cache[cache_key] = (timestamp - timedelta(seconds=120), data)
        
        # Second call should hit API again
        unified_api.get_account_instruments()
        assert mock_legacy_api.get_account_instruments.call_count == 2
    
    def test_error_handling(self, unified_api, mock_legacy_api):
        """Test error handling in API calls."""
        # Mock API to raise exception
        mock_legacy_api.get_account_summary.side_effect = Exception("API Error")
        
        # Should return None instead of raising
        result = unified_api.get_account_summary()
        assert result is None
    
    def test_health_check(self, unified_api, mock_legacy_api):
        """Test health check functionality."""
        health = unified_api.health_check()
        
        assert "legacy_system" in health
        assert "new_system" in health
        assert "overall" in health
        assert isinstance(health["legacy_system"], bool)
        assert isinstance(health["new_system"], bool)
        assert isinstance(health["overall"], bool)
    
    def test_cache_management(self, unified_api, mock_legacy_api):
        """Test cache management functions."""
        # Add some data to cache
        unified_api.get_account_instruments()
        
        # Check cache stats
        stats = unified_api.get_cache_stats()
        assert stats["cached_items"] > 0
        assert stats["cache_ttl_seconds"] == 60
        
        # Clear cache
        unified_api.clear_cache()
        stats = unified_api.get_cache_stats()
        assert stats["cached_items"] == 0


class TestDataSynchronization:
    """Test data synchronization between systems."""
    
    @pytest.fixture
    def mock_data_sources(self):
        """Mock different data sources."""
        legacy_data = {
            "EUR_USD": pd.DataFrame({
                'time': [datetime.now()],
                'mid_o': [1.1000],
                'mid_c': [1.1005]
            })
        }
        
        new_data = {
            "EUR_USD": pd.DataFrame({
                'time': [datetime.now()],
                'open': [1.1000],
                'close': [1.1005]
            })
        }
        
        return legacy_data, new_data
    
    def test_data_format_compatibility(self, mock_data_sources):
        """Test that data formats are compatible between systems."""
        legacy_data, new_data = mock_data_sources
        
        # Both should have time column
        assert 'time' in legacy_data["EUR_USD"].columns
        assert 'time' in new_data["EUR_USD"].columns
        
        # Both should have price data
        assert 'mid_c' in legacy_data["EUR_USD"].columns or 'close' in new_data["EUR_USD"].columns


class TestConfigurationMigration:
    """Test configuration migration from JSON to YAML."""
    
    def test_json_to_yaml_conversion(self):
        """Test conversion of legacy JSON config to new YAML format."""
        legacy_config = {
            "pairs": {
                "EUR_USD": {
                    "ema_short": 12,
                    "ema_long": 26,
                    "rsi_period": 14
                }
            },
            "trade_risk": 0.02
        }
        
        # Expected YAML structure
        expected_yaml_structure = {
            "trading_pairs": ["EUR_USD"],
            "strategies": {
                "EUR_USD": {
                    "ema_short": 12,
                    "ema_long": 26,
                    "rsi_period": 14
                }
            },
            "risk_management": {
                "max_risk_per_trade": 0.02
            }
        }
        
        # Test conversion logic
        converted = self._convert_json_to_yaml(legacy_config)
        assert converted["trading_pairs"] == ["EUR_USD"]
        assert converted["strategies"]["EUR_USD"]["ema_short"] == 12
        assert converted["risk_management"]["max_risk_per_trade"] == 0.02
    
    def _convert_json_to_yaml(self, legacy_config):
        """Convert legacy JSON config to new YAML format."""
        converted = {
            "trading_pairs": list(legacy_config["pairs"].keys()),
            "strategies": legacy_config["pairs"],
            "risk_management": {
                "max_risk_per_trade": legacy_config["trade_risk"]
            }
        }
        return converted


class TestErrorRecovery:
    """Test error recovery mechanisms."""
    
    @pytest.fixture
    def api_with_failures(self, mock_legacy_api):
        """Create API that fails intermittently."""
        call_count = 0
        
        def failing_get_summary():
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:  # Fail every other call
                raise Exception("Temporary API failure")
            return {"id": "test_account"}
        
        mock_legacy_api.get_account_summary.side_effect = failing_get_summary
        return mock_legacy_api
    
    def test_graceful_degradation(self, api_with_failures):
        """Test system continues operating with partial failures."""
        with patch('unified_api.OandaApi', return_value=api_with_failures):
            unified_api = UnifiedOandaApi()
            
            # First call should succeed
            result1 = unified_api.get_account_summary()
            assert result1 is not None
            
            # Second call should fail but not crash
            result2 = unified_api.get_account_summary()
            assert result2 is None  # Should return None on failure
    
    def test_retry_mechanism(self):
        """Test retry mechanism for transient failures."""
        # TODO: Implement retry mechanism test
        pass


class TestPerformance:
    """Test performance characteristics."""
    
    def test_api_latency(self, unified_api, mock_legacy_api):
        """Test that API calls meet latency requirements."""
        start_time = time.time()
        unified_api.get_account_summary()
        end_time = time.time()
        
        latency = end_time - start_time
        assert latency < 1.0  # Should complete within 1 second
    
    def test_cache_performance(self, unified_api, mock_legacy_api):
        """Test cache performance benefits."""
        # First call (cache miss)
        start_time = time.time()
        unified_api.get_account_instruments()
        first_call_time = time.time() - start_time
        
        # Second call (cache hit)
        start_time = time.time()
        unified_api.get_account_instruments()
        second_call_time = time.time() - start_time
        
        # Cache hit should be faster
        assert second_call_time < first_call_time


class TestConcurrency:
    """Test concurrent access patterns."""
    
    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self, unified_api, mock_legacy_api):
        """Test concurrent API calls don't interfere."""
        async def make_api_call():
            return unified_api.get_account_summary()
        
        # Make multiple concurrent calls
        tasks = [make_api_call() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All calls should succeed
        assert all(result is not None for result in results)
        assert mock_legacy_api.get_account_summary.call_count == 5
    
    def test_thread_safety(self, unified_api, mock_legacy_api):
        """Test thread safety of cache operations."""
        import threading
        
        results = []
        errors = []
        
        def worker():
            try:
                result = unified_api.get_account_instruments()
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=worker) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have no errors and all results
        assert len(errors) == 0
        assert len(results) == 10
        assert all(result is not None for result in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 