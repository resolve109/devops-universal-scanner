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
    # Compute - EC2
    "aws_instance": {
        "t2.micro": 8.50,
        "t2.small": 16.79,
        "t2.medium": 33.58,
        "t2.large": 67.16,
        "t3.micro": 7.59,
        "t3.small": 15.18,
        "t3.medium": 30.37,
        "t3.large": 60.74,
        "t3.xlarge": 121.47,
        "t3.2xlarge": 242.94,
        "m5.large": 69.35,
        "m5.xlarge": 138.70,
        "m5.2xlarge": 277.40,
        "m5.4xlarge": 554.80,
        "m5.8xlarge": 1109.60,
        "c5.large": 61.84,
        "c5.xlarge": 123.69,
        "c5.2xlarge": 247.38,
        "c5.4xlarge": 494.76,
        "r5.large": 91.25,
        "r5.xlarge": 182.50,
        "r5.2xlarge": 365.00,
        "p3.2xlarge": 2204.16,  # GPU instance
        "p3.8xlarge": 8816.64,  # GPU instance
        "p3.16xlarge": 17633.28,  # GPU instance
        "p4d.24xlarge": 23320.80,  # High-end GPU instance
        "g4dn.xlarge": 380.88,  # GPU instance
        "g4dn.2xlarge": 543.84,  # GPU instance
        "g5.xlarge": 766.08,  # GPU instance
        "g5.2xlarge": 932.64,  # GPU instance
    },
    # Compute - ECS/Fargate
    "aws_ecs_cluster": 0.00,  # No charge for cluster itself
    "aws_ecs_service": 0.00,  # Charges are for underlying compute
    "aws_ecs_task_definition": 0.00,  # Free
    "fargate": {
        "0.25_vCPU_0.5_GB": 10.97,  # per task/month
        "0.5_vCPU_1_GB": 21.94,
        "1_vCPU_2_GB": 43.88,
        "2_vCPU_4_GB": 87.76,
        "4_vCPU_8_GB": 175.52,
    },
    # RDS Databases
    "aws_db_instance": {
        "db.t2.micro": 12.41,
        "db.t2.small": 24.82,
        "db.t3.micro": 11.69,
        "db.t3.small": 23.37,
        "db.t3.medium": 46.74,
        "db.t3.large": 93.48,
        "db.m5.large": 116.07,
        "db.m5.xlarge": 232.14,
        "db.m5.2xlarge": 464.28,
        "db.r5.large": 173.70,
        "db.r5.xlarge": 347.40,
        "db.r5.2xlarge": 694.80,
    },
    # DynamoDB
    "aws_dynamodb_table": 0.25,  # $0.25 per GB/month + $1.25 per million writes (minimal estimate)
    # Storage - EBS
    "aws_ebs_volume": {
        "gp3": 0.08,  # per GB/month
        "gp2": 0.10,  # per GB/month
        "io1": 0.125,  # per GB/month
        "io2": 0.125,  # per GB/month
        "st1": 0.045,  # per GB/month
        "sc1": 0.015,  # per GB/month
    },
    # Storage - S3
    "aws_s3_bucket": {
        "standard": 0.023,  # per GB/month
        "standard_ia": 0.0125,  # per GB/month
        "glacier": 0.004,  # per GB/month
        "glacier_deep_archive": 0.00099,  # per GB/month
    },
    # Storage - EFS
    "aws_efs_file_system": 0.30,  # per GB/month
    # Load Balancers
    "aws_lb": {
        "application": 16.43,  # ALB
        "network": 16.43,  # NLB
        "gateway": 16.43,  # GWLB
    },
    "aws_elb": 18.25,  # Classic LB
    "aws_alb": 16.43,  # Application LB (alias)
    # Networking
    "aws_nat_gateway": 32.85,
    "aws_vpn_connection": 36.50,
    "aws_vpn_gateway": 0.05,  # per GB transferred
    "aws_vpc_endpoint": 7.30,  # Interface endpoint
    "aws_transit_gateway": 36.50,
    # CloudFront
    "aws_cloudfront_distribution": 0.085,  # per GB transferred (minimal estimate)
    # Route53
    "aws_route53_zone": 0.50,  # per hosted zone/month
    "aws_route53_record": 0.00,  # Free for basic queries
    # ElastiCache
    "aws_elasticache_cluster": {
        "cache.t2.micro": 12.41,
        "cache.t2.small": 24.82,
        "cache.t3.micro": 11.69,
        "cache.t3.small": 23.37,
        "cache.m5.large": 116.07,
        "cache.m5.xlarge": 232.14,
        "cache.r5.large": 173.70,
    },
    # Lambda
    "aws_lambda_function": 0.20,  # per 1M requests (minimal estimate)
    # EKS
    "aws_eks_cluster": 73.00,  # Control plane only
    "aws_eks_node_group": 0.00,  # Charged for underlying EC2
    "aws_eks_fargate_profile": 0.00,  # Charged for Fargate pods
    # ECR
    "aws_ecr_repository": 0.10,  # per GB/month stored
    # SageMaker
    "aws_sagemaker_notebook_instance": {
        "ml.t2.medium": 33.58,
        "ml.t3.medium": 30.37,
        "ml.m5.large": 83.22,
        "ml.m5.xlarge": 166.46,
        "ml.p3.2xlarge": 2204.16,
    },
    # Redshift
    "aws_redshift_cluster": {
        "dc2.large": 182.50,
        "dc2.8xlarge": 3650.00,
        "ra3.xlplus": 997.92,
        "ra3.4xlarge": 2394.00,
    },
    # OpenSearch (Elasticsearch)
    "aws_opensearch_domain": {
        "t3.small.search": 27.74,
        "t3.medium.search": 55.48,
        "m5.large.search": 100.74,
        "r5.large.search": 145.70,
    },
    "aws_elasticsearch_domain": {  # Alias
        "t3.small.search": 27.74,
        "t3.medium.search": 55.48,
        "m5.large.search": 100.74,
        "r5.large.search": 145.70,
    },
    # MSK (Kafka)
    "aws_msk_cluster": {
        "kafka.t3.small": 36.50,
        "kafka.m5.large": 146.00,
        "kafka.m5.xlarge": 292.00,
    },
    # EMR
    "aws_emr_cluster": {
        "m5.xlarge": 27.00,  # Per instance/month (EMR charge only, add EC2 cost)
        "m5.2xlarge": 54.00,
    },
    # Kinesis
    "aws_kinesis_stream": 10.95,  # Per shard/month
    "aws_kinesis_firehose_delivery_stream": 0.029,  # Per GB ingested
    # API Gateway
    "aws_api_gateway_rest_api": 3.50,  # Per million requests
    "aws_apigatewayv2_api": 1.00,  # HTTP API - per million requests
    # Step Functions
    "aws_sfn_state_machine": 25.00,  # Per 1000 state transitions (standard)
    # CloudWatch
    "aws_cloudwatch_log_group": 0.50,  # Per GB ingested
    # SNS/SQS
    "aws_sns_topic": 0.50,  # Per million requests
    "aws_sqs_queue": 0.40,  # Per million requests
    # Secrets Manager
    "aws_secretsmanager_secret": 0.40,  # Per secret/month
    # IAM (Free)
    "aws_iam_role": 0.00,
    "aws_iam_policy": 0.00,
    "aws_iam_user": 0.00,
    "aws_iam_group": 0.00,
    # Security Groups (Free)
    "aws_security_group": 0.00,
    "aws_security_group_rule": 0.00,
    # VPC (Free)
    "aws_vpc": 0.00,
    "aws_subnet": 0.00,
    "aws_internet_gateway": 0.00,
    "aws_route_table": 0.00,
    # Free tier / managed services
    "aws_cloudformation_stack": 0.00,
}

# Azure Resource Cost Estimates (monthly, USD)
AZURE_COST_ESTIMATES = {
    # Compute - Virtual Machines
    "azurerm_virtual_machine": {
        "Standard_B1s": 7.59,
        "Standard_B2s": 30.37,
        "Standard_B2ms": 60.74,
        "Standard_D2s_v3": 70.08,
        "Standard_D4s_v3": 140.16,
        "Standard_E2s_v3": 96.36,
        "Standard_F2s_v2": 61.32,
        "Standard_NC6": 657.00,  # GPU
        "Standard_NC12": 1314.00,  # GPU
        "Standard_NV6": 803.28,  # GPU
    },
    "azurerm_linux_virtual_machine": {  # Alias
        "Standard_B1s": 7.59,
        "Standard_B2s": 30.37,
        "Standard_D2s_v3": 70.08,
    },
    "azurerm_windows_virtual_machine": {  # Alias (includes Windows license)
        "Standard_B2s": 52.56,
        "Standard_D2s_v3": 118.26,
    },
    # Container Services
    "azurerm_kubernetes_cluster": 73.00,  # Control plane
    "azurerm_container_group": 0.0000012,  # Per vCPU-second + per GB-second
    "azurerm_container_registry": 5.00,  # Basic tier
    # Databases
    "azurerm_sql_database": {
        "Basic": 4.90,
        "S0": 14.98,
        "S1": 29.96,
        "P1": 465.00,
    },
    "azurerm_cosmosdb_account": 23.36,  # 100 RU/s provisioned
    "azurerm_postgresql_server": {
        "B_Gen5_1": 24.82,
        "B_Gen5_2": 49.64,
        "GP_Gen5_2": 131.83,
    },
    "azurerm_mysql_server": {
        "B_Gen5_1": 24.82,
        "B_Gen5_2": 49.64,
        "GP_Gen5_2": 131.83,
    },
    # Storage
    "azurerm_storage_account": 0.018,  # per GB
    "azurerm_managed_disk": {
        "Standard_LRS": 0.040,  # per GB/month
        "StandardSSD_LRS": 0.075,  # per GB/month
        "Premium_LRS": 0.135,  # per GB/month
        "UltraSSD_LRS": 0.120,  # per GB/month (base, + IOPS/throughput)
    },
    # Networking
    "azurerm_application_gateway": 125.07,
    "azurerm_lb": 18.25,  # Load Balancer
    "azurerm_vpn_gateway": {
        "Basic": 27.38,
        "VpnGw1": 131.40,
        "VpnGw2": 329.85,
    },
    # App Services
    "azurerm_app_service_plan": {
        "B1": 12.41,
        "S1": 54.75,
        "P1v2": 72.27,
    },
    "azurerm_function_app": 0.20,  # Consumption plan (per 1M executions)
    # Misc
    "azurerm_redis_cache": {
        "Basic_C0": 15.33,
        "Standard_C1": 49.64,
    },
}

# GCP Resource Cost Estimates (monthly, USD)
GCP_COST_ESTIMATES = {
    # Compute - Compute Engine
    "google_compute_instance": {
        "f1-micro": 3.88,
        "g1-small": 14.24,
        "n1-standard-1": 24.27,
        "n1-standard-2": 48.55,
        "n1-standard-4": 97.09,
        "n2-standard-2": 54.51,
        "n2-standard-4": 109.03,
        "e2-micro": 6.11,
        "e2-small": 12.23,
        "e2-medium": 24.45,
        "c2-standard-4": 168.47,
    },
    # Container Services
    "google_container_cluster": 73.00,  # GKE management fee per cluster
    "google_container_node_pool": 0.00,  # Charged for underlying compute
    # Cloud Run
    "google_cloud_run_service": 0.40,  # Per million requests (minimal)
    # Databases
    "google_sql_database_instance": {
        "db-f1-micro": 7.67,
        "db-g1-small": 25.00,
        "db-n1-standard-1": 46.17,
        "db-n1-standard-2": 92.34,
    },
    "google_bigtable_instance": 0.65,  # per node/hour = $474.50/month
    # Storage
    "google_storage_bucket": 0.020,  # per GB/month (Standard)
    "google_compute_disk": {
        "pd-standard": 0.040,  # per GB/month
        "pd-balanced": 0.100,  # per GB/month
        "pd-ssd": 0.170,  # per GB/month
    },
    # Networking
    "google_compute_forwarding_rule": 0.025,  # per rule/hour = $18.25/month
    "google_compute_address": 0.005,  # per hour if not attached = $3.65/month
    "google_compute_vpn_gateway": 0.05,  # per tunnel/hour = $36.50/month
    # Cloud Functions
    "google_cloudfunctions_function": 0.40,  # Per million invocations
    # BigQuery
    "google_bigquery_dataset": 0.020,  # per GB/month (active storage)
    "google_bigquery_table": 0.00,  # Included in dataset
    # Pub/Sub
    "google_pubsub_topic": 0.00,  # Free (charged for message volume)
    "google_pubsub_subscription": 0.00,  # Free (charged for message volume)
    # IAM (Free)
    "google_service_account": 0.00,
    "google_project_iam_member": 0.00,
    # VPC (Free)
    "google_compute_network": 0.00,
    "google_compute_subnetwork": 0.00,
    "google_compute_firewall": 0.00,
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
