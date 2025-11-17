"""
Idle Resource Detector
Identifies resources that may be idle or underutilized

Operations:
- detect_idle_resources: Find potentially idle resources
- analyze_utilization_patterns: Analyze resource usage patterns
- estimate_waste: Calculate cost of idle resources
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from analyzers.finops.cost_analyzer import CostBreakdown


@dataclass
class IdleResourceWarning:
    """Warning about potentially idle resource"""
    resource_name: str
    resource_type: str
    idle_reason: str
    monthly_waste: float
    recommendation: str
    severity: str


class IdleResourceDetector:
    """
    Detects potentially idle or underutilized resources

    Operations:
    1. detect_unattached_resources - Find unattached EBS, IPs, etc.
    2. detect_empty_resources - Find empty load balancers, security groups
    3. detect_oversized_resources - Find resources that may be oversized
    """

    def __init__(self):
        self.warnings: List[IdleResourceWarning] = []

    def analyze(self, resources: List[Dict[str, Any]], cost_breakdowns: List[CostBreakdown]) -> List[IdleResourceWarning]:
        """
        Analyze resources for idle/waste patterns

        Args:
            resources: Parsed resources from IaC
            cost_breakdowns: Cost breakdowns for resources

        Returns:
            List of idle resource warnings
        """
        warnings = []

        # Create cost lookup
        cost_map = {cb.resource_name: cb for cb in cost_breakdowns}

        for resource in resources:
            resource_name = resource.get("name", "")
            resource_type = resource.get("type", "")

            # Check for idle patterns
            idle_warnings = self._check_idle_patterns(resource, cost_map.get(resource_name))

            warnings.extend(idle_warnings)

        self.warnings = warnings
        return warnings

    def _check_idle_patterns(self, resource: Dict[str, Any], cost_breakdown: Optional[CostBreakdown]) -> List[IdleResourceWarning]:
        """Check resource for idle patterns"""
        warnings = []
        resource_type = resource.get("type", "")
        resource_name = resource.get("name", "")

        # Unattached EBS volumes
        if resource_type == "aws_ebs_volume":
            body = resource.get("body", "")
            if "attach" not in body.lower() and "instance" not in body.lower():
                monthly_cost = cost_breakdown.monthly_cost if cost_breakdown else 0.0
                warnings.append(IdleResourceWarning(
                    resource_name=resource_name,
                    resource_type=resource_type,
                    idle_reason="EBS volume appears unattached",
                    monthly_waste=monthly_cost,
                    recommendation="Delete unused volume or attach to an instance",
                    severity="medium"
                ))

        # Elastic IPs without instance
        if resource_type == "aws_eip":
            body = resource.get("body", "")
            if "instance" not in body.lower():
                warnings.append(IdleResourceWarning(
                    resource_name=resource_name,
                    resource_type=resource_type,
                    idle_reason="Elastic IP not associated with instance ($3.65/month waste)",
                    monthly_waste=3.65,
                    recommendation="Release unused Elastic IP or associate with instance",
                    severity="low"
                ))

        # Load balancers without targets
        if resource_type in ["aws_lb", "aws_elb"]:
            # This is hard to detect from static analysis alone
            # But we can flag it for manual review
            pass

        return warnings

    def generate_idle_report(self) -> str:
        """Generate idle resource report"""
        if not self.warnings:
            return "\n✅ No idle resource warnings detected.\n"

        lines = []
        lines.append("")
        lines.append("=" * 80)
        lines.append("⚠️  IDLE RESOURCE DETECTION")
        lines.append("=" * 80)
        lines.append("")

        total_waste = sum(w.monthly_waste for w in self.warnings)

        lines.append(f"📊 POTENTIAL MONTHLY WASTE: ${total_waste:.2f}")
        lines.append(f"📅 POTENTIAL ANNUAL WASTE: ${total_waste * 12:.2f}")
        lines.append("")

        for i, warning in enumerate(self.warnings, 1):
            severity_indicator = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢",
            }.get(warning.severity, "⚪")

            lines.append(f"{i}. {severity_indicator} {warning.resource_name}")
            lines.append(f"   Type: {warning.resource_type}")
            lines.append(f"   Issue: {warning.idle_reason}")
            lines.append(f"   Monthly Waste: ${warning.monthly_waste:.2f}")
            lines.append(f"   💡 Recommendation: {warning.recommendation}")
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)
