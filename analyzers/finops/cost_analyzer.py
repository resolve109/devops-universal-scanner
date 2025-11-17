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
from analyzers.core.config import (
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
        resources = self._extract_cloudformation_resources(file_content)
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

        return resources

    def _extract_cloudformation_resources(self, content: str) -> List[Dict[str, Any]]:
        """Extract resources from CloudFormation template"""
        import yaml
        import json

        resources = []

        try:
            # Try YAML first
            try:
                data = yaml.safe_load(content)
            except:
                # Try JSON
                data = json.loads(content)

            cf_resources = data.get("Resources", {})

            for resource_name, resource_data in cf_resources.items():
                resource_type = resource_data.get("Type", "")
                properties = resource_data.get("Properties", {})

                # Convert CloudFormation type to internal format
                # AWS::EC2::Instance -> aws_instance
                internal_type = self._convert_cf_type_to_internal(resource_type)

                # Extract instance type
                instance_type = self._extract_cf_instance_type(properties, resource_type)

                resources.append({
                    "type": internal_type,
                    "name": resource_name,
                    "instance_type": instance_type,
                    "properties": properties,
                    "cf_type": resource_type,
                })

        except Exception as e:
            # If parsing fails, return empty list
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
        }

        return mapping.get(cf_type, cf_type.lower())

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

    def _extract_cf_instance_type(self, properties: Dict[str, Any], resource_type: str) -> Optional[str]:
        """Extract instance type from CloudFormation properties"""

        # Check common property names
        instance_type_keys = ["InstanceType", "DBInstanceClass", "NodeType", "CacheNodeType"]

        for key in instance_type_keys:
            if key in properties:
                value = properties[key]
                # Handle Ref and other CloudFormation functions
                if isinstance(value, dict):
                    if "Ref" in value:
                        continue  # Skip references for now
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

            # Get cost estimate
            monthly_cost = self._get_resource_cost(resource_type, instance_type)

            if monthly_cost > 0:
                # Calculate different time periods
                weekly_cost = monthly_cost / 4.33  # Average weeks per month
                daily_cost = monthly_cost / 30
                hourly_cost = monthly_cost / 730  # Average hours per month

                # Determine cost category
                cost_category = self._determine_cost_category(monthly_cost)

                # Check if GPU instance
                is_gpu = is_gpu_instance(instance_type or "")

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
                    notes=f"Approximate cost in US East region"
                )

                cost_breakdowns.append(breakdown)

        self.cost_breakdowns = cost_breakdowns
        self.total_monthly_cost = sum(cb.monthly_cost for cb in cost_breakdowns)

        return cost_breakdowns

    def _get_resource_cost(self, resource_type: str, instance_type: Optional[str]) -> float:
        """Get monthly cost for a resource"""

        cost_data = AWS_COST_ESTIMATES.get(resource_type)

        if cost_data is None:
            return 0.0

        if isinstance(cost_data, dict) and instance_type:
            return cost_data.get(instance_type, 0.0)
        elif isinstance(cost_data, (int, float)):
            return float(cost_data)

        return 0.0

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
        lines.append("💰 FINOPS COST ANALYSIS")
        lines.append("=" * 80)
        lines.append("")

        # Total costs
        lines.append(f"📊 TOTAL ESTIMATED COSTS:")
        lines.append(f"   Monthly:  ${self.total_monthly_cost:,.2f}")
        lines.append(f"   Weekly:   ${self.total_monthly_cost / 4.33:,.2f}")
        lines.append(f"   Daily:    ${self.total_monthly_cost / 30:,.2f}")
        lines.append(f"   Hourly:   ${self.total_monthly_cost / 730:,.2f}")
        lines.append("")

        # Resource breakdown
        lines.append("📋 RESOURCE COST BREAKDOWN:")
        lines.append("")

        # Sort by monthly cost (highest first)
        sorted_costs = sorted(self.cost_breakdowns, key=lambda x: x.monthly_cost, reverse=True)

        for i, breakdown in enumerate(sorted_costs, 1):
            # Cost category indicator
            indicator = self._get_cost_indicator(breakdown.cost_category)

            lines.append(f"{i}. {indicator} {breakdown.resource_name}")
            lines.append(f"   Type: {breakdown.resource_type}")
            if breakdown.instance_type:
                lines.append(f"   Instance: {breakdown.instance_type}")
            if breakdown.is_gpu:
                lines.append(f"   ⚡ GPU-ENABLED INSTANCE - High compute costs!")
            lines.append(f"   Monthly:  ${breakdown.monthly_cost:,.2f}")
            lines.append(f"   Weekly:   ${breakdown.weekly_cost:,.2f}")
            lines.append(f"   Daily:    ${breakdown.daily_cost:,.2f}")
            lines.append(f"   Hourly:   ${breakdown.hourly_cost:,.2f}")
            lines.append("")

        lines.append("=" * 80)
        lines.append("📌 Note: Costs are estimates based on US East (N. Virginia) region")
        lines.append("   Actual costs may vary based on region, usage, and AWS pricing changes")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _get_cost_indicator(self, category: str) -> str:
        """Get visual indicator for cost category"""
        indicators = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "minimal": "⚪",
        }
        return indicators.get(category, "⚪")

    def get_total_monthly_cost(self) -> float:
        """Get total monthly cost"""
        return self.total_monthly_cost

    def get_high_cost_resources(self, threshold: float = 1000.0) -> List[CostBreakdown]:
        """Get resources with monthly cost above threshold"""
        return [cb for cb in self.cost_breakdowns if cb.monthly_cost >= threshold]

    def get_gpu_resources(self) -> List[CostBreakdown]:
        """Get all GPU-enabled resources"""
        return [cb for cb in self.cost_breakdowns if cb.is_gpu]
