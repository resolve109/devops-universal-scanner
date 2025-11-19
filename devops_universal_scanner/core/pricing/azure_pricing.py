"""
Azure Pricing API Integration
Fetches real-time pricing from Azure Retail Prices API (public, no auth required)

Azure provides a public REST API for pricing:
https://prices.azure.com/api/retail/prices
"""

import logging
import requests
from typing import Dict, Optional
from datetime import datetime
from devops_universal_scanner.core.pricing.pricing_cache import PricingCache

# Set up logger
logger = logging.getLogger(__name__)


class AzurePricingAPI:
    """
    Fetches live pricing from Azure Retail Prices API

    Azure Retail Prices API is PUBLIC and requires NO authentication!
    https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices
    """

    PRICING_API_ENDPOINT = "https://prices.azure.com/api/retail/prices"

    def __init__(self, region: str = "eastus", cache_ttl: int = 3600):
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
            logger.info("Azure Retail Prices API ready (public API, no credentials required)")
            return True
        except ImportError:
            self.api_available = False
            self.initialization_error = "requests library not installed"
            logger.warning("requests library not available - falling back to static pricing")
            return False

    def get_vm_pricing(self, vm_size: str, region: str = None) -> Optional[Dict]:
        """
        Get Azure VM pricing from live API

        Args:
            vm_size: Azure VM size (e.g., 'Standard_B1s')
            region: Azure region (defaults to self.region)

        Returns:
            Dict with pricing information
        """
        region = region or self.region
        cache_key = f"vm_{vm_size}_{region}"

        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Using cached pricing for {vm_size}")
            return cached

        # Try live API if available
        if self.api_available:
            try:
                price_data = self._fetch_vm_price_from_api(vm_size, region)
                if price_data:
                    self.cache.set(cache_key, price_data)
                    logger.info(f"Fetched live pricing for {vm_size} from Azure API")
                    return price_data
            except Exception as e:
                logger.error(f"Azure Pricing API call failed for {vm_size}: {e}")

        # Fallback to static pricing
        from devops_universal_scanner.core.data.cost_estimates import AZURE_COST_ESTIMATES
        vm_prices = AZURE_COST_ESTIMATES.get("azurerm_virtual_machine", {})
        monthly_cost = vm_prices.get(vm_size, 0.0)

        return {
            "vm_size": vm_size,
            "monthly_cost": monthly_cost,
            "hourly_cost": round(monthly_cost / 730, 4) if monthly_cost else 0.0,
            "source": "static_fallback",
            "updated_at": datetime.utcnow().isoformat(),
            "region": region,
            "fallback_reason": self.initialization_error or "API call failed"
        }

    def _fetch_vm_price_from_api(self, vm_size: str, region: str) -> Optional[Dict]:
        """
        Fetch VM pricing from Azure Retail Prices API

        Args:
            vm_size: Azure VM size (e.g., 'Standard_B1s')
            region: Azure region (e.g., 'eastus')

        Returns:
            Dict with pricing data or None if not found
        """
        try:
            # Build API query
            # Example: https://prices.azure.com/api/retail/prices?$filter=serviceName eq 'Virtual Machines' and armRegionName eq 'eastus' and armSkuName eq 'Standard_B1s'
            filter_query = (
                f"serviceName eq 'Virtual Machines' "
                f"and armRegionName eq '{region}' "
                f"and armSkuName eq '{vm_size}' "
                f"and priceType eq 'Consumption'"
            )

            params = {
                "$filter": filter_query
            }

            response = requests.get(
                self.PRICING_API_ENDPOINT,
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                logger.warning(f"Azure API returned status {response.status_code}")
                return None

            data = response.json()
            items = data.get("Items", [])

            if not items:
                logger.debug(f"No pricing data found for {vm_size} in {region}")
                return None

            # Get first matching item (lowest cost)
            item = items[0]
            hourly_price = float(item.get("retailPrice", 0))
            monthly_cost = hourly_price * 730

            return {
                "vm_size": vm_size,
                "monthly_cost": round(monthly_cost, 2),
                "hourly_cost": round(hourly_price, 4),
                "source": "azure_retail_api",
                "updated_at": datetime.utcnow().isoformat(),
                "region": region,
                "currency": item.get("currencyCode", "USD"),
                "note": "Live pricing from Azure Retail Prices API"
            }

        except Exception as e:
            logger.error(f"Error fetching Azure pricing for {vm_size}: {e}")
            return None

    def get_pricing_status(self) -> Dict:
        """Get pricing API status"""
        status = "Live API" if self.api_available else "Using Fallback"

        status_dict = {
            "provider": "Azure",
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
            status_dict["note"] = "Live Azure Retail Prices API (public, no credentials required)"
            status_dict["api_info"] = "Azure Retail Prices API is publicly accessible and requires no authentication"
            status_dict["endpoint"] = self.PRICING_API_ENDPOINT

        return status_dict
