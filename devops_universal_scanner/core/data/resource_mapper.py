"""
Resource Mapper - Normalizes resource names across IaC formats

Maps resource names from different IaC technologies to canonical names for
consistent cost lookups and analysis.

Examples:
    - Terraform `aws_instance` → canonical `ec2_instance`
    - CloudFormation `AWS::EC2::Instance` → canonical `ec2_instance`
    - ARM `Microsoft.Compute/virtualMachines` → canonical `virtual_machine`
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import lru_cache


class ResourceMapper:
    """Maps resource names across IaC formats to canonical names"""

    def __init__(self):
        """Initialize with resource mapping index"""
        self.mapping_file = Path(__file__).parent / "resource_mapping.json"
        self.mappings = self._load_mappings()

        # Create reverse indexes for faster lookups
        self.terraform_index = {}
        self.cloudformation_index = {}
        self.arm_index = {}
        self.bicep_index = {}

        self._build_indexes()

    def _load_mappings(self) -> Dict[str, Any]:
        """Load resource mappings from JSON file"""
        try:
            with self.mapping_file.open('r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Resource mapping file not found: {self.mapping_file}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in mapping file: {e}")
            return {}

    def _build_indexes(self):
        """Build reverse indexes for fast lookups"""
        for category, resources in self.mappings.items():
            for resource_id, resource_data in resources.items():
                # Terraform index
                if 'terraform' in resource_data:
                    self.terraform_index[resource_data['terraform']] = {
                        'canonical_name': resource_data['canonical_name'],
                        'cloud_provider': resource_data['cloud_provider'],
                        'resource_type': resource_data['resource_type'],
                        'category': category,
                        'all_formats': resource_data
                    }

                # CloudFormation index
                if 'cloudformation' in resource_data:
                    self.cloudformation_index[resource_data['cloudformation']] = {
                        'canonical_name': resource_data['canonical_name'],
                        'cloud_provider': resource_data['cloud_provider'],
                        'resource_type': resource_data['resource_type'],
                        'category': category,
                        'all_formats': resource_data
                    }

                # ARM index
                if 'arm' in resource_data:
                    self.arm_index[resource_data['arm']] = {
                        'canonical_name': resource_data['canonical_name'],
                        'cloud_provider': resource_data['cloud_provider'],
                        'resource_type': resource_data['resource_type'],
                        'category': category,
                        'all_formats': resource_data
                    }

                # Bicep index (same as ARM usually)
                if 'bicep' in resource_data:
                    self.bicep_index[resource_data['bicep']] = {
                        'canonical_name': resource_data['canonical_name'],
                        'cloud_provider': resource_data['cloud_provider'],
                        'resource_type': resource_data['resource_type'],
                        'category': category,
                        'all_formats': resource_data
                    }

    @lru_cache(maxsize=512)
    def get_canonical_name(self, resource_type: str, framework: str = "terraform") -> Optional[str]:
        """
        Get canonical name for a resource type

        Args:
            resource_type: Resource type in framework format
            framework: IaC framework (terraform, cloudformation, arm, bicep)

        Returns:
            Canonical resource name or None if not found

        Example:
            >>> mapper = ResourceMapper()
            >>> mapper.get_canonical_name("aws_instance", "terraform")
            'ec2_instance'
            >>> mapper.get_canonical_name("AWS::EC2::Instance", "cloudformation")
            'ec2_instance'
        """
        framework = framework.lower()

        if framework == "terraform":
            result = self.terraform_index.get(resource_type)
        elif framework == "cloudformation":
            result = self.cloudformation_index.get(resource_type)
        elif framework == "arm":
            result = self.arm_index.get(resource_type)
        elif framework == "bicep":
            result = self.bicep_index.get(resource_type)
        else:
            return None

        return result['canonical_name'] if result else None

    @lru_cache(maxsize=512)
    def get_resource_info(self, resource_type: str, framework: str = "terraform") -> Optional[Dict[str, Any]]:
        """
        Get complete resource information

        Args:
            resource_type: Resource type in framework format
            framework: IaC framework

        Returns:
            Dictionary with resource info or None

        Example:
            >>> mapper = ResourceMapper()
            >>> info = mapper.get_resource_info("aws_instance", "terraform")
            >>> print(info['cloud_provider'])
            'aws'
            >>> print(info['resource_type'])
            'compute'
        """
        framework = framework.lower()

        if framework == "terraform":
            return self.terraform_index.get(resource_type)
        elif framework == "cloudformation":
            return self.cloudformation_index.get(resource_type)
        elif framework == "arm":
            return self.arm_index.get(resource_type)
        elif framework == "bicep":
            return self.bicep_index.get(resource_type)

        return None

    def get_cloud_provider(self, resource_type: str, framework: str = "terraform") -> Optional[str]:
        """
        Get cloud provider for a resource

        Args:
            resource_type: Resource type in framework format
            framework: IaC framework

        Returns:
            Cloud provider (aws, azure, gcp) or None
        """
        info = self.get_resource_info(resource_type, framework)
        return info['cloud_provider'] if info else None

    def get_category(self, resource_type: str, framework: str = "terraform") -> Optional[str]:
        """
        Get category for a resource

        Args:
            resource_type: Resource type in framework format
            framework: IaC framework

        Returns:
            Category (compute, storage, database, etc.) or None
        """
        info = self.get_resource_info(resource_type, framework)
        return info['category'] if info else None

    def convert_to_terraform(self, resource_type: str, framework: str) -> Optional[str]:
        """
        Convert resource type from any framework to Terraform format

        Args:
            resource_type: Resource type in source framework format
            framework: Source framework

        Returns:
            Terraform resource type or None

        Example:
            >>> mapper = ResourceMapper()
            >>> mapper.convert_to_terraform("AWS::EC2::Instance", "cloudformation")
            'aws_instance'
        """
        info = self.get_resource_info(resource_type, framework)
        if info and 'all_formats' in info:
            return info['all_formats'].get('terraform')
        return None

    def convert_to_cloudformation(self, resource_type: str, framework: str) -> Optional[str]:
        """
        Convert resource type from any framework to CloudFormation format

        Args:
            resource_type: Resource type in source framework format
            framework: Source framework

        Returns:
            CloudFormation resource type or None
        """
        info = self.get_resource_info(resource_type, framework)
        if info and 'all_formats' in info:
            return info['all_formats'].get('cloudformation')
        return None

    def is_gpu_resource(self, resource_type: str, framework: str = "terraform") -> bool:
        """
        Check if resource is a GPU-enabled compute instance

        Args:
            resource_type: Resource type
            framework: IaC framework

        Returns:
            True if GPU resource
        """
        canonical = self.get_canonical_name(resource_type, framework)
        if not canonical:
            return False

        # GPU resources are compute instances with specific patterns
        gpu_patterns = ['ec2_instance', 'virtual_machine', 'compute_instance']
        return canonical in gpu_patterns

    def is_serverless(self, resource_type: str, framework: str = "terraform") -> bool:
        """
        Check if resource is serverless

        Args:
            resource_type: Resource type
            framework: IaC framework

        Returns:
            True if serverless resource
        """
        category = self.get_category(resource_type, framework)
        return category == "serverless"

    def get_all_resources_by_cloud(self, cloud_provider: str) -> List[str]:
        """
        Get all resources for a specific cloud provider

        Args:
            cloud_provider: Cloud provider (aws, azure, gcp)

        Returns:
            List of canonical resource names
        """
        resources = []
        for category in self.mappings.values():
            for resource_data in category.values():
                if resource_data.get('cloud_provider') == cloud_provider:
                    resources.append(resource_data['canonical_name'])
        return resources

    def get_stats(self) -> Dict[str, int]:
        """Get mapping statistics"""
        return {
            "total_resources": sum(len(cat) for cat in self.mappings.values()),
            "categories": len(self.mappings),
            "terraform_mappings": len(self.terraform_index),
            "cloudformation_mappings": len(self.cloudformation_index),
            "arm_mappings": len(self.arm_index),
            "bicep_mappings": len(self.bicep_index),
        }


# Global instance
_resource_mapper = None

def get_resource_mapper() -> ResourceMapper:
    """
    Get or create global resource mapper instance

    Returns:
        ResourceMapper instance
    """
    global _resource_mapper
    if _resource_mapper is None:
        _resource_mapper = ResourceMapper()
    return _resource_mapper
