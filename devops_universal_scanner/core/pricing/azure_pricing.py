"""
Azure Pricing API Integration
Fetches real-time pricing from Azure Retail Prices API
"""

import logging
import subprocess
from typing import Dict, Optional
from datetime import datetime
from devops_universal_scanner.core.pricing.pricing_cache import PricingCache

# Set up logger
logger = logging.getLogger(__name__)


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
        self.credentials_available = False
        self.initialization_error = None

        # Check Azure credentials
        self._check_azure_credentials()

    def _check_azure_credentials(self) -> bool:
        """
        Check if Azure credentials are configured using Azure CLI

        This works with all credential methods (az login, service principal,
        managed identity, etc.)

        Returns:
            bool: True if Azure credentials are configured and working
        """
        try:
            result = subprocess.run(
                ['az', 'account', 'show'],
                capture_output=True,
                timeout=5,
                text=True
            )
            # Exit code 0 means credentials work
            if result.returncode == 0:
                self.credentials_available = True
                logger.info("Azure credentials found and validated")
                return True
            else:
                self.initialization_error = "No Azure credentials configured"
                logger.debug("No Azure credentials - use 'az login' to authenticate")
                return False
        except subprocess.TimeoutExpired:
            logger.debug("Azure credential check timed out")
            self.initialization_error = "Azure CLI timeout"
            return False
        except FileNotFoundError:
            logger.debug("Azure CLI not installed")
            self.initialization_error = "Azure CLI not installed"
            return False
        except Exception as e:
            logger.debug(f"Azure credential check failed: {e}")
            self.initialization_error = f"Credential check failed: {str(e)}"
            return False

    def get_vm_pricing(self, vm_size: str) -> Optional[Dict]:
        """Get Azure VM pricing"""
        from devops_universal_scanner.core.data.cost_estimates import AZURE_COST_ESTIMATES

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
        status_dict = {
            "provider": "Azure",
            "region": self.region,
            "cache_size": self.cache.size(),
            "credentials_available": self.credentials_available,
            "api_available": False,  # TODO: Implement live API
            "using_fallback": True,
            "status": "Using Fallback"
        }

        if not self.credentials_available:
            status_dict["note"] = f"Azure credentials not configured. {self.initialization_error or 'Unknown error'}"
            status_dict["how_to_configure"] = "Run 'az login' to authenticate with Azure"
            status_dict["fallback_data_source"] = "devops_universal_scanner/core/data/cost_estimates.py"
        else:
            status_dict["note"] = "Azure credentials available but live API not yet implemented"

        return status_dict
