"""
AWS Pricing API Integration
Fetches real-time pricing from AWS Pricing API using boto3

Note: AWS Pricing API is only available in us-east-1 and ap-south-1
"""

import json
import logging
import subprocess
from typing import Dict, Optional, Tuple
from datetime import datetime
from devops_universal_scanner.core.pricing.pricing_cache import PricingCache

# Set up logger
logger = logging.getLogger(__name__)


# AWS region to location name mapping for Pricing API
AWS_REGION_LOCATION_MAP = {
    "us-east-1": "US East (N. Virginia)",
    "us-east-2": "US East (Ohio)",
    "us-west-1": "US West (N. California)",
    "us-west-2": "US West (Oregon)",
    "eu-west-1": "EU (Ireland)",
    "eu-west-2": "EU (London)",
    "eu-west-3": "EU (Paris)",
    "eu-central-1": "EU (Frankfurt)",
    "eu-north-1": "EU (Stockholm)",
    "ap-south-1": "Asia Pacific (Mumbai)",
    "ap-northeast-1": "Asia Pacific (Tokyo)",
    "ap-northeast-2": "Asia Pacific (Seoul)",
    "ap-southeast-1": "Asia Pacific (Singapore)",
    "ap-southeast-2": "Asia Pacific (Sydney)",
    "ca-central-1": "Canada (Central)",
    "sa-east-1": "South America (Sao Paulo)",
}


class AWSPricingAPI:
    """
    Fetches live pricing from AWS Pricing API using boto3

    Operations:
    1. get_ec2_pricing - Get EC2 instance pricing
    2. get_rds_pricing - Get RDS instance pricing
    3. get_ebs_pricing - Get EBS volume pricing
    4. get_s3_pricing - Get S3 storage pricing
    """

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
        self.boto3_available = False
        self.pricing_client = None
        self.credentials_available = False
        self.initialization_error = None

        # Try to initialize boto3
        self._initialize_boto3()

    def _initialize_boto3(self) -> None:
        """Initialize boto3 client and check for credentials using AWS CLI"""
        try:
            import boto3
            self.boto3_available = True
            logger.debug("boto3 is available")

            # Check AWS credentials using AWS CLI (simpler and more reliable)
            if self._check_aws_credentials():
                try:
                    # Create pricing client (Pricing API is only in us-east-1)
                    self.pricing_client = boto3.client('pricing', region_name='us-east-1')
                    self.credentials_available = True
                    logger.info("AWS credentials found and validated - Live pricing API enabled")
                except Exception as e:
                    self.initialization_error = f"Failed to create pricing client: {str(e)}"
                    logger.warning(f"Failed to create AWS Pricing client: {e}")
            else:
                self.initialization_error = "No AWS credentials configured"
                logger.warning("No AWS credentials configured - use 'aws configure' or set environment variables")

        except ImportError:
            self.boto3_available = False
            self.initialization_error = "boto3 not installed"
            logger.warning("boto3 not installed - falling back to static pricing")

    def _check_aws_credentials(self) -> bool:
        """
        Check if AWS credentials are configured using AWS CLI

        This is simpler and more reliable than boto3 credential detection
        because it works with ALL credential methods (env vars, ~/.aws/credentials,
        IAM roles, SSO, etc.)

        Returns:
            bool: True if AWS credentials are configured and working
        """
        try:
            result = subprocess.run(
                ['aws', 's3', 'ls'],
                capture_output=True,
                timeout=5,
                text=True
            )
            # Exit code 0 means credentials work
            # Exit code 255 or other means no credentials or AWS CLI not installed
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.debug("AWS credential check timed out")
            return False
        except FileNotFoundError:
            logger.debug("AWS CLI not installed")
            return False
        except Exception as e:
            logger.debug(f"AWS credential check failed: {e}")
            return False

    def get_ec2_pricing(self, instance_type: str, region: str = None) -> Optional[Dict]:
        """
        Get EC2 instance pricing (live from AWS API if credentials available)

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
            logger.debug(f"Using cached pricing for {instance_type}")
            return cached

        # Try live API if credentials available
        if self.credentials_available and self.pricing_client:
            try:
                price_data = self._fetch_ec2_price_from_api(instance_type, region)

                if price_data:
                    self.cache.set(cache_key, price_data)
                    logger.info(f"Fetched live pricing for {instance_type} from AWS API")
                    return price_data
                else:
                    logger.warning(f"No live pricing found for {instance_type}, using fallback")

            except Exception as e:
                logger.error(f"AWS Pricing API call failed for {instance_type}: {e}")

        # Fallback to static pricing
        fallback_data = self._get_static_ec2_price(instance_type, region)
        logger.debug(f"Using static fallback pricing for {instance_type}")
        return fallback_data

    def _fetch_ec2_price_from_api(self, instance_type: str, region: str) -> Optional[Dict]:
        """
        Fetch EC2 pricing from AWS Pricing API using boto3

        Args:
            instance_type: EC2 instance type (e.g., 't3.micro')
            region: AWS region code (e.g., 'us-east-1')

        Returns:
            Dict with pricing data or None if not found
        """
        if not self.pricing_client:
            return None

        # Convert region code to location name
        location = AWS_REGION_LOCATION_MAP.get(region)
        if not location:
            logger.warning(f"Unknown region: {region}, defaulting to us-east-1")
            location = AWS_REGION_LOCATION_MAP["us-east-1"]

        try:
            # Query AWS Pricing API
            response = self.pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                    {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                    {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                    {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'},
                ],
                MaxResults=1
            )

            if not response.get('PriceList'):
                logger.debug(f"No pricing data found for {instance_type} in {region}")
                return None

            # Parse the pricing data
            price_item = json.loads(response['PriceList'][0])

            # Extract on-demand pricing
            on_demand_terms = price_item.get('terms', {}).get('OnDemand', {})

            if not on_demand_terms:
                logger.warning(f"No on-demand pricing found for {instance_type}")
                return None

            # Get the first on-demand term
            term = list(on_demand_terms.values())[0]
            price_dimensions = term.get('priceDimensions', {})

            if not price_dimensions:
                return None

            # Get the first price dimension (hourly price)
            price_dim = list(price_dimensions.values())[0]
            hourly_price = float(price_dim['pricePerUnit']['USD'])

            # Calculate monthly cost (730 hours/month average)
            monthly_cost = hourly_price * 730

            return {
                "instance_type": instance_type,
                "monthly_cost": round(monthly_cost, 2),
                "hourly_cost": round(hourly_price, 4),
                "source": "aws_pricing_api",
                "updated_at": datetime.utcnow().isoformat(),
                "region": region,
                "location": location,
                "note": "Live pricing from AWS Pricing API"
            }

        except Exception as e:
            logger.error(f"Error fetching pricing for {instance_type}: {e}")
            return None

    def _get_static_ec2_price(self, instance_type: str, region: str = None) -> Dict:
        """
        Fallback to static pricing data

        Args:
            instance_type: EC2 instance type
            region: AWS region (optional)

        Returns:
            Dict with static pricing data
        """
        from devops_universal_scanner.core.data.cost_estimates import AWS_COST_ESTIMATES

        ec2_prices = AWS_COST_ESTIMATES.get("aws_instance", {})
        monthly_cost = ec2_prices.get(instance_type, 0.0)

        # Build fallback reason message
        if not self.boto3_available:
            fallback_reason = "boto3 not installed"
        elif not self.credentials_available:
            fallback_reason = self.initialization_error or "No AWS credentials"
        else:
            fallback_reason = "API call failed"

        return {
            "instance_type": instance_type,
            "monthly_cost": monthly_cost,
            "hourly_cost": round(monthly_cost / 730, 4) if monthly_cost else 0.0,
            "source": "static_fallback",
            "updated_at": datetime.utcnow().isoformat(),
            "region": region or self.region,
            "note": f"Static pricing (Fallback: {fallback_reason})",
            "fallback_reason": fallback_reason
        }

    def get_rds_pricing(self, instance_class: str, engine: str = "mysql", region: str = None) -> Optional[Dict]:
        """
        Get RDS instance pricing

        Args:
            instance_class: RDS instance class (e.g., 'db.t3.micro')
            engine: Database engine (default: 'mysql')
            region: AWS region (defaults to self.region)

        Returns:
            Dict with pricing info
        """
        region = region or self.region
        cache_key = f"rds_{instance_class}_{engine}_{region}"

        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Try live API if available
        if self.credentials_available and self.pricing_client:
            try:
                price_data = self._fetch_rds_price_from_api(instance_class, engine, region)
                if price_data:
                    self.cache.set(cache_key, price_data)
                    return price_data
            except Exception as e:
                logger.error(f"RDS pricing API call failed: {e}")

        # Fallback
        return self._get_static_rds_price(instance_class, engine, region)

    def _fetch_rds_price_from_api(self, instance_class: str, engine: str, region: str) -> Optional[Dict]:
        """Fetch RDS pricing from AWS API"""
        if not self.pricing_client:
            return None

        location = AWS_REGION_LOCATION_MAP.get(region, AWS_REGION_LOCATION_MAP["us-east-1"])

        try:
            response = self.pricing_client.get_products(
                ServiceCode='AmazonRDS',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_class},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                    {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': engine.capitalize()},
                    {'Type': 'TERM_MATCH', 'Field': 'deploymentOption', 'Value': 'Single-AZ'},
                ],
                MaxResults=1
            )

            if not response.get('PriceList'):
                return None

            price_item = json.loads(response['PriceList'][0])
            on_demand_terms = price_item.get('terms', {}).get('OnDemand', {})

            if not on_demand_terms:
                return None

            term = list(on_demand_terms.values())[0]
            price_dimensions = term.get('priceDimensions', {})
            price_dim = list(price_dimensions.values())[0]
            hourly_price = float(price_dim['pricePerUnit']['USD'])
            monthly_cost = hourly_price * 730

            return {
                "instance_class": instance_class,
                "engine": engine,
                "monthly_cost": round(monthly_cost, 2),
                "hourly_cost": round(hourly_price, 4),
                "source": "aws_pricing_api",
                "updated_at": datetime.utcnow().isoformat(),
                "region": region,
                "location": location,
            }

        except Exception as e:
            logger.error(f"Error fetching RDS pricing: {e}")
            return None

    def _get_static_rds_price(self, instance_class: str, engine: str, region: str = None) -> Dict:
        """Fallback to static RDS pricing"""
        from devops_universal_scanner.core.data.cost_estimates import AWS_COST_ESTIMATES

        rds_prices = AWS_COST_ESTIMATES.get("aws_db_instance", {})
        monthly_cost = rds_prices.get(instance_class, 0.0)

        fallback_reason = self._get_fallback_reason()

        return {
            "instance_class": instance_class,
            "engine": engine,
            "monthly_cost": monthly_cost,
            "hourly_cost": round(monthly_cost / 730, 4) if monthly_cost else 0.0,
            "source": "static_fallback",
            "updated_at": datetime.utcnow().isoformat(),
            "region": region or self.region,
            "fallback_reason": fallback_reason
        }

    def get_ebs_pricing(self, volume_type: str, size_gb: int = 100, region: str = None) -> Optional[Dict]:
        """Get EBS volume pricing"""
        from devops_universal_scanner.core.data.cost_estimates import AWS_COST_ESTIMATES

        region = region or self.region
        ebs_prices = AWS_COST_ESTIMATES.get("aws_ebs_volume", {})
        price_per_gb = ebs_prices.get(volume_type, 0.0)
        monthly_cost = price_per_gb * size_gb

        return {
            "volume_type": volume_type,
            "size_gb": size_gb,
            "price_per_gb": price_per_gb,
            "monthly_cost": round(monthly_cost, 2),
            "source": "static_fallback",
            "updated_at": datetime.utcnow().isoformat(),
            "region": region,
            "fallback_reason": self._get_fallback_reason()
        }

    def get_s3_pricing(self, storage_class: str = "standard", size_gb: int = 1000, region: str = None) -> Optional[Dict]:
        """Get S3 storage pricing"""
        from devops_universal_scanner.core.data.cost_estimates import AWS_COST_ESTIMATES

        region = region or self.region
        s3_prices = AWS_COST_ESTIMATES.get("aws_s3_bucket", {})
        price_per_gb = s3_prices.get(storage_class, 0.023)
        monthly_cost = price_per_gb * size_gb

        return {
            "storage_class": storage_class,
            "size_gb": size_gb,
            "price_per_gb": price_per_gb,
            "monthly_cost": round(monthly_cost, 2),
            "source": "static_fallback",
            "updated_at": datetime.utcnow().isoformat(),
            "region": region,
            "fallback_reason": self._get_fallback_reason()
        }

    def _get_fallback_reason(self) -> str:
        """Get the reason for using fallback pricing"""
        if not self.boto3_available:
            return "boto3 not installed"
        elif not self.credentials_available:
            return self.initialization_error or "No AWS credentials"
        else:
            return "API call failed"

    def get_pricing_status(self) -> Dict:
        """
        Get pricing API status and configuration

        Returns:
            Dict with detailed status information
        """
        status = "Live API" if self.credentials_available else "Using Fallback"

        status_dict = {
            "provider": "AWS",
            "region": self.region,
            "cache_size": self.cache.size(),
            "boto3_available": self.boto3_available,
            "credentials_available": self.credentials_available,
            "api_available": self.credentials_available,
            "using_fallback": not self.credentials_available,
            "status": status,
        }

        # Add detailed error message if using fallback
        if not self.credentials_available:
            if not self.boto3_available:
                status_dict["note"] = "boto3 not installed. Install with: pip install boto3"
                status_dict["fallback_data_source"] = "devops_universal_scanner/core/data/cost_estimates.py"
            else:
                status_dict["note"] = f"AWS credentials not configured. {self.initialization_error or 'Unknown error'}"
                status_dict["how_to_configure"] = "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables, or configure with 'aws configure'"
                status_dict["fallback_data_source"] = "devops_universal_scanner/core/data/cost_estimates.py"
        else:
            status_dict["note"] = "Live AWS Pricing API is active"
            status_dict["last_update"] = self.last_update or "Not yet fetched"

        return status_dict
