"""
Core configuration for the DevOps Universal Scanner
Defines tool configurations, cost data, and analysis parameters
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum


class ScannerTool(Enum):
    """Supported scanning tools"""
    CHECKOV = "checkov"
    CFN_LINT = "cfn-lint"
    TFLINT = "tflint"
    TFSEC = "tfsec"
    TRIVY = "trivy"
    TERRAFORM = "terraform"
    BICEP = "bicep"
    ARM_TTK = "arm-ttk"


class SeverityLevel(Enum):
    """Finding severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class AnalysisCategory(Enum):
    """Analysis categories for findings"""
    SECURITY = "Security"
    FINOPS = "FinOps"
    AIML = "AI/ML Operations"
    COMPLIANCE = "Compliance"
    BEST_PRACTICE = "Best Practice"
    PERFORMANCE = "Performance"


@dataclass
class ToolConfig:
    """Configuration for a scanning tool"""
    name: str
    command: str
    frameworks: List[str]
    output_parser: str
    enabled: bool = True


@dataclass
class CostEstimate:
    """Cost estimation data"""
    monthly_cost_usd: float
    resource_type: str
    notes: str = ""
    idle_cost_warning: bool = False


# AWS Resource Cost Estimates (monthly, USD)
# These are approximate costs - actual costs vary by region and usage
AWS_COST_ESTIMATES = {
    # Compute
    "aws_instance": {
        "t2.micro": 8.50,
        "t2.small": 16.79,
        "t2.medium": 33.58,
        "t2.large": 67.16,
        "t3.micro": 7.59,
        "t3.small": 15.18,
        "t3.medium": 30.37,
        "t3.large": 60.74,
        "m5.large": 69.35,
        "m5.xlarge": 138.70,
        "m5.2xlarge": 277.40,
        "c5.large": 61.84,
        "c5.xlarge": 123.69,
        "c5.2xlarge": 247.38,
        "p3.2xlarge": 2204.16,  # GPU instance
        "p3.8xlarge": 8816.64,  # GPU instance
        "p3.16xlarge": 17633.28,  # GPU instance
        "p4d.24xlarge": 23320.80,  # High-end GPU instance
        "g4dn.xlarge": 380.88,  # GPU instance
        "g4dn.2xlarge": 543.84,  # GPU instance
        "g5.xlarge": 766.08,  # GPU instance
    },
    # RDS Databases
    "aws_db_instance": {
        "db.t2.micro": 12.41,
        "db.t2.small": 24.82,
        "db.t3.micro": 11.69,
        "db.t3.small": 23.37,
        "db.t3.medium": 46.74,
        "db.m5.large": 116.07,
        "db.m5.xlarge": 232.14,
        "db.r5.large": 173.70,
        "db.r5.xlarge": 347.40,
    },
    # Storage
    "aws_ebs_volume": {
        "gp3": 0.08,  # per GB/month
        "gp2": 0.10,  # per GB/month
        "io1": 0.125,  # per GB/month
        "io2": 0.125,  # per GB/month
        "st1": 0.045,  # per GB/month
        "sc1": 0.015,  # per GB/month
    },
    "aws_s3_bucket": {
        "standard": 0.023,  # per GB/month
        "standard_ia": 0.0125,  # per GB/month
        "glacier": 0.004,  # per GB/month
    },
    # Load Balancers
    "aws_lb": {
        "application": 16.43,  # ALB
        "network": 16.43,  # NLB
        "gateway": 16.43,  # GWLB
    },
    "aws_elb": 18.25,  # Classic LB
    # NAT Gateway
    "aws_nat_gateway": 32.85,
    # VPN
    "aws_vpn_connection": 36.50,
    # ElastiCache
    "aws_elasticache_cluster": {
        "cache.t2.micro": 12.41,
        "cache.t2.small": 24.82,
        "cache.t3.micro": 11.69,
        "cache.m5.large": 116.07,
    },
    # Lambda (per 1M requests + compute)
    "aws_lambda_function": 0.20,  # per 1M requests (minimal estimate)
    # EKS
    "aws_eks_cluster": 73.00,  # Control plane only
    # SageMaker
    "aws_sagemaker_notebook_instance": {
        "ml.t2.medium": 33.58,
        "ml.t3.medium": 30.37,
        "ml.m5.xlarge": 166.46,
        "ml.p3.2xlarge": 2204.16,
    },
}

# Azure Resource Cost Estimates (monthly, USD)
AZURE_COST_ESTIMATES = {
    "azurerm_virtual_machine": {
        "Standard_B1s": 7.59,
        "Standard_B2s": 30.37,
        "Standard_D2s_v3": 70.08,
        "Standard_NC6": 657.00,  # GPU
    },
    "azurerm_kubernetes_cluster": 73.00,
    "azurerm_storage_account": 0.018,  # per GB
}

# GCP Resource Cost Estimates (monthly, USD)
GCP_COST_ESTIMATES = {
    "google_compute_instance": {
        "f1-micro": 3.88,
        "g1-small": 14.24,
        "n1-standard-1": 24.27,
        "n1-standard-2": 48.55,
    },
    "google_container_cluster": 73.00,
    "google_storage_bucket": 0.020,  # per GB
}

# Idle resource detection patterns
IDLE_RESOURCE_INDICATORS = {
    "public_ip_not_attached": "Elastic IP without attached instance",
    "empty_security_group": "Security group with no instances",
    "unused_ebs_volume": "EBS volume not attached to instance",
    "stopped_instance": "EC2 instance in stopped state",
    "empty_load_balancer": "Load balancer with no targets",
}

# AI/ML specific resource patterns
AIML_RESOURCE_PATTERNS = {
    "gpu_instances": ["p2.", "p3.", "p4.", "g3.", "g4.", "g5."],
    "ml_services": ["sagemaker", "ml.", "ai."],
    "training_jobs": ["training", "train"],
    "inference_endpoints": ["inference", "endpoint", "serving"],
}

# Security enhancement patterns (beyond base tools)
SECURITY_ENHANCEMENT_PATTERNS = {
    "data_exfiltration_risk": {
        "description": "Resources that could lead to data exfiltration",
        "patterns": ["0.0.0.0/0", "publicly_accessible"],
    },
    "privilege_escalation": {
        "description": "IAM policies with excessive permissions",
        "patterns": ["*:*", "iam:*", "admin"],
    },
    "secrets_in_code": {
        "description": "Potential hardcoded secrets",
        "patterns": ["password", "secret", "api_key", "token"],
    },
}

# FinOps idle time thresholds (in days)
IDLE_WARNING_THRESHOLDS = {
    "development": 7,  # Warn if dev resources run > 7 days
    "staging": 14,  # Warn if staging resources run > 14 days
    "testing": 3,  # Warn if test resources run > 3 days
    "demo": 1,  # Warn if demo resources run > 1 day
}

# Cost warning thresholds (monthly USD)
COST_WARNING_THRESHOLDS = {
    "low": 100,
    "medium": 500,
    "high": 1000,
    "critical": 5000,
}


def get_cost_estimate(resource_type: str, instance_type: str = None) -> CostEstimate:
    """
    Get cost estimate for a resource

    Args:
        resource_type: The resource type (e.g., 'aws_instance')
        instance_type: The instance type (e.g., 't2.micro')

    Returns:
        CostEstimate object with cost data
    """
    cost_data = AWS_COST_ESTIMATES.get(resource_type)

    if cost_data is None:
        return CostEstimate(
            monthly_cost_usd=0.0,
            resource_type=resource_type,
            notes="Cost data not available for this resource type"
        )

    if isinstance(cost_data, dict) and instance_type:
        cost = cost_data.get(instance_type, 0.0)
        return CostEstimate(
            monthly_cost_usd=cost,
            resource_type=f"{resource_type} ({instance_type})",
            notes=f"Approximate monthly cost in US East region"
        )
    elif isinstance(cost_data, (int, float)):
        return CostEstimate(
            monthly_cost_usd=cost_data,
            resource_type=resource_type,
            notes="Approximate monthly cost"
        )

    return CostEstimate(
        monthly_cost_usd=0.0,
        resource_type=resource_type,
        notes="Unable to calculate cost for this configuration"
    )


def is_gpu_instance(instance_type: str) -> bool:
    """Check if an instance type is GPU-enabled"""
    if not instance_type:
        return False
    return any(pattern in instance_type.lower() for pattern in AIML_RESOURCE_PATTERNS["gpu_instances"])


def is_aiml_resource(resource_type: str) -> bool:
    """Check if a resource is AI/ML related"""
    if not resource_type:
        return False
    resource_lower = resource_type.lower()
    return any(pattern in resource_lower for pattern in AIML_RESOURCE_PATTERNS["ml_services"])
