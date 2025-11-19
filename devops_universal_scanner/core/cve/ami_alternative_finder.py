"""
AMI Alternative Finder
Provides specific AMI ID recommendations as alternatives to vulnerable/outdated AMIs

Uses AWS CLI and Azure CLI for real-time image lookups:
1. AWS CLI: `aws ec2 describe-images --owners amazon --profile default`
2. Azure CLI: `az vm image list --all --publisher Canonical`
3. GCP CLI: `gcloud compute images list --project ubuntu-os-cloud`
"""

import json
import subprocess
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AMIAlternative:
    """AMI/Image alternative recommendation"""
    ami_id: str
    name: str
    distribution: str
    version: str
    region: str
    architecture: str = "x86_64"
    last_updated: Optional[str] = None
    source: str = "AWS CLI"


class AMIAlternativeFinder:
    """
    Finds alternative AMI IDs for vulnerable/outdated AMIs using CLI tools

    Supports:
    - AWS CLI for AMI lookups (--profile default)
    - Azure CLI for VM image lookups
    - GCP gcloud for compute image lookups
    - Multi-region support
    """

    def __init__(self, region: str = "us-east-1", aws_profile: str = "default"):
        """
        Initialize AMI Alternative Finder

        Args:
            region: AWS region for AMI lookups (default: us-east-1)
            aws_profile: AWS CLI profile to use (default: default)
        """
        self.region = region
        self.aws_profile = aws_profile
        self.aws_available = self._check_aws_cli()
        self.azure_available = self._check_azure_cli()
        self.gcp_available = self._check_gcp_cli()

        if self.aws_available:
            logger.info(f"AMI Finder initialized with AWS CLI (region: {region}, profile: {aws_profile})")
        else:
            logger.warning("AWS CLI not available - AMI lookups will be limited")

    def _check_aws_cli(self) -> bool:
        """Check if AWS CLI is available"""
        try:
            result = subprocess.run(
                ["aws", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_azure_cli(self) -> bool:
        """Check if Azure CLI is available"""
        try:
            result = subprocess.run(
                ["az", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_gcp_cli(self) -> bool:
        """Check if GCP gcloud CLI is available"""
        try:
            result = subprocess.run(
                ["gcloud", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_amazon_linux_amis(self, architecture: str = "x86_64") -> List[AMIAlternative]:
        """
        Get latest Amazon Linux AMIs using AWS CLI

        Args:
            architecture: CPU architecture (x86_64 or arm64)

        Returns:
            List of AMIAlternative objects
        """
        if not self.aws_available:
            logger.warning("AWS CLI not available")
            return []

        alternatives = []

        # Map architecture to AWS filter format
        arch_map = {"x86_64": "x86_64", "arm64": "arm64"}
        aws_arch = arch_map.get(architecture, "x86_64")

        try:
            # Get Amazon Linux 2023 (latest)
            cmd = [
                "aws", "ec2", "describe-images",
                "--owners", "amazon",
                "--filters",
                "Name=name,Values=al2023-ami-*",
                f"Name=architecture,Values={aws_arch}",
                "Name=root-device-type,Values=ebs",
                "Name=virtualization-type,Values=hvm",
                "--query", "Images | sort_by(@, &CreationDate) | [-1].[ImageId,Name,CreationDate]",
                "--output", "json",
                "--region", self.region,
                "--profile", self.aws_profile
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data and len(data) > 0:
                    ami_id, name, created = data[0], data[1] if len(data) > 1 else "Amazon Linux 2023", data[2] if len(data) > 2 else ""
                    alternatives.append(AMIAlternative(
                        ami_id=ami_id,
                        name="Amazon Linux 2023 (Latest)",
                        distribution="Amazon Linux 2023",
                        version="2023",
                        region=self.region,
                        architecture=architecture,
                        last_updated=created.split('T')[0] if created else datetime.utcnow().strftime('%Y-%m-%d'),
                        source="AWS CLI"
                    ))
                    logger.debug(f"Found Amazon Linux 2023 AMI: {ami_id}")

            # Get Amazon Linux 2 as fallback
            cmd_al2 = [
                "aws", "ec2", "describe-images",
                "--owners", "amazon",
                "--filters",
                "Name=name,Values=amzn2-ami-hvm-*",
                f"Name=architecture,Values={aws_arch}",
                "Name=root-device-type,Values=ebs",
                "Name=virtualization-type,Values=hvm",
                "--query", "Images | sort_by(@, &CreationDate) | [-1].[ImageId,Name,CreationDate]",
                "--output", "json",
                "--region", self.region,
                "--profile", self.aws_profile
            ]

            result_al2 = subprocess.run(
                cmd_al2,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result_al2.returncode == 0:
                data_al2 = json.loads(result_al2.stdout)
                if data_al2 and len(data_al2) > 0:
                    ami_id, name, created = data_al2[0], data_al2[1] if len(data_al2) > 1 else "Amazon Linux 2", data_al2[2] if len(data_al2) > 2 else ""
                    alternatives.append(AMIAlternative(
                        ami_id=ami_id,
                        name="Amazon Linux 2 (Latest)",
                        distribution="Amazon Linux 2",
                        version="2",
                        region=self.region,
                        architecture=architecture,
                        last_updated=created.split('T')[0] if created else datetime.utcnow().strftime('%Y-%m-%d'),
                        source="AWS CLI"
                    ))
                    logger.debug(f"Found Amazon Linux 2 AMI: {ami_id}")

        except subprocess.TimeoutExpired:
            logger.error("AWS CLI command timed out")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AWS CLI output: {e}")
        except Exception as e:
            logger.error(f"Failed to get Amazon Linux AMIs: {e}")

        return alternatives

    def _get_ubuntu_amis(self, version: str = "22.04", architecture: str = "x86_64") -> List[AMIAlternative]:
        """
        Get latest Ubuntu LTS AMIs using AWS CLI

        Args:
            version: Ubuntu version (20.04, 22.04, 24.04)
            architecture: CPU architecture (x86_64 or arm64)

        Returns:
            List of AMIAlternative objects
        """
        if not self.aws_available:
            logger.warning("AWS CLI not available")
            return []

        alternatives = []

        # Map architecture to AWS filter format
        arch_map = {"x86_64": "x86_64", "arm64": "arm64"}
        aws_arch = arch_map.get(architecture, "x86_64")

        # Canonical's owner ID
        canonical_owner = "099720109477"

        try:
            # Get latest Ubuntu LTS
            version_clean = version.replace(".", "")  # 22.04 -> 2204
            cmd = [
                "aws", "ec2", "describe-images",
                "--owners", canonical_owner,
                "--filters",
                f"Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-*-{version}-*-server-*",
                f"Name=architecture,Values={aws_arch}",
                "Name=root-device-type,Values=ebs",
                "Name=virtualization-type,Values=hvm",
                "--query", "Images | sort_by(@, &CreationDate) | [-1].[ImageId,Name,CreationDate]",
                "--output", "json",
                "--region", self.region,
                "--profile", self.aws_profile
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data and len(data) > 0:
                    ami_id, name, created = data[0], data[1] if len(data) > 1 else f"Ubuntu {version}", data[2] if len(data) > 2 else ""
                    alternatives.append(AMIAlternative(
                        ami_id=ami_id,
                        name=f"Ubuntu Server {version} LTS (Latest)",
                        distribution=f"Ubuntu Server {version} LTS",
                        version=version,
                        region=self.region,
                        architecture=architecture,
                        last_updated=created.split('T')[0] if created else datetime.utcnow().strftime('%Y-%m-%d'),
                        source="AWS CLI"
                    ))
                    logger.debug(f"Found Ubuntu {version} AMI: {ami_id}")

        except subprocess.TimeoutExpired:
            logger.error("AWS CLI command timed out")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AWS CLI output: {e}")
        except Exception as e:
            logger.error(f"Failed to get Ubuntu AMIs: {e}")

        return alternatives

    def find_alternatives(
        self,
        distribution: str = "amazon_linux_2023",
        architecture: str = "x86_64",
        count: int = 3
    ) -> List[AMIAlternative]:
        """
        Find alternative AMI recommendations using AWS CLI

        Args:
            distribution: Distribution name (amazon_linux_2023, ubuntu_24_04, etc.)
            architecture: CPU architecture (x86_64 or arm64)
            count: Number of alternatives to return

        Returns:
            List of AMIAlternative objects
        """
        alternatives = []

        # Route to appropriate CLI method based on distribution
        if "amazon_linux" in distribution:
            alternatives.extend(self._get_amazon_linux_amis(architecture))
        elif "ubuntu" in distribution:
            # Extract version from distribution name (ubuntu_24_04 -> 24.04)
            version = distribution.replace("ubuntu_", "").replace("_", ".")
            alternatives.extend(self._get_ubuntu_amis(version, architecture))

        # If no specific distribution found, get popular alternatives
        if not alternatives:
            alternatives.extend(self._get_popular_alternatives(architecture))

        return alternatives[:count]

    def _get_popular_alternatives(self, architecture: str = "x86_64") -> List[AMIAlternative]:
        """
        Get popular AMI alternatives using AWS CLI

        Args:
            architecture: CPU architecture

        Returns:
            List of AMIAlternative objects
        """
        popular = []

        # Get Amazon Linux 2023 (recommended)
        al2023 = self._get_amazon_linux_amis(architecture)
        popular.extend(al2023)

        # Get Ubuntu 22.04 LTS
        ubuntu = self._get_ubuntu_amis("22.04", architecture)
        popular.extend(ubuntu)

        # Get Ubuntu 24.04 LTS if we need more
        if len(popular) < 3:
            ubuntu24 = self._get_ubuntu_amis("24.04", architecture)
            popular.extend(ubuntu24)

        return popular

    def get_recommendation_for_ami(self, ami_id: str) -> List[AMIAlternative]:
        """
        Get recommendations for a specific AMI using AWS CLI

        Args:
            ami_id: AMI ID to find alternatives for

        Returns:
            List of AMIAlternative objects
        """
        # Get Amazon Linux 2023 (most recommended)
        recommendations = self._get_amazon_linux_amis("x86_64")

        # Add Ubuntu 22.04
        ubuntu = self._get_ubuntu_amis("22.04", "x86_64")
        recommendations.extend(ubuntu)

        # Add Ubuntu 24.04 if we need more
        if len(recommendations) < 3:
            ubuntu24 = self._get_ubuntu_amis("24.04", "x86_64")
            recommendations.extend(ubuntu24)

        return recommendations[:3]

    def get_azure_images(self, publisher: str = "Canonical", offer: str = "0001-com-ubuntu-server-jammy") -> List[Dict]:
        """
        Get Azure VM images using Azure CLI

        Args:
            publisher: Image publisher (default: Canonical)
            offer: Image offer (default: Ubuntu 22.04)

        Returns:
            List of image dictionaries
        """
        if not self.azure_available:
            logger.warning("Azure CLI not available")
            return []

        try:
            cmd = [
                "az", "vm", "image", "list",
                "--publisher", publisher,
                "--offer", offer,
                "--all",
                "--output", "json"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                images = json.loads(result.stdout)
                logger.debug(f"Found {len(images)} Azure images")
                return images

        except subprocess.TimeoutExpired:
            logger.error("Azure CLI command timed out")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Azure CLI output: {e}")
        except Exception as e:
            logger.error(f"Failed to get Azure images: {e}")

        return []

    def get_gcp_images(self, project: str = "ubuntu-os-cloud", family: str = "ubuntu-2204-lts") -> List[Dict]:
        """
        Get GCP compute images using gcloud CLI

        Args:
            project: GCP project (default: ubuntu-os-cloud)
            family: Image family (default: ubuntu-2204-lts)

        Returns:
            List of image dictionaries
        """
        if not self.gcp_available:
            logger.warning("GCP gcloud CLI not available")
            return []

        try:
            cmd = [
                "gcloud", "compute", "images", "list",
                "--project", project,
                "--filter", f"family={family}",
                "--format", "json"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                images = json.loads(result.stdout)
                logger.debug(f"Found {len(images)} GCP images")
                return images

        except subprocess.TimeoutExpired:
            logger.error("gcloud CLI command timed out")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse gcloud output: {e}")
        except Exception as e:
            logger.error(f"Failed to get GCP images: {e}")

        return []
