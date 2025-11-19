"""
Unit tests for AWS Pricing API

Tests the public AWS Pricing API functionality without requiring credentials.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from devops_universal_scanner.core.pricing.aws_pricing import AWSPricingAPI


class TestAWSPricingAPIInitialization:
    """Test AWS Pricing API initialization"""

    @patch('devops_universal_scanner.core.pricing.aws_pricing.boto3')
    def test_initialization_with_boto3_available(self, mock_boto3):
        """Test initialization when boto3 is available"""
        # Setup
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        # Execute
        api = AWSPricingAPI()

        # Assert
        assert api.boto3_available is True
        assert api.pricing_client is not None
        assert api.credentials_available is True  # Public API doesn't need credentials
        mock_boto3.client.assert_called_once()

    def test_initialization_without_boto3(self):
        """Test initialization when boto3 is not available"""
        # Setup - mock boto3 import failure
        with patch.dict('sys.modules', {'boto3': None}):
            with patch('devops_universal_scanner.core.pricing.aws_pricing.boto3', side_effect=ImportError):
                # Execute
                api = AWSPricingAPI()

                # Assert
                assert api.boto3_available is False
                assert api.pricing_client is None
                assert api.initialization_error == "boto3 not installed"


class TestAWSPricingAPIEC2Pricing:
    """Test EC2 pricing retrieval"""

    @pytest.fixture
    def mock_api(self):
        """Create a mocked AWS Pricing API"""
        with patch('devops_universal_scanner.core.pricing.aws_pricing.boto3'):
            api = AWSPricingAPI()
            return api

    def test_get_ec2_pricing_from_cache(self, mock_api):
        """Test EC2 pricing retrieval from cache"""
        # Setup
        cached_data = {
            "instance_type": "t3.micro",
            "monthly_cost": 7.59,
            "source": "cache"
        }
        mock_api.cache.set("ec2_t3.micro_us-east-1", cached_data)

        # Execute
        result = mock_api.get_ec2_pricing("t3.micro")

        # Assert
        assert result == cached_data
        assert result["source"] == "cache"

    @patch('devops_universal_scanner.core.pricing.aws_pricing.boto3')
    def test_get_ec2_pricing_from_api(self, mock_boto3, mock_api):
        """Test EC2 pricing retrieval from live API"""
        # Setup
        mock_client = Mock()
        mock_response = {
            'PriceList': [
                '{"terms": {"OnDemand": {"test": {"priceDimensions": {"test": {"pricePerUnit": {"USD": "0.0104"}}}}}}}'
            ]
        }
        mock_client.get_products.return_value = mock_response
        mock_api.pricing_client = mock_client
        mock_api.credentials_available = True

        # Execute
        result = mock_api.get_ec2_pricing("t3.micro")

        # Assert
        assert result is not None
        assert result["instance_type"] == "t3.micro"
        assert result["source"] == "aws_pricing_api"
        assert "monthly_cost" in result
        assert "hourly_cost" in result

    def test_get_ec2_pricing_fallback(self, mock_api):
        """Test EC2 pricing fallback to static data"""
        # Setup
        mock_api.credentials_available = False

        # Execute
        result = mock_api.get_ec2_pricing("t3.micro")

        # Assert
        assert result is not None
        assert result["instance_type"] == "t3.micro"
        assert result["source"] == "static_fallback"
        assert "monthly_cost" in result


class TestAWSPricingAPIStatus:
    """Test pricing API status"""

    @patch('devops_universal_scanner.core.pricing.aws_pricing.boto3')
    def test_get_pricing_status_api_available(self, mock_boto3):
        """Test status when API is available"""
        # Setup
        api = AWSPricingAPI()

        # Execute
        status = api.get_pricing_status()

        # Assert
        assert status["provider"] == "AWS"
        assert status["api_available"] is True
        assert "Live AWS Pricing API" in status["note"]

    def test_get_pricing_status_boto3_unavailable(self):
        """Test status when boto3 is unavailable"""
        # Setup
        with patch.dict('sys.modules', {'boto3': None}):
            with patch('devops_universal_scanner.core.pricing.aws_pricing.boto3', side_effect=ImportError):
                api = AWSPricingAPI()

                # Execute
                status = api.get_pricing_status()

                # Assert
                assert status["api_available"] is False
                assert status["using_fallback"] is True
                assert "boto3 not installed" in status["note"]


class TestAWSPricingAPIRDSPricing:
    """Test RDS pricing retrieval"""

    @pytest.fixture
    def mock_api(self):
        """Create a mocked AWS Pricing API"""
        with patch('devops_universal_scanner.core.pricing.aws_pricing.boto3'):
            api = AWSPricingAPI()
            return api

    def test_get_rds_pricing_fallback(self, mock_api):
        """Test RDS pricing fallback to static data"""
        # Setup
        mock_api.credentials_available = False

        # Execute
        result = mock_api.get_rds_pricing("db.t3.micro", engine="mysql")

        # Assert
        assert result is not None
        assert result["instance_class"] == "db.t3.micro"
        assert result["engine"] == "mysql"
        assert result["source"] == "static_fallback"


@pytest.mark.requires_network
@pytest.mark.slow
class TestAWSPricingAPILiveIntegration:
    """
    Integration tests with live AWS Pricing API

    These tests require network access and actually call the AWS API.
    Mark as slow and requires_network.
    """

    @pytest.mark.requires_aws
    def test_live_ec2_pricing(self):
        """Test retrieving EC2 pricing from live AWS API"""
        # Skip if boto3 not available
        pytest.importorskip("boto3")

        # Execute
        api = AWSPricingAPI()
        result = api.get_ec2_pricing("t3.micro", region="us-east-1")

        # Assert
        assert result is not None
        assert result["instance_type"] == "t3.micro"
        # Should either be from API or fallback
        assert result["source"] in ["aws_pricing_api", "static_fallback"]
        assert result["monthly_cost"] > 0

    @pytest.mark.requires_aws
    def test_live_rds_pricing(self):
        """Test retrieving RDS pricing from live AWS API"""
        # Skip if boto3 not available
        pytest.importorskip("boto3")

        # Execute
        api = AWSPricingAPI()
        result = api.get_rds_pricing("db.t3.micro", engine="mysql", region="us-east-1")

        # Assert
        assert result is not None
        assert result["instance_class"] == "db.t3.micro"
        assert result["monthly_cost"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
