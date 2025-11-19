"""
GCP Pricing API Integration
Fetches real-time pricing from Google Cloud Billing API
"""

import logging
import subprocess
from typing import Dict, Optional
from datetime import datetime
from devops_universal_scanner.core.pricing.pricing_cache import PricingCache

# Set up logger
logger = logging.getLogger(__name__)


class GCPPricingAPI:
    """
    Fetches live pricing from GCP Cloud Billing API
    """

    def __init__(self, region: str = "us-east1", cache_ttl: int = 3600):
        self.region = region
        self.cache = PricingCache(ttl=cache_ttl)
        self.credentials_available = False
        self.initialization_error = None

        # Check GCP credentials
        self._check_gcp_credentials()

    def _check_gcp_credentials(self) -> bool:
        """
        Check if GCP credentials are configured using gcloud CLI

        This works with all credential methods (gcloud auth login, service account,
        application default credentials, etc.)

        Returns:
            bool: True if GCP credentials are configured and working
        """
        try:
            result = subprocess.run(
                ['gcloud', 'auth', 'list', '--filter=status:ACTIVE', '--format=value(account)'],
                capture_output=True,
                timeout=5,
                text=True
            )
            # Exit code 0 and non-empty output means credentials work
            if result.returncode == 0 and result.stdout.strip():
                self.credentials_available = True
                logger.info("GCP credentials found and validated")
                return True
            else:
                self.initialization_error = "No GCP credentials configured"
                logger.debug("No GCP credentials - use 'gcloud auth login' to authenticate")
                return False
        except subprocess.TimeoutExpired:
            logger.debug("GCP credential check timed out")
            self.initialization_error = "gcloud CLI timeout"
            return False
        except FileNotFoundError:
            logger.debug("gcloud CLI not installed")
            self.initialization_error = "gcloud CLI not installed"
            return False
        except Exception as e:
            logger.debug(f"GCP credential check failed: {e}")
            self.initialization_error = f"Credential check failed: {str(e)}"
            return False

    def get_instance_pricing(self, machine_type: str) -> Optional[Dict]:
        """Get GCP instance pricing"""
        from devops_universal_scanner.core.data.cost_estimates import GCP_COST_ESTIMATES

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
        status_dict = {
            "provider": "GCP",
            "region": self.region,
            "cache_size": self.cache.size(),
            "credentials_available": self.credentials_available,
            "api_available": False,  # TODO: Implement live API
            "using_fallback": True,
            "status": "Using Fallback"
        }

        if not self.credentials_available:
            status_dict["note"] = f"GCP credentials not configured. {self.initialization_error or 'Unknown error'}"
            status_dict["how_to_configure"] = "Run 'gcloud auth login' to authenticate with GCP"
            status_dict["fallback_data_source"] = "devops_universal_scanner/core/data/cost_estimates.py"
        else:
            status_dict["note"] = "GCP credentials available but live API not yet implemented"

        return status_dict
