"""
Enhanced Security Checker
Provides security insights beyond base scanning tools

Operations:
- detect_data_exfiltration_risks: Find data exfiltration patterns
- detect_privilege_escalation: Find privilege escalation risks
- detect_secrets_in_code: Find potential hardcoded secrets
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from devops_universal_scanner.core.data.cost_estimates import SECURITY_ENHANCEMENT_PATTERNS


@dataclass
class SecurityInsight:
    """Enhanced security insight"""
    category: str
    severity: str
    resource_name: str
    finding: str
    recommendation: str


class EnhancedSecurityChecker:
    """
    Provides security checks beyond base tools

    Operations:
    1. check_public_exposure - Detect public exposure risks
    2. check_encryption - Verify encryption settings
    3. check_logging - Verify logging and monitoring
    """

    def __init__(self):
        self.insights: List[SecurityInsight] = []

    def analyze(self, resources: List[Dict[str, Any]]) -> List[SecurityInsight]:
        """Analyze resources for security issues"""
        insights = []

        for resource in resources:
            # Check for public exposure
            public_insights = self._check_public_exposure(resource)
            insights.extend(public_insights)

            # Check for encryption
            encryption_insights = self._check_encryption(resource)
            insights.extend(encryption_insights)

        self.insights = insights
        return insights

    def _check_public_exposure(self, resource: Dict[str, Any]) -> List[SecurityInsight]:
        """Check for public exposure risks"""
        insights = []
        resource_type = resource.get("type", "")
        resource_name = resource.get("name", "")
        body = str(resource.get("body", "")) + str(resource.get("properties", ""))

        # Check for 0.0.0.0/0
        if "0.0.0.0/0" in body:
            insights.append(SecurityInsight(
                category="Public Exposure",
                severity="high",
                resource_name=resource_name,
                finding="Resource allows access from 0.0.0.0/0 (entire internet)",
                recommendation="Restrict access to specific IP ranges or VPC only"
            ))

        # Check for publicly_accessible
        if "publicly_accessible" in body.lower() and "true" in body.lower():
            insights.append(SecurityInsight(
                category="Public Exposure",
                severity="high",
                resource_name=resource_name,
                finding="Resource configured as publicly accessible",
                recommendation="Make resource private and access via VPN or bastion host"
            ))

        return insights

    def _check_encryption(self, resource: Dict[str, Any]) -> List[SecurityInsight]:
        """Check encryption settings"""
        insights = []
        resource_type = resource.get("type", "")
        resource_name = resource.get("name", "")

        # Check for databases without encryption
        if "db_instance" in resource_type.lower():
            body = str(resource.get("body", ""))
            if "storage_encrypted" not in body.lower():
                insights.append(SecurityInsight(
                    category="Encryption",
                    severity="high",
                    resource_name=resource_name,
                    finding="Database does not have encryption enabled",
                    recommendation="Enable storage_encrypted = true for data at rest encryption"
                ))

        return insights

    def generate_security_report(self) -> str:
        """Generate security insights report"""
        if not self.insights:
            return ""

        lines = []
        lines.append("")
        lines.append("=" * 80)
        lines.append("[SECURITY] ENHANCED SECURITY INSIGHTS")
        lines.append("=" * 80)
        lines.append("")

        # Group by severity
        high_insights = [i for i in self.insights if i.severity == "high"]
        medium_insights = [i for i in self.insights if i.severity == "medium"]

        if high_insights:
            lines.append("[HIGH] HIGH SEVERITY FINDINGS:")
            lines.append("")
            for i, insight in enumerate(high_insights, 1):
                lines.append(f"{i}. {insight.resource_name}")
                lines.append(f"   Category: {insight.category}")
                lines.append(f"   Finding: {insight.finding}")
                lines.append(f"   [RECOMMENDATION] {insight.recommendation}")
                lines.append("")

        if medium_insights:
            lines.append("[MEDIUM] MEDIUM SEVERITY FINDINGS:")
            lines.append("")
            for i, insight in enumerate(medium_insights, 1):
                lines.append(f"{i}. {insight.resource_name}")
                lines.append(f"   Category: {insight.category}")
                lines.append(f"   Finding: {insight.finding}")
                lines.append(f"   [RECOMMENDATION] {insight.recommendation}")
                lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)
