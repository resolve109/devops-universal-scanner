"""
Unit tests for Azure Pricing API

Tests the public Azure Retail Prices API functionality without requiring credentials.
"""

import pytest
from unittest.mock import Mock, patch
from devops_universal_scanner.core.pricing.azure_pricing import AzurePricingAPI


class TestAzurePricingAPIInitialization:
    """Test Azure Pricing API initialization"""

    @patch('devops_universal_scanner.core.pricing.azure_pricing.requests')
    def test_initialization_with_requests_available(self, mock_requests):
        """Test initialization when requests library is available"""
        api = AzurePricingAPI()
        assert api.api_available is True
        assert api.initialization_error is None

    def test_initialization_without_requests(self):
        """Test initialization when requests is not available"""
        with patch.dict('sys.modules', {'requests': None}):
            with patch('devops_universal_scanner.core.pricing.azure_pricing.requests', side_effect=ImportError):
                api = AzurePricingAPI()
                assert api.api_available is False
                assert api.initialization_error == "requests library not installed"


class TestAzurePricingAPIVMPricing:
    """Test VM pricing retrieval"""

    @pytest.fixture
    def mock_api(self):
        """Create a mocked Azure Pricing API"""
        with patch('devops_universal_scanner.core.pricing.azure_pricing.requests'):
            return AzurePricingAPI()

    def test_get_vm_pricing_from_cache(self, mock_api):
        """Test VM pricing retrieval from cache"""
        cached_data = {
            "vm_size": "Standard_B1s",
            "monthly_cost": 7.59,
            "source": "cache"
        }
        mock_api.cache.set("vm_Standard_B1s_eastus", cached_data)

        result = mock_api.get_vm_pricing("Standard_B1s")
        assert result == cached_data

    @patch('devops_universal_scanner.core.pricing.azure_pricing.requests')
    def test_get_vm_pricing_from_api(self, mock_requests, mock_api):
        """Test VM pricing retrieval from live API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Items": [{"retailPrice": 0.0104, "currencyCode": "USD"}]
        }
        mock_requests.get.return_value = mock_response
        mock_api.api_available = True

        result = mock_api.get_vm_pricing("Standard_B1s")
        assert result is not None
        assert result["vm_size"] == "Standard_B1s"

    def test_get_vm_pricing_fallback(self, mock_api):
        """Test VM pricing fallback to static data"""
        mock_api.api_available = False

        result = mock_api.get_vm_pricing("Standard_B1s")
        assert result is not None
        assert result["source"] == "static_fallback"


@pytest.mark.requires_network
@pytest.mark.slow
class TestAzurePricingAPILiveIntegration:
    """Integration tests with live Azure Retail Prices API"""

    @pytest.mark.requires_azure
    def test_live_vm_pricing(self):
        """Test retrieving VM pricing from live Azure API"""
        pytest.importorskip("requests")

        api = AzurePricingAPI()
        result = api.get_vm_pricing("Standard_B1s", region="eastus")

        assert result is not None
        assert result["vm_size"] == "Standard_B1s"
        assert result["source"] in ["azure_retail_api", "static_fallback"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
