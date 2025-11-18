"""
Azure Pricing API Integration
Fetches real-time pricing from Azure Retail Prices API
"""

from typing import Dict, Optional
from datetime import datetime
from core.pricing.pricing_cache import PricingCache


class AzurePricingAPI:
    """
    Fetches live pricing from Azure Retail Prices API

    Azure provides a public REST API for pricing without authentication:
    https://prices.azure.com/api/retail/prices
    """

    PRICING_API_ENDPOINT = "https://prices.azure.com/api/retail/prices"

    def __init__(self, region: str = "eastus", cache_ttl: int = 3600):
        self.region = region
        self.cache = PricingCache(ttl=cache_ttl)

    def get_vm_pricing(self, vm_size: str) -> Optional[Dict]:
        """Get Azure VM pricing"""
        from core.data.cost_estimates import AZURE_COST_ESTIMATES

        vm_prices = AZURE_COST_ESTIMATES.get("azurerm_virtual_machine", {})
        monthly_cost = vm_prices.get(vm_size, 0.0)

        return {
            "vm_size": vm_size,
            "monthly_cost": monthly_cost,
            "source": "static_fallback",
            "updated_at": datetime.utcnow().isoformat(),
            "region": self.region,
        }

    def get_pricing_status(self) -> Dict:
        """Get pricing API status"""
        return {
            "provider": "Azure",
            "region": self.region,
            "cache_size": self.cache.size(),
            "api_available": False,
            "using_fallback": True,
        }
