"""
Result aggregator - collects and combines findings from all tools
"""

from typing import List, Dict, Any
from collections import defaultdict
from analyzers.core.result_parser import Finding
from analyzers.core.config import SeverityLevel, AnalysisCategory


class ResultAggregator:
    """Aggregates and organizes findings from multiple tools"""

    def __init__(self):
        self.findings: List[Finding] = []
        self.stats: Dict[str, Any] = {}

    def add_findings(self, findings: List[Finding]):
        """Add findings from a tool"""
        self.findings.extend(findings)

    def add_finding(self, finding: Finding):
        """Add a single finding"""
        self.findings.append(finding)

    def get_findings_by_severity(self, severity: SeverityLevel) -> List[Finding]:
        """Get all findings of a specific severity"""
        return [f for f in self.findings if f.severity == severity]

    def get_findings_by_category(self, category: AnalysisCategory) -> List[Finding]:
        """Get all findings of a specific category"""
        return [f for f in self.findings if f.category == category]

    def get_findings_by_tool(self, tool: str) -> List[Finding]:
        """Get all findings from a specific tool"""
        return [f for f in self.findings if f.tool == tool]

    def get_critical_findings(self) -> List[Finding]:
        """Get all critical findings"""
        return self.get_findings_by_severity(SeverityLevel.CRITICAL)

    def get_high_findings(self) -> List[Finding]:
        """Get all high severity findings"""
        return self.get_findings_by_severity(SeverityLevel.HIGH)

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics about findings"""
        stats = {
            "total_findings": len(self.findings),
            "by_severity": defaultdict(int),
            "by_category": defaultdict(int),
            "by_tool": defaultdict(int),
            "by_resource_type": defaultdict(int),
        }

        for finding in self.findings:
            stats["by_severity"][finding.severity.value] += 1
            stats["by_category"][finding.category.value] += 1
            stats["by_tool"][finding.tool] += 1
            if finding.resource_type:
                stats["by_resource_type"][finding.resource_type] += 1

        # Convert defaultdicts to regular dicts
        self.stats = {
            "total_findings": stats["total_findings"],
            "by_severity": dict(stats["by_severity"]),
            "by_category": dict(stats["by_category"]),
            "by_tool": dict(stats["by_tool"]),
            "by_resource_type": dict(stats["by_resource_type"]),
        }

        return self.stats

    def get_summary(self) -> str:
        """Get a text summary of findings"""
        if not self.stats:
            self.calculate_statistics()

        summary = []
        summary.append(f"Total Findings: {self.stats['total_findings']}")
        summary.append("")
        summary.append("By Severity:")
        for severity, count in sorted(self.stats['by_severity'].items()):
            summary.append(f"  {severity}: {count}")

        summary.append("")
        summary.append("By Category:")
        for category, count in sorted(self.stats['by_category'].items()):
            summary.append(f"  {category}: {count}")

        return "\n".join(summary)

    def to_dict(self) -> Dict[str, Any]:
        """Convert aggregator data to dictionary"""
        return {
            "findings": [f.to_dict() for f in self.findings],
            "statistics": self.stats if self.stats else self.calculate_statistics(),
        }
