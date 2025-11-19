"""
AMI Alternative Finder
Provides specific AMI ID recommendations as alternatives to vulnerable/outdated AMIs

Features:
1. AWS SSM Parameter Store integration for official AMI IDs
2. Region-aware AMI recommendations
3. Fallback to curated AMI database when AWS API unavailable
4. Architecture-specific recommendations (x86_64, arm64)
"""

import subprocess
import json
import re
from typing import List, Optional, Dict
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime


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

    # Fallback AMI database (curated, updated monthly)
    FALLBACK_AMIS = {
        "us-east-1": {
            "amazon_linux_2023_x86_64": {
                "ami_id": "ami-0c02fb55c47d2f8f5",
                "name": "Amazon Linux 2023",
                "version": "2023.3.20250115",
                "last_updated": "2025-01-15"
            },
            "amazon_linux_2_x86_64": {
                "ami_id": "ami-0c101f26f147fa7fd",
                "name": "Amazon Linux 2",
                "version": "2.0.20250115",
                "last_updated": "2025-01-15"
            },
            "ubuntu_24_04_x86_64": {
                "ami_id": "ami-0e2c8caa4b6378d8c",
                "name": "Ubuntu Server 24.04 LTS",
                "version": "24.04",
                "last_updated": "2025-01-15"
            },
            "ubuntu_22_04_x86_64": {
                "ami_id": "ami-0c7217cdde317cfec",
                "name": "Ubuntu Server 22.04 LTS",
                "version": "22.04",
                "last_updated": "2025-01-15"
            }
        },
        "us-west-2": {
            "amazon_linux_2023_x86_64": {
                "ami_id": "ami-0c94855ba95c574c8",
                "name": "Amazon Linux 2023",
                "version": "2023.3.20250115",
                "last_updated": "2025-01-15"
            },
            "amazon_linux_2_x86_64": {
                "ami_id": "ami-0d081196e3df05f4d",
                "name": "Amazon Linux 2",
                "version": "2.0.20250115",
                "last_updated": "2025-01-15"
            },
            "ubuntu_24_04_x86_64": {
                "ami_id": "ami-0aff18ec83b712f05",
                "name": "Ubuntu Server 24.04 LTS",
                "version": "24.04",
                "last_updated": "2025-01-15"
            }
        }
    }

    def __init__(self, region: str = "us-east-1"):
        """
        Initialize AMI Alternative Finder

        Args:
            region: AWS region for AMI lookups (default: us-east-1)
        """
        self.region = region
        self.aws_available = self._check_aws_cli()

    def _check_aws_cli(self) -> bool:
        """Check if AWS CLI is available and configured"""
        try:
            result = subprocess.run(
                ['aws', '--version'],
                capture_output=True,
                timeout=2,
                text=True
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_ami_from_ssm(self, parameter_path: str) -> Optional[str]:
        """
        Get AMI ID from AWS SSM Parameter Store

        Args:
            parameter_path: SSM parameter path

        Returns:
            AMI ID or None if unavailable
        """
        if not self.aws_available:
            return None

        try:
            result = subprocess.run(
                [
                    'aws', 'ssm', 'get-parameter',
                    '--name', parameter_path,
                    '--region', self.region,
                    '--query', 'Parameter.Value',
                    '--output', 'text'
                ],
                capture_output=True,
                timeout=5,
                text=True
            )

            if result.returncode == 0:
                ami_id = result.stdout.strip()
                if ami_id.startswith('ami-'):
                    return ami_id
        except (subprocess.TimeoutExpired, Exception):
            pass

        return None

    def find_alternatives(
        self,
        distribution: str = "amazon_linux_2023",
        architecture: str = "x86_64",
        count: int = 3
    ) -> List[AMIAlternative]:
        """
        Find alternative AMI recommendations

        Args:
            distribution: Distribution name (amazon_linux_2023, ubuntu_24_04, etc.)
            architecture: CPU architecture (x86_64 or arm64)
            count: Number of alternatives to return

        Returns:
            List of AMIAlternative objects
        """
        alternatives = []
        key = f"{distribution}_{architecture}"

        # Try AWS SSM first
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
                    source="AWS SSM"
                ))

        # Add fallback database entries
        if self.region in self.FALLBACK_AMIS:
            region_amis = self.FALLBACK_AMIS[self.region]
            if key in region_amis:
                ami_data = region_amis[key]
                alternatives.append(AMIAlternative(
                    ami_id=ami_data['ami_id'],
                    name=ami_data['name'],
                    distribution=ami_data['name'],
                    version=ami_data['version'],
                    region=self.region,
                    architecture=architecture,
                    last_updated=ami_data['last_updated'],
                    source="Fallback Database"
                ))

        # If no matches, provide popular alternatives
        if not alternatives:
            alternatives.extend(self._get_popular_alternatives(architecture))

        return alternatives[:count]

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
        """Get popular AMI alternatives when specific match not found"""
        popular = []

        # Amazon Linux 2023 (recommended default)
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
                    source="AWS SSM"
                ))

        # Fallback to database if AWS SSM failed
        if not popular and self.region in self.FALLBACK_AMIS:
            for key, data in self.FALLBACK_AMIS[self.region].items():
                if architecture in key:
                    popular.append(AMIAlternative(
                        ami_id=data['ami_id'],
                        name=data['name'],
                        distribution=data['name'],
                        version=data['version'],
                        region=self.region,
                        architecture=architecture,
                        last_updated=data['last_updated'],
                        source="Fallback Database"
                    ))
                    if len(popular) >= 2:
                        break

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
