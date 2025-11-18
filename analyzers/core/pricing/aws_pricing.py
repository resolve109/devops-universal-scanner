"""
AWS Pricing API Integration
Fetches real-time pricing from AWS Pricing API

Note: AWS Pricing API is only available in us-east-1 and ap-south-1
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Optional, Tuple
from datetime import datetime
from analyzers.core.pricing.pricing_cache import PricingCache


class AWSPricingAPI:
    """
    Fetches live pricing from AWS Pricing API

    Operations:
    1. get_ec2_pricing - Get EC2 instance pricing
    2. get_rds_pricing - Get RDS instance pricing
    3. get_ebs_pricing - Get EBS volume pricing
    4. get_s3_pricing - Get S3 storage pricing
    """

    # AWS Pricing API endpoint (us-east-1 only)
    PRICING_API_ENDPOINT = "https://pricing.us-east-1.amazonaws.com"

    def __init__(self, region: str = "us-east-1", cache_ttl: int = 3600):
        """
        Initialize AWS Pricing API client

        Args:
            region: AWS region for pricing (default: us-east-1)
            cache_ttl: Cache TTL in seconds (default: 1 hour)
        """
        self.region = region
        self.cache = PricingCache(ttl=cache_ttl)
        self.last_update = None

    def get_ec2_pricing(self, instance_type: str, region: str = None) -> Optional[Dict]:
        """
        Get EC2 instance pricing (live from AWS API)

        Args:
            instance_type: EC2 instance type (e.g., 't3.micro')
            region: AWS region (defaults to self.region)

        Returns:
            Dict with pricing info or None if not found
        """
        region = region or self.region
        cache_key = f"ec2_{instance_type}_{region}"

        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            # Try to fetch from AWS Pricing API
            price_data = self._fetch_ec2_price_from_api(instance_type, region)

            if price_data:
                self.cache.set(cache_key, price_data)
                return price_data
            else:
                # Fallback to static pricing if API fails
                return self._get_static_ec2_price(instance_type)

        except Exception as e:
            # Fallback to static pricing on error
            return self._get_static_ec2_price(instance_type)

    def _fetch_ec2_price_from_api(self, instance_type: str, region: str) -> Optional[Dict]:
        """
        Fetch EC2 pricing from AWS Pricing API

        Note: This is a simplified implementation. In production, you'd use boto3
        with AWS credentials. For now, we'll use a fallback approach.
        """
        # AWS Pricing API requires authentication
        # For this implementation, we'll return None to trigger fallback
        # In production, you would:
        # 1. Use boto3 with credentials
        # 2. Call pricing.get_products() with filters
        # 3. Parse the JSON response

        # Example of what the call would look like with boto3:
        # import boto3
        # pricing = boto3.client('pricing', region_name='us-east-1')
        # response = pricing.get_products(
        #     ServiceCode='AmazonEC2',
        #     Filters=[
        #         {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
        #         {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region_mapping[region]},
        #         {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
        #         {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
        #         {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
        #     ]
        # )

        return None  # Trigger fallback for now

    def _get_static_ec2_price(self, instance_type: str) -> Dict:
        """Fallback to static pricing data"""
        from analyzers.core.config import AWS_COST_ESTIMATES

        ec2_prices = AWS_COST_ESTIMATES.get("aws_instance", {})
        monthly_cost = ec2_prices.get(instance_type, 0.0)

        return {
            "instance_type": instance_type,
            "monthly_cost": monthly_cost,
            "hourly_cost": monthly_cost / 730,
            "source": "static_fallback",
            "updated_at": datetime.utcnow().isoformat(),
            "region": self.region,
            "note": "Using static pricing (AWS API requires credentials)"
        }

    def get_rds_pricing(self, instance_class: str, engine: str = "mysql") -> Optional[Dict]:
        """Get RDS instance pricing"""
        from analyzers.core.config import AWS_COST_ESTIMATES

        rds_prices = AWS_COST_ESTIMATES.get("aws_db_instance", {})
        monthly_cost = rds_prices.get(instance_class, 0.0)

        return {
            "instance_class": instance_class,
            "engine": engine,
            "monthly_cost": monthly_cost,
            "hourly_cost": monthly_cost / 730,
            "source": "static_fallback",
            "updated_at": datetime.utcnow().isoformat(),
            "region": self.region,
        }

    def get_ebs_pricing(self, volume_type: str, size_gb: int = 100) -> Optional[Dict]:
        """Get EBS volume pricing"""
        from analyzers.core.config import AWS_COST_ESTIMATES

        ebs_prices = AWS_COST_ESTIMATES.get("aws_ebs_volume", {})
        price_per_gb = ebs_prices.get(volume_type, 0.0)
        monthly_cost = price_per_gb * size_gb

        return {
            "volume_type": volume_type,
            "size_gb": size_gb,
            "price_per_gb": price_per_gb,
            "monthly_cost": monthly_cost,
            "source": "static_fallback",
            "updated_at": datetime.utcnow().isoformat(),
            "region": self.region,
        }

    def get_s3_pricing(self, storage_class: str = "standard", size_gb: int = 1000) -> Optional[Dict]:
        """Get S3 storage pricing"""
        from analyzers.core.config import AWS_COST_ESTIMATES

        s3_prices = AWS_COST_ESTIMATES.get("aws_s3_bucket", {})
        price_per_gb = s3_prices.get(storage_class, 0.023)
        monthly_cost = price_per_gb * size_gb

        return {
            "storage_class": storage_class,
            "size_gb": size_gb,
            "price_per_gb": price_per_gb,
            "monthly_cost": monthly_cost,
            "source": "static_fallback",
            "updated_at": datetime.utcnow().isoformat(),
            "region": self.region,
        }

    def get_pricing_status(self) -> Dict:
        """Get pricing API status"""
        return {
            "provider": "AWS",
            "region": self.region,
            "cache_size": self.cache.size(),
            "api_available": False,  # Would be True with boto3 credentials
            "using_fallback": True,
            "note": "Live AWS Pricing API requires boto3 and AWS credentials. Using static fallback."
        }
