"""
AMI Alternative Finder
Provides specific AMI ID recommendations as alternatives to vulnerable/outdated AMIs

Features:
1. AWS SSM Parameter Store via public API (NO credentials required)
2. Canonical's Ubuntu Cloud Images API for latest Ubuntu AMIs
3. Region-aware AMI recommendations
4. Architecture-specific recommendations (x86_64, arm64)
5. 100% web-based - no fallback databases
"""

import requests
import json
import re
from typing import List, Optional, Dict
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AMIAlternative:
    """AMI alternative recommendation"""
    ami_id: str
    name: str
    distribution: str
    version: str
    region: str
    architecture: str = "x86_64"
    last_updated: Optional[str] = None
    source: str = "AWS SSM"  # 'AWS SSM' or 'Fallback Database'


class AMIAlternativeFinder:
    """
    Finds alternative AMI IDs for vulnerable/outdated AMIs

    Supports:
    - Amazon Linux 2023, Amazon Linux 2
    - Ubuntu LTS versions
    - Multi-region support
    - Graceful degradation when AWS API unavailable
    """

    # AWS SSM Parameter Store paths for official AMIs
    SSM_PARAMETERS = {
        "amazon_linux_2023_x86_64": "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64",
        "amazon_linux_2023_arm64": "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64",
        "amazon_linux_2_x86_64": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
        "amazon_linux_2_arm64": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-arm64-gp2",
        "ubuntu_24_04_x86_64": "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp2/ami-id",
        "ubuntu_22_04_x86_64": "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id",
        "ubuntu_20_04_x86_64": "/aws/service/canonical/ubuntu/server/20.04/stable/current/amd64/hvm/ebs-gp2/ami-id",
    }

    # Canonical Ubuntu Cloud Images API
    UBUNTU_CLOUD_IMAGES_API = "https://cloud-images.ubuntu.com/locator/ec2/releasesTable"

    def __init__(self, region: str = "us-east-1"):
        """
        Initialize AMI Alternative Finder

        Args:
            region: AWS region for AMI lookups (default: us-east-1)
        """
        self.region = region
        self.boto3_available = False
        self.ssm_client = None

        # Try to initialize boto3 for SSM access (anonymous, no credentials needed)
        try:
            import boto3
            from botocore.config import Config
            from botocore import UNSIGNED

            self.ssm_client = boto3.client(
                'ssm',
                region_name=region,
                config=Config(signature_version=UNSIGNED)
            )
            self.boto3_available = True
            logger.info(f"AMI Finder initialized with boto3 (region: {region})")
        except ImportError:
            logger.warning("boto3 not available - will use HTTP fallback for AMI lookups")
        except Exception as e:
            logger.warning(f"Failed to initialize boto3 SSM client: {e}")

    def _get_ami_from_ssm(self, parameter_path: str) -> Optional[str]:
        """
        Get AMI ID from AWS SSM Parameter Store (public, no auth required)

        Args:
            parameter_path: SSM parameter path

        Returns:
            AMI ID or None if unavailable
        """
        # Try boto3 first (fastest)
        if self.ssm_client:
            try:
                response = self.ssm_client.get_parameter(Name=parameter_path)
                ami_id = response['Parameter']['Value']
                if ami_id.startswith('ami-'):
                    logger.debug(f"Got AMI from SSM: {ami_id}")
                    return ami_id
            except Exception as e:
                logger.debug(f"SSM parameter fetch failed: {e}")

        # Fallback to HTTP request to AWS SSM public API
        try:
            # AWS SSM has a public HTTP endpoint we can query
            url = f"https://ssm.{self.region}.amazonaws.com/"
            params = {
                'Action': 'GetParameter',
                'Name': parameter_path,
                'Version': '2014-11-06'
            }
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                # Parse XML response for AMI ID
                ami_match = re.search(r'ami-[a-f0-9]{8,17}', response.text)
                if ami_match:
                    ami_id = ami_match.group(0)
                    logger.debug(f"Got AMI from SSM HTTP: {ami_id}")
                    return ami_id
        except Exception as e:
            logger.debug(f"HTTP SSM fetch failed: {e}")

        return None

    def find_alternatives(
        self,
        distribution: str = "amazon_linux_2023",
        architecture: str = "x86_64",
        count: int = 3
    ) -> List[AMIAlternative]:
        """
        Find alternative AMI recommendations from live web sources

        Args:
            distribution: Distribution name (amazon_linux_2023, ubuntu_24_04, etc.)
            architecture: CPU architecture (x86_64 or arm64)
            count: Number of alternatives to return

        Returns:
            List of AMIAlternative objects
        """
        alternatives = []
        key = f"{distribution}_{architecture}"

        # Try AWS SSM for Amazon/Ubuntu official AMIs
        if key in self.SSM_PARAMETERS:
            ami_id = self._get_ami_from_ssm(self.SSM_PARAMETERS[key])
            if ami_id:
                alternatives.append(AMIAlternative(
                    ami_id=ami_id,
                    name=self._get_friendly_name(distribution),
                    distribution=self._get_friendly_name(distribution),
                    version="Latest",
                    region=self.region,
                    architecture=architecture,
                    last_updated=datetime.utcnow().strftime('%Y-%m-%d'),
                    source="AWS SSM Public API"
                ))

        # Try Canonical Ubuntu Cloud Images API for Ubuntu
        if "ubuntu" in distribution and len(alternatives) < count:
            ubuntu_amis = self._get_ubuntu_amis_from_web(distribution, architecture)
            alternatives.extend(ubuntu_amis[:(count - len(alternatives))])

        # If no matches, provide popular alternatives from web
        if not alternatives:
            alternatives.extend(self._get_popular_alternatives(architecture))

        return alternatives[:count]

    def _get_ubuntu_amis_from_web(self, distribution: str, architecture: str) -> List[AMIAlternative]:
        """
        Fetch latest Ubuntu AMI IDs from Canonical's Cloud Images API

        Args:
            distribution: Ubuntu distribution (e.g., "ubuntu_22_04")
            architecture: CPU architecture (x86_64 or arm64)

        Returns:
            List of AMIAlternative objects
        """
        alternatives = []

        try:
            # Canonical provides a JSON endpoint with current AMIs
            # Parse version from distribution name
            version = distribution.replace("ubuntu_", "").replace("_", ".")

            response = requests.get(self.UBUNTU_CLOUD_IMAGES_API, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Ubuntu Cloud Images API returned {response.status_code}")
                return alternatives

            # Parse JSON response
            data = response.json()

            # Filter for matching region, version, and architecture
            arch_map = {"x86_64": "amd64", "arm64": "arm64"}
            target_arch = arch_map.get(architecture, "amd64")

            for item in data.get('aaData', []):
                # Item format: [zone, name, version, arch, instance_type, release, ami_id, aki_id]
                if len(item) < 7:
                    continue

                item_region = item[0]
                item_version = item[2]
                item_arch = item[3]
                ami_id = item[6]

                if (self.region in item_region and
                    version in item_version and
                    target_arch == item_arch and
                    ami_id.startswith('ami-')):

                    alternatives.append(AMIAlternative(
                        ami_id=ami_id,
                        name=f"Ubuntu Server {version} LTS",
                        distribution=f"Ubuntu Server {version} LTS",
                        version=item_version,
                        region=self.region,
                        architecture=architecture,
                        last_updated=datetime.utcnow().strftime('%Y-%m-%d'),
                        source="Canonical Cloud Images API"
                    ))

                    if len(alternatives) >= 2:
                        break

        except Exception as e:
            logger.warning(f"Failed to fetch Ubuntu AMIs from web: {e}")

        return alternatives

    def _get_friendly_name(self, distribution: str) -> str:
        """Convert distribution key to friendly name"""
        mapping = {
            "amazon_linux_2023": "Amazon Linux 2023",
            "amazon_linux_2": "Amazon Linux 2",
            "ubuntu_24_04": "Ubuntu Server 24.04 LTS",
            "ubuntu_22_04": "Ubuntu Server 22.04 LTS",
            "ubuntu_20_04": "Ubuntu Server 20.04 LTS",
        }
        return mapping.get(distribution, distribution)

    def _get_popular_alternatives(self, architecture: str = "x86_64") -> List[AMIAlternative]:
        """
        Get popular AMI alternatives from live web sources

        Tries multiple sources:
        1. Amazon Linux 2023 from AWS SSM
        2. Ubuntu 22.04 LTS from AWS SSM or Canonical API

        Args:
            architecture: CPU architecture

        Returns:
            List of AMIAlternative objects from live sources
        """
        popular = []

        # 1. Amazon Linux 2023 (recommended default) from AWS SSM
        al2023_key = f"amazon_linux_2023_{architecture}"
        if al2023_key in self.SSM_PARAMETERS:
            ami_id = self._get_ami_from_ssm(self.SSM_PARAMETERS[al2023_key])
            if ami_id:
                popular.append(AMIAlternative(
                    ami_id=ami_id,
                    name="Amazon Linux 2023 (Recommended)",
                    distribution="Amazon Linux 2023",
                    version="Latest",
                    region=self.region,
                    architecture=architecture,
                    last_updated=datetime.utcnow().strftime('%Y-%m-%d'),
                    source="AWS SSM Public API"
                ))

        # 2. Ubuntu 22.04 LTS from AWS SSM or Canonical API
        if len(popular) < 2:
            ubuntu_key = f"ubuntu_22_04_{architecture}"
            if ubuntu_key in self.SSM_PARAMETERS:
                ami_id = self._get_ami_from_ssm(self.SSM_PARAMETERS[ubuntu_key])
                if ami_id:
                    popular.append(AMIAlternative(
                        ami_id=ami_id,
                        name="Ubuntu Server 22.04 LTS",
                        distribution="Ubuntu Server 22.04 LTS",
                        version="22.04",
                        region=self.region,
                        architecture=architecture,
                        last_updated=datetime.utcnow().strftime('%Y-%m-%d'),
                        source="AWS SSM Public API"
                    ))

        # 3. If still no results, try Ubuntu from Canonical API
        if not popular:
            ubuntu_amis = self._get_ubuntu_amis_from_web("ubuntu_22_04", architecture)
            popular.extend(ubuntu_amis[:2])

        return popular

    def get_recommendation_for_ami(self, ami_id: str) -> List[AMIAlternative]:
        """
        Get recommendations for a specific AMI

        Args:
            ami_id: AMI ID to find alternatives for

        Returns:
            List of AMIAlternative objects
        """
        # Default to Amazon Linux 2023 (most common)
        recommendations = self.find_alternatives("amazon_linux_2023", "x86_64", count=2)

        # Add Ubuntu as alternative
        ubuntu_alts = self.find_alternatives("ubuntu_24_04", "x86_64", count=1)
        recommendations.extend(ubuntu_alts)

        return recommendations[:3]
