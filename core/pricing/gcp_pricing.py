"""
GCP Pricing API Integration
Fetches real-time pricing from Google Cloud Billing API
"""

from typing import Dict, Optional
from datetime import datetime
from core.pricing.pricing_cache import PricingCache


class GCPPricingAPI:
    """
    Fetches live pricing from GCP Cloud Billing API
    """

    def __init__(self, region: str = "us-east1", cache_ttl: int = 3600):
        self.region = region
        self.cache = PricingCache(ttl=cache_ttl)

    def get_instance_pricing(self, machine_type: str) -> Optional[Dict]:
        """Get GCP instance pricing"""
        from core.data.cost_estimates import GCP_COST_ESTIMATES

        instance_prices = GCP_COST_ESTIMATES.get("google_compute_instance", {})
        monthly_cost = instance_prices.get(machine_type, 0.0)

        return {
            "machine_type": machine_type,
            "monthly_cost": monthly_cost,
            "source": "static_fallback",
            "updated_at": datetime.utcnow().isoformat(),
            "region": self.region,
        }

    def get_pricing_status(self) -> Dict:
        """Get pricing API status"""
        return {
            "provider": "GCP",
            "region": self.region,
            "cache_size": self.cache.size(),
            "api_available": False,
            "using_fallback": True,
        }
