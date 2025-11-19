"""
GCP Pricing API Integration
Fetches real-time pricing from Google Cloud Billing API (public, no auth required)

GCP provides public pricing APIs:
https://cloudbilling.googleapis.com/v1/services/{service}/skus
"""

import logging
import requests
from typing import Dict, Optional, List
from datetime import datetime
from devops_universal_scanner.core.pricing.pricing_cache import PricingCache

# Set up logger
logger = logging.getLogger(__name__)


class GCPPricingAPI:
    """
    Fetches live pricing from GCP Cloud Billing API

    GCP Cloud Billing API is PUBLIC and requires NO authentication!
    https://cloud.google.com/billing/v1/how-tos/catalog-api
    """

    # GCP Compute Engine service ID
    COMPUTE_ENGINE_SERVICE = "services/6F81-5844-456A"
    PRICING_API_BASE = "https://cloudbilling.googleapis.com/v1"

    def __init__(self, region: str = "us-east1", cache_ttl: int = 3600):
        self.region = region
        self.cache = PricingCache(ttl=cache_ttl)
        self.api_available = True
        self.initialization_error = None

        # Check if requests library is available
        self._check_requests_library()

    def _check_requests_library(self) -> bool:
        """Check if requests library is available for HTTP calls"""
        try:
            import requests
            self.api_available = True
            logger.info("GCP Cloud Billing API ready (public API, no credentials required)")
            return True
        except ImportError:
            self.api_available = False
            self.initialization_error = "requests library not installed"
            logger.warning("requests library not available - falling back to static pricing")
            return False

    def get_instance_pricing(self, machine_type: str, region: str = None) -> Optional[Dict]:
        """
        Get GCP instance pricing from live API

        Args:
            machine_type: GCP machine type (e.g., 'n1-standard-1')
            region: GCP region (defaults to self.region)

        Returns:
            Dict with pricing information
        """
        region = region or self.region
        cache_key = f"instance_{machine_type}_{region}"

        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Using cached pricing for {machine_type}")
            return cached

        # Try live API if available
        if self.api_available:
            try:
                price_data = self._fetch_instance_price_from_api(machine_type, region)
                if price_data:
                    self.cache.set(cache_key, price_data)
                    logger.info(f"Fetched live pricing for {machine_type} from GCP API")
                    return price_data
            except Exception as e:
                logger.error(f"GCP Pricing API call failed for {machine_type}: {e}")

        # Fallback to static pricing
        from devops_universal_scanner.core.data.cost_estimates import GCP_COST_ESTIMATES
        instance_prices = GCP_COST_ESTIMATES.get("google_compute_instance", {})
        monthly_cost = instance_prices.get(machine_type, 0.0)

        return {
            "machine_type": machine_type,
            "monthly_cost": monthly_cost,
            "hourly_cost": round(monthly_cost / 730, 4) if monthly_cost else 0.0,
            "source": "static_fallback",
            "updated_at": datetime.utcnow().isoformat(),
            "region": region,
            "fallback_reason": self.initialization_error or "API call failed"
        }

    def _fetch_instance_price_from_api(self, machine_type: str, region: str) -> Optional[Dict]:
        """
        Fetch instance pricing from GCP Cloud Billing API

        Args:
            machine_type: GCP machine type (e.g., 'n1-standard-1')
            region: GCP region (e.g., 'us-east1')

        Returns:
            Dict with pricing data or None if not found
        """
        try:
            # Query GCP Compute Engine SKUs
            url = f"{self.PRICING_API_BASE}/{self.COMPUTE_ENGINE_SERVICE}/skus"

            # Note: GCP API uses pageSize for pagination
            params = {
                "pageSize": 100  # Get first 100 SKUs (can paginate if needed)
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                logger.warning(f"GCP API returned status {response.status_code}")
                return None

            data = response.json()
            skus = data.get("skus", [])

            # Search for matching machine type SKU
            # SKU description format: "N1 Predefined Instance Core running in <region>"
            for sku in skus:
                description = sku.get("description", "")
                # Match machine type in description (simplified matching)
                if machine_type.lower() in description.lower() and region in description.lower():
                    # Extract pricing
                    pricing_info = sku.get("pricingInfo", [])
                    if not pricing_info:
                        continue

                    pricing_expression = pricing_info[0].get("pricingExpression", {})
                    tiered_rates = pricing_expression.get("tieredRates", [])

                    if not tiered_rates:
                        continue

                    # Get first tier (base rate)
                    base_rate = tiered_rates[0]
                    unit_price = base_rate.get("unitPrice", {})

                    # GCP prices are in nanos (10^-9)
                    nanos = unit_price.get("nanos", 0)
                    units = unit_price.get("units", "0")
                    hourly_price = float(units) + (nanos / 1_000_000_000)

                    # Calculate monthly cost (730 hours)
                    monthly_cost = hourly_price * 730

                    return {
                        "machine_type": machine_type,
                        "monthly_cost": round(monthly_cost, 2),
                        "hourly_cost": round(hourly_price, 4),
                        "source": "gcp_billing_api",
                        "updated_at": datetime.utcnow().isoformat(),
                        "region": region,
                        "currency": unit_price.get("currencyCode", "USD"),
                        "note": "Live pricing from GCP Cloud Billing API"
                    }

            logger.debug(f"No pricing data found for {machine_type} in {region}")
            return None

        except Exception as e:
            logger.error(f"Error fetching GCP pricing for {machine_type}: {e}")
            return None

    def get_pricing_status(self) -> Dict:
        """Get pricing API status"""
        status = "Live API" if self.api_available else "Using Fallback"

        status_dict = {
            "provider": "GCP",
            "region": self.region,
            "cache_size": self.cache.size(),
            "api_available": self.api_available,
            "using_fallback": not self.api_available,
            "status": status,
        }

        if not self.api_available:
            status_dict["note"] = f"Pricing API unavailable: {self.initialization_error or 'Unknown error'}"
            status_dict["fallback_data_source"] = "devops_universal_scanner/core/data/cost_estimates.py"
        else:
            status_dict["note"] = "Live GCP Cloud Billing API (public, no credentials required)"
            status_dict["api_info"] = "GCP Cloud Billing API is publicly accessible and requires no authentication"
            status_dict["endpoint"] = f"{self.PRICING_API_BASE}/{self.COMPUTE_ENGINE_SERVICE}/skus"

        return status_dict
