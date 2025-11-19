"""
FinOps Cost Analyzer
Calculates resource costs and provides financial insights
Operations:
- calculate_resource_cost: Get cost for specific resource
- calculate_total_cost: Sum all resource costs
- get_cost_breakdown: Detailed cost breakdown by resource type
- estimate_savings: Calculate potential cost savings
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from devops_universal_scanner.core.data.cost_estimates import (
    AWS_COST_ESTIMATES,
    AZURE_COST_ESTIMATES,
    GCP_COST_ESTIMATES,
    COST_WARNING_THRESHOLDS,
    is_gpu_instance,
)


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a resource"""
    resource_name: str
    resource_type: str
    instance_type: Optional[str]
    monthly_cost: float
    weekly_cost: float
    daily_cost: float
    hourly_cost: float
    cost_category: str  # 'low', 'medium', 'high', 'critical'
    is_gpu: bool = False
    notes: str = ""
    cost_components: Dict[str, Any] = None  # Detailed cost breakdown (e.g., S3 storage, requests, transfer)
    is_free_service: bool = False  # True for free AWS services (Security Groups, IAM, etc.)


class CostAnalyzer:
    """
    Analyzes infrastructure costs from IaC templates

    Operations:
    1. extract_resources - Parse IaC file to find resources
    2. calculate_costs - Calculate costs for all resources
    3. generate_cost_report - Create detailed cost breakdown
    """

    def __init__(self):
        self.resources: List[Dict[str, Any]] = []
        self.cost_breakdowns: List[CostBreakdown] = []
        self.total_monthly_cost: float = 0.0

    def analyze_terraform(self, file_content: str) -> List[CostBreakdown]:
        """
        Analyze Terraform file for cost implications

        Args:
            file_content: Terraform file content

        Returns:
            List of cost breakdowns
        """
        resources = self._extract_terraform_resources(file_content)
        return self._calculate_costs(resources, "terraform")

    def analyze_cloudformation(self, file_content: str) -> List[CostBreakdown]:
        """
        Analyze CloudFormation template for cost implications

        Args:
            file_content: CloudFormation template content

        Returns:
            List of cost breakdowns
        """
        # Parse template to get parameters
        import yaml

        # Add custom YAML constructors for CloudFormation intrinsic functions
        def cfn_constructor(loader, tag_suffix, node):
            """Generic constructor for CloudFormation tags"""
            # For !Ref, !Sub, !GetAtt etc., return as dict for proper resolution
            if isinstance(node, yaml.ScalarNode):
                value = loader.construct_scalar(node)
                if tag_suffix in ('Ref', 'Sub', 'GetAtt', 'Join', 'Select'):
                    return {tag_suffix: value}
                return value
            elif isinstance(node, yaml.SequenceNode):
                return loader.construct_sequence(node)
            elif isinstance(node, yaml.MappingNode):
                return loader.construct_mapping(node)
            return None

        yaml.SafeLoader.add_multi_constructor('!', cfn_constructor)

        try:
            template = yaml.safe_load(file_content)
            parameters = template.get("Parameters", {})
        except:
            parameters = {}

        resources = self._extract_cloudformation_resources(file_content, parameters)
        return self._calculate_costs(resources, "cloudformation")

    def _extract_terraform_resources(self, content: str) -> List[Dict[str, Any]]:
        """Extract resources from Terraform file"""
        resources = []

        # Pattern: resource "aws_instance" "my_instance" {
        resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'

        for match in re.finditer(resource_pattern, content, re.MULTILINE | re.DOTALL):
            resource_type = match.group(1)
            resource_name = match.group(2)
            resource_body = match.group(3)

            # Extract instance_type if present
            instance_type = self._extract_instance_type(resource_body, resource_type, "terraform")

            resources.append({
                "type": resource_type,
                "name": resource_name,
                "instance_type": instance_type,
                "body": resource_body,
            })

            # Extract Azure managed disks from VM resources
            if resource_type in ["azurerm_virtual_machine", "azurerm_linux_virtual_machine", "azurerm_windows_virtual_machine"]:
                self._extract_azure_disks(resource_body, resource_name, resources)

            # Extract GCP attached disks from compute instances
            if resource_type == "google_compute_instance":
                self._extract_gcp_disks(resource_body, resource_name, resources)

            # Extract AWS EBS volumes from EC2 instances
            if resource_type == "aws_instance":
                self._extract_aws_ebs_from_terraform(resource_body, resource_name, resources)

        return resources

    def _extract_azure_disks(self, resource_body: str, parent_name: str, resources: List[Dict[str, Any]]):
        """Extract Azure managed disks from VM resource body"""
        # Extract OS disk
        os_disk_match = re.search(r'os_disk\s*\{([^}]+)\}', resource_body)
        if os_disk_match:
            os_disk_body = os_disk_match.group(1)
            disk_size_match = re.search(r'disk_size_gb\s*=\s*(\d+)', os_disk_body)
            storage_type_match = re.search(r'storage_account_type\s*=\s*"([^"]+)"', os_disk_body)

            if disk_size_match:
                disk_size = int(disk_size_match.group(1))
                storage_type = storage_type_match.group(1) if storage_type_match else "Standard_LRS"

                resources.append({
                    "type": "azurerm_managed_disk",
                    "name": f"{parent_name}_os_disk",
                    "instance_type": None,
                    "body": "",
                    "disk_size_gb": disk_size,
                    "storage_type": storage_type,
                })

        # Extract data disks
        for idx, data_disk_match in enumerate(re.finditer(r'data_disk\s*\{([^}]+)\}', resource_body)):
            data_disk_body = data_disk_match.group(1)
            disk_size_match = re.search(r'disk_size_gb\s*=\s*(\d+)', data_disk_body)
            storage_type_match = re.search(r'storage_account_type\s*=\s*"([^"]+)"', data_disk_body)

            if disk_size_match:
                disk_size = int(disk_size_match.group(1))
                storage_type = storage_type_match.group(1) if storage_type_match else "Standard_LRS"

                resources.append({
                    "type": "azurerm_managed_disk",
                    "name": f"{parent_name}_data_disk_{idx}",
                    "instance_type": None,
                    "body": "",
                    "disk_size_gb": disk_size,
                    "storage_type": storage_type,
                })

    def _extract_gcp_disks(self, resource_body: str, parent_name: str, resources: List[Dict[str, Any]]):
        """Extract GCP persistent disks from compute instance resource body"""
        # Extract boot disk
        boot_disk_match = re.search(r'boot_disk\s*\{([^}]+)\}', resource_body)
        if boot_disk_match:
            boot_disk_body = boot_disk_match.group(1)
            size_match = re.search(r'size\s*=\s*(\d+)', boot_disk_body)
            type_match = re.search(r'type\s*=\s*"([^"]+)"', boot_disk_body)

            if size_match:
                disk_size = int(size_match.group(1))
                disk_type = type_match.group(1) if type_match else "pd-standard"

                resources.append({
                    "type": "google_compute_disk",
                    "name": f"{parent_name}_boot_disk",
                    "instance_type": None,
                    "body": "",
                    "disk_size_gb": disk_size,
                    "disk_type": disk_type,
                })

        # Extract attached disks
        for idx, attached_disk_match in enumerate(re.finditer(r'attached_disk\s*\{([^}]+)\}', resource_body)):
            attached_disk_body = attached_disk_match.group(1)
            size_match = re.search(r'size\s*=\s*(\d+)', attached_disk_body)
            type_match = re.search(r'type\s*=\s*"([^"]+)"', attached_disk_body)

            if size_match:
                disk_size = int(size_match.group(1))
                disk_type = type_match.group(1) if type_match else "pd-standard"

                resources.append({
                    "type": "google_compute_disk",
                    "name": f"{parent_name}_attached_disk_{idx}",
                    "instance_type": None,
                    "body": "",
                    "disk_size_gb": disk_size,
                    "disk_type": disk_type,
                })

    def _extract_aws_ebs_from_terraform(self, resource_body: str, parent_name: str, resources: List[Dict[str, Any]]):
        """Extract AWS EBS volumes from Terraform EC2 instance resource body"""
        # Extract root block device
        root_block_match = re.search(r'root_block_device\s*\{([^}]+)\}', resource_body)
        if root_block_match:
            root_block_body = root_block_match.group(1)
            volume_size_match = re.search(r'volume_size\s*=\s*(\d+)', root_block_body)
            volume_type_match = re.search(r'volume_type\s*=\s*"([^"]+)"', root_block_body)

            if volume_size_match:
                volume_size = int(volume_size_match.group(1))
                volume_type = volume_type_match.group(1) if volume_type_match else "gp2"

                resources.append({
                    "type": "aws_ebs_volume",
                    "name": f"{parent_name}_root_volume",
                    "instance_type": None,
                    "body": "",
                    "volume_size": volume_size,
                    "volume_type": volume_type,
                })

        # Extract EBS block devices
        for idx, ebs_block_match in enumerate(re.finditer(r'ebs_block_device\s*\{([^}]+)\}', resource_body)):
            ebs_block_body = ebs_block_match.group(1)
            volume_size_match = re.search(r'volume_size\s*=\s*(\d+)', ebs_block_body)
            volume_type_match = re.search(r'volume_type\s*=\s*"([^"]+)"', ebs_block_body)

            if volume_size_match:
                volume_size = int(volume_size_match.group(1))
                volume_type = volume_type_match.group(1) if volume_type_match else "gp2"

                resources.append({
                    "type": "aws_ebs_volume",
                    "name": f"{parent_name}_ebs_{idx}",
                    "instance_type": None,
                    "body": "",
                    "volume_size": volume_size,
                    "volume_type": volume_type,
                })

    def _extract_cloudformation_resources(self, content: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Extract resources from CloudFormation template"""
        import yaml
        import json

        if parameters is None:
            parameters = {}

        resources = []

        try:
            # Add custom YAML constructors for CloudFormation intrinsic functions
            # These allow safe_load to handle !Ref, !Sub, !GetAtt, etc.
            def cfn_constructor(loader, tag_suffix, node):
                """Generic constructor for CloudFormation tags"""
                # For !Ref, !Sub, !GetAtt etc., return as dict for proper resolution
                if isinstance(node, yaml.ScalarNode):
                    value = loader.construct_scalar(node)
                    if tag_suffix in ('Ref', 'Sub', 'GetAtt', 'Join', 'Select'):
                        return {tag_suffix: value}
                    return value
                elif isinstance(node, yaml.SequenceNode):
                    return loader.construct_sequence(node)
                elif isinstance(node, yaml.MappingNode):
                    return loader.construct_mapping(node)
                return None

            # Register constructors for common CloudFormation tags
            yaml.SafeLoader.add_multi_constructor('!', cfn_constructor)

            # Try YAML first
            try:
                data = yaml.safe_load(content)
            except Exception as yaml_error:
                # Try JSON as fallback
                try:
                    data = json.loads(content)
                except Exception as json_error:
                    import sys
                    print(f"DEBUG: YAML parse error: {yaml_error}", file=sys.stderr)
                    print(f"DEBUG: JSON parse error: {json_error}", file=sys.stderr)
                    raise yaml_error

            cf_resources = data.get("Resources", {})

            for resource_name, resource_data in cf_resources.items():
                resource_type = resource_data.get("Type", "")
                properties = resource_data.get("Properties", {})

                # Convert CloudFormation type to internal format
                # AWS::EC2::Instance -> aws_instance
                internal_type = self._convert_cf_type_to_internal(resource_type)

                # Extract instance type (pass parameters for Ref resolution)
                instance_type = self._extract_cf_instance_type(properties, resource_type, parameters)

                resources.append({
                    "type": internal_type,
                    "name": resource_name,
                    "instance_type": instance_type,
                    "properties": properties,
                    "cf_type": resource_type,
                })

                # Extract EBS volumes from BlockDeviceMappings
                # This applies to EC2 instances, Launch Configurations, Launch Templates, EKS Nodegroups
                resources_with_block_devices = [
                    "AWS::EC2::Instance",
                    "AWS::AutoScaling::LaunchConfiguration",
                    "AWS::EC2::LaunchTemplate",
                    "AWS::Batch::ComputeEnvironment"
                ]

                if resource_type in resources_with_block_devices:
                    # Handle both direct BlockDeviceMappings and nested in LaunchTemplateData
                    block_devices = properties.get("BlockDeviceMappings", [])

                    # For Launch Templates, check LaunchTemplateData
                    if resource_type == "AWS::EC2::LaunchTemplate":
                        launch_template_data = properties.get("LaunchTemplateData", {})
                        block_devices = launch_template_data.get("BlockDeviceMappings", [])

                    for idx, mapping in enumerate(block_devices):
                        if "Ebs" in mapping:
                            ebs_props = mapping["Ebs"]
                            volume_size = ebs_props.get("VolumeSize", 0)
                            volume_type = ebs_props.get("VolumeType", "gp2")

                            # Skip if volume size is 0 or not specified
                            if volume_size > 0:
                                # Add as separate EBS volume resource
                                resources.append({
                                    "type": "aws_ebs_volume",
                                    "name": f"{resource_name}_ebs_{idx}",
                                    "instance_type": None,
                                    "properties": {
                                        "VolumeSize": volume_size,
                                        "VolumeType": volume_type
                                    },
                                    "cf_type": "AWS::EC2::Volume",
                                    "volume_size": volume_size,
                                    "volume_type": volume_type,
                                })

        except Exception as e:
            # If parsing fails, return empty list
            # Silently fail as this is expected for some templates
            pass

        return resources

    def _convert_cf_type_to_internal(self, cf_type: str) -> str:
        """Convert CloudFormation type to internal format"""
        # AWS::EC2::Instance -> aws_instance
        # AWS::RDS::DBInstance -> aws_db_instance

        mapping = {
            "AWS::EC2::Instance": "aws_instance",
            "AWS::RDS::DBInstance": "aws_db_instance",
            "AWS::ElasticLoadBalancingV2::LoadBalancer": "aws_lb",
            "AWS::ElasticLoadBalancing::LoadBalancer": "aws_elb",
            "AWS::EC2::NatGateway": "aws_nat_gateway",
            "AWS::EC2::Volume": "aws_ebs_volume",
            "AWS::S3::Bucket": "aws_s3_bucket",
            "AWS::VPN::Connection": "aws_vpn_connection",
            "AWS::ElastiCache::CacheCluster": "aws_elasticache_cluster",
            "AWS::Lambda::Function": "aws_lambda_function",
            "AWS::EKS::Cluster": "aws_eks_cluster",
            "AWS::SageMaker::NotebookInstance": "aws_sagemaker_notebook_instance",
            # Free services
            "AWS::EC2::SecurityGroup": "aws_security_group",
            "AWS::IAM::Role": "aws_iam_role",
            "AWS::IAM::Policy": "aws_iam_policy",
            "AWS::IAM::User": "aws_iam_user",
            "AWS::IAM::Group": "aws_iam_group",
        }

        return mapping.get(cf_type, cf_type.lower())

    def _is_free_aws_service(self, cf_type: str) -> bool:
        """Check if CloudFormation resource type is a free AWS service"""
        free_services = [
            "AWS::EC2::SecurityGroup",
            "AWS::IAM::Role",
            "AWS::IAM::Policy",
            "AWS::IAM::User",
            "AWS::IAM::Group",
            "AWS::IAM::InstanceProfile",
            "AWS::EC2::RouteTable",
            "AWS::EC2::Route",
            "AWS::EC2::SubnetRouteTableAssociation",
            "AWS::EC2::VPCGatewayAttachment",
            "AWS::CloudWatch::Alarm",  # Free within limits
            "AWS::Logs::LogGroup",  # Storage costs apply, but resource itself is free
        ]
        return cf_type in free_services

    def _extract_instance_type(self, resource_body: str, resource_type: str, format_type: str) -> Optional[str]:
        """Extract instance type from resource configuration"""

        # Common instance type patterns
        patterns = [
            r'instance_type\s*=\s*"([^"]+)"',  # Terraform
            r'instance_type\s*=\s*var\.([^"\s]+)',  # Terraform variable
            r'db_instance_class\s*=\s*"([^"]+)"',  # RDS
            r'node_type\s*=\s*"([^"]+)"',  # ElastiCache
            r'cache\.([^\s"]+)',  # Cache instance types
        ]

        for pattern in patterns:
            match = re.search(pattern, resource_body, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_cf_instance_type(self, properties: Dict[str, Any], resource_type: str, parameters: Dict[str, Any] = None) -> Optional[str]:
        """Extract instance type from CloudFormation properties"""

        if parameters is None:
            parameters = {}

        # Check common property names
        instance_type_keys = ["InstanceType", "DBInstanceClass", "NodeType", "CacheNodeType"]

        for key in instance_type_keys:
            if key in properties:
                value = properties[key]
                # Handle Ref and other CloudFormation functions
                if isinstance(value, dict):
                    if "Ref" in value:
                        # Resolve parameter reference
                        param_name = value["Ref"]
                        if param_name in parameters:
                            param_config = parameters[param_name]
                            # Get default value if available
                            if "Default" in param_config:
                                return str(param_config["Default"])
                        # Skip if we can't resolve the reference
                        continue
                else:
                    return str(value)

        return None

    def _calculate_costs(self, resources: List[Dict[str, Any]], format_type: str) -> List[CostBreakdown]:
        """Calculate costs for extracted resources"""
        cost_breakdowns = []

        for resource in resources:
            resource_type = resource.get("type", "")
            resource_name = resource.get("name", "")
            instance_type = resource.get("instance_type")
            cf_type = resource.get("cf_type", "")

            # Check if this is a free AWS service
            is_free = False
            if cf_type:
                is_free = self._is_free_aws_service(cf_type)

            # Get cost estimate and detailed breakdown
            # Pass volume info for EBS volumes
            if resource_type == "aws_ebs_volume":
                volume_size = resource.get("volume_size", 0)
                volume_type = resource.get("volume_type", "gp2")
                monthly_cost, cost_components = self._get_ebs_cost_detailed(volume_type, volume_size)
            else:
                monthly_cost, cost_components = self._get_resource_cost_detailed(resource_type, instance_type)

            # Include free services in the breakdown
            if monthly_cost > 0 or is_free:
                # Calculate different time periods
                weekly_cost = monthly_cost / 4.33  # Average weeks per month
                daily_cost = monthly_cost / 30
                hourly_cost = monthly_cost / 730  # Average hours per month

                # Determine cost category
                cost_category = self._determine_cost_category(monthly_cost) if not is_free else "free"

                # Check if GPU instance
                is_gpu = is_gpu_instance(instance_type or "")

                notes = "No charge (AWS managed service)" if is_free else "Approximate cost in US East region"

                breakdown = CostBreakdown(
                    resource_name=resource_name,
                    resource_type=resource_type,
                    instance_type=instance_type,
                    monthly_cost=monthly_cost,
                    weekly_cost=weekly_cost,
                    daily_cost=daily_cost,
                    hourly_cost=hourly_cost,
                    cost_category=cost_category,
                    is_gpu=is_gpu,
                    notes=notes,
                    cost_components=cost_components,
                    is_free_service=is_free
                )

                cost_breakdowns.append(breakdown)

        self.cost_breakdowns = cost_breakdowns
        self.total_monthly_cost = sum(cb.monthly_cost for cb in cost_breakdowns)

        return cost_breakdowns

    def _get_resource_cost(self, resource_type: str, instance_type: Optional[str]) -> float:
        """Get monthly cost for a resource (simple version - use _get_resource_cost_detailed for details)"""
        cost, _ = self._get_resource_cost_detailed(resource_type, instance_type)
        return cost

    def _get_ebs_cost_detailed(self, volume_type: str, volume_size: int) -> Tuple[float, Optional[Dict[str, Any]]]:
        """
        Get monthly cost for EBS volume with detailed breakdown

        Args:
            volume_type: EBS volume type (gp2, gp3, io1, io2, st1, sc1)
            volume_size: Volume size in GB

        Returns:
            Tuple of (total_monthly_cost, cost_components_dict)
        """
        cost_data = AWS_COST_ESTIMATES.get("aws_ebs_volume", {})

        if not cost_data:
            return 0.0, None

        # Get price per GB-month for volume type
        price_per_gb = cost_data.get(volume_type, 0.0)
        monthly_cost = price_per_gb * volume_size

        components = {
            "storage": {
                "description": f"{volume_type.upper()} volume",
                "rate_per_gb": price_per_gb,
                "size_gb": volume_size,
                "monthly_cost": monthly_cost
            }
        }

        return monthly_cost, components

    def _get_resource_cost_detailed(self, resource_type: str, instance_type: Optional[str]) -> Tuple[float, Optional[Dict[str, Any]]]:
        """
        Get monthly cost for a resource with detailed breakdown

        Returns:
            Tuple of (total_monthly_cost, cost_components_dict)
        """
        cost_data = AWS_COST_ESTIMATES.get(resource_type)

        if cost_data is None:
            return 0.0, None

        # Handle S3 buckets with detailed breakdown
        if resource_type == "aws_s3_bucket":
            assumed_storage_gb = 100  # Default assumption
            storage_rate = cost_data.get("standard", 0.023)  # $0.023 per GB-month
            storage_cost = storage_rate * assumed_storage_gb

            components = {
                "storage": {
                    "description": "Standard storage",
                    "rate_per_gb": storage_rate,
                    "estimated_gb": assumed_storage_gb,
                    "monthly_cost": storage_cost
                },
                "requests": {
                    "description": "PUT, COPY, POST, LIST requests",
                    "monthly_cost": 0.00,
                    "note": "Included in estimate (minimal usage assumed)"
                },
                "data_transfer": {
                    "description": "Data transfer out",
                    "monthly_cost": 0.00,
                    "note": "First 100 GB/month free"
                }
            }
            return storage_cost, components

        # Handle instance-based resources
        if isinstance(cost_data, dict):
            if instance_type:
                cost = cost_data.get(instance_type, 0.0)
                components = {
                    "compute": {
                        "description": f"{instance_type} instance",
                        "monthly_cost": cost
                    }
                }
                return cost, components
            else:
                # For resources with tiers but no specific instance type
                if "standard" in cost_data:
                    cost = cost_data["standard"] * 100  # Assume 100GB
                    return cost, None
                elif cost_data:
                    # Return first value * assumed usage
                    first_cost = next(iter(cost_data.values()))
                    cost = first_cost * 100
                    return cost, None
                return 0.0, None
        elif isinstance(cost_data, (int, float)):
            cost = float(cost_data)
            components = {
                "service": {
                    "description": f"{resource_type} service",
                    "monthly_cost": cost
                }
            }
            return cost, components

        return 0.0, None

    def _determine_cost_category(self, monthly_cost: float) -> str:
        """Determine cost warning category"""
        if monthly_cost >= COST_WARNING_THRESHOLDS["critical"]:
            return "critical"
        elif monthly_cost >= COST_WARNING_THRESHOLDS["high"]:
            return "high"
        elif monthly_cost >= COST_WARNING_THRESHOLDS["medium"]:
            return "medium"
        elif monthly_cost >= COST_WARNING_THRESHOLDS["low"]:
            return "low"
        else:
            return "minimal"

    def generate_cost_report(self) -> str:
        """Generate a formatted cost report"""
        if not self.cost_breakdowns:
            return "No cost data available"

        lines = []
        lines.append("=" * 80)
        lines.append("[COST] COST BREAKDOWN")
        lines.append("=" * 80)
        lines.append("")

        # Total costs
        lines.append("[TOTAL] ESTIMATED COSTS:")
        lines.append(f"   Monthly:  ${self.total_monthly_cost:,.2f}")
        lines.append(f"   Weekly:   ${self.total_monthly_cost / 4.33:,.2f}")
        lines.append(f"   Daily:    ${self.total_monthly_cost / 30:,.2f}")
        lines.append(f"   Hourly:   ${self.total_monthly_cost / 730:,.2f}")
        lines.append("")

        # Resource breakdown
        lines.append("[BREAKDOWN] RESOURCE COST BREAKDOWN:")
        lines.append("")

        # Sort by monthly cost (highest first), but keep free services at the end
        sorted_costs = sorted(
            self.cost_breakdowns,
            key=lambda x: (x.is_free_service, -x.monthly_cost)
        )

        for i, breakdown in enumerate(sorted_costs, 1):
            # Cost category indicator
            indicator = self._get_cost_indicator(breakdown.cost_category)

            lines.append(f"{i}. {indicator} {breakdown.resource_name}")
            lines.append(f"   Type: {breakdown.resource_type}")
            if breakdown.instance_type:
                lines.append(f"   Instance: {breakdown.instance_type}")

            # Show detailed cost breakdown for resources with components (e.g., S3)
            if breakdown.cost_components:
                lines.append("   Cost Components:")
                for comp_name, comp_data in breakdown.cost_components.items():
                    if "rate_per_gb" in comp_data:
                        # Storage component (S3 uses 'estimated_gb', EBS uses 'size_gb')
                        size_gb = comp_data.get('estimated_gb', comp_data.get('size_gb', 0))
                        lines.append(f"     - {comp_data['description']}: ${comp_data['rate_per_gb']:.3f}/GB × {size_gb}GB = ${comp_data['monthly_cost']:.2f}/month")
                    elif "note" in comp_data:
                        # Component with note (e.g., free tier)
                        lines.append(f"     - {comp_data['description']}: ${comp_data['monthly_cost']:.2f}/month ({comp_data['note']})")
                    else:
                        # Simple component
                        lines.append(f"     - {comp_data['description']}: ${comp_data['monthly_cost']:.2f}/month")

            if breakdown.is_gpu:
                lines.append("   [WARNING] GPU-ENABLED INSTANCE - High compute costs!")

            if breakdown.is_free_service:
                lines.append("   Monthly:  $0.00 (No charge - AWS managed service)")
            else:
                lines.append(f"   Monthly:  ${breakdown.monthly_cost:,.2f}")
                lines.append(f"   Weekly:   ${breakdown.weekly_cost:,.2f}")
                lines.append(f"   Daily:    ${breakdown.daily_cost:,.2f}")
                lines.append(f"   Hourly:   ${breakdown.hourly_cost:,.2f}")
            lines.append("")

        lines.append("=" * 80)
        lines.append("[NOTE] Costs are estimates based on US East (N. Virginia) region")
        lines.append("       Actual costs may vary based on region, usage, and AWS pricing changes")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _get_cost_indicator(self, category: str) -> str:
        """Get visual indicator for cost category"""
        indicators = {
            "critical": "[CRITICAL]",
            "high": "[HIGH]",
            "medium": "[MEDIUM]",
            "low": "[LOW]",
            "minimal": "[MINIMAL]",
            "free": "[FREE]",
        }
        return indicators.get(category, "[INFO]")

    def get_total_monthly_cost(self) -> float:
        """Get total monthly cost"""
        return self.total_monthly_cost

    def get_high_cost_resources(self, threshold: float = 1000.0) -> List[CostBreakdown]:
        """Get resources with monthly cost above threshold"""
        return [cb for cb in self.cost_breakdowns if cb.monthly_cost >= threshold]

    def get_gpu_resources(self) -> List[CostBreakdown]:
        """Get all GPU-enabled resources"""
        return [cb for cb in self.cost_breakdowns if cb.is_gpu]
