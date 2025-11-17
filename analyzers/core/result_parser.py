"""
Result parsers for different scanning tools
Normalizes output from various tools into a common format
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from analyzers.core.config import SeverityLevel, AnalysisCategory


@dataclass
class Finding:
    """Normalized finding from any scanner tool"""
    tool: str
    severity: SeverityLevel
    category: AnalysisCategory
    check_id: str
    check_name: str
    resource_type: str
    resource_name: str
    file_path: str
    line_number: int = 0
    description: str = ""
    remediation: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['severity'] = self.severity.value if isinstance(self.severity, SeverityLevel) else self.severity
        data['category'] = self.category.value if isinstance(self.category, AnalysisCategory) else self.category
        return data


class ResultParser:
    """Base class for result parsers"""

    def parse(self, output: str, output_format: str = "text") -> List[Finding]:
        """Parse tool output into normalized findings"""
        raise NotImplementedError


class CheckovParser(ResultParser):
    """Parser for Checkov output"""

    SEVERITY_MAP = {
        "CRITICAL": SeverityLevel.CRITICAL,
        "HIGH": SeverityLevel.HIGH,
        "MEDIUM": SeverityLevel.MEDIUM,
        "LOW": SeverityLevel.LOW,
        "INFO": SeverityLevel.INFO,
    }

    def parse(self, output: str, output_format: str = "json") -> List[Finding]:
        """Parse Checkov JSON or text output"""
        findings = []

        if output_format == "json":
            findings = self._parse_json(output)
        else:
            findings = self._parse_text(output)

        return findings

    def _parse_json(self, output: str) -> List[Finding]:
        """Parse Checkov JSON output"""
        findings = []

        try:
            data = json.loads(output)
            failed_checks = data.get("results", {}).get("failed_checks", [])

            for check in failed_checks:
                severity = self.SEVERITY_MAP.get(
                    check.get("severity", "MEDIUM"),
                    SeverityLevel.MEDIUM
                )

                finding = Finding(
                    tool="checkov",
                    severity=severity,
                    category=AnalysisCategory.SECURITY,
                    check_id=check.get("check_id", ""),
                    check_name=check.get("check_name", ""),
                    resource_type=check.get("check_class", ""),
                    resource_name=check.get("resource", ""),
                    file_path=check.get("file_path", ""),
                    line_number=check.get("file_line_range", [0])[0] if check.get("file_line_range") else 0,
                    description=check.get("description", ""),
                    remediation=check.get("guideline", ""),
                    raw_data=check
                )
                findings.append(finding)

        except json.JSONDecodeError:
            pass

        return findings

    def _parse_text(self, output: str) -> List[Finding]:
        """Parse Checkov text output"""
        findings = []
        # Parse text format - simplified for now
        # Can be enhanced to parse the actual text output format
        return findings


class TFLintParser(ResultParser):
    """Parser for TFLint output"""

    def parse(self, output: str, output_format: str = "text") -> List[Finding]:
        """Parse TFLint output"""
        findings = []

        # Example TFLint output line:
        # Warning: Missing version constraint for provider "aws" in `required_providers` (terraform_required_providers)
        pattern = r'(Error|Warning):\s+(.+?)\s+\((.+?)\)'

        for line in output.split('\n'):
            match = re.search(pattern, line)
            if match:
                severity_str, description, check_id = match.groups()

                severity = SeverityLevel.HIGH if severity_str == "Error" else SeverityLevel.MEDIUM

                finding = Finding(
                    tool="tflint",
                    severity=severity,
                    category=AnalysisCategory.BEST_PRACTICE,
                    check_id=check_id,
                    check_name=check_id,
                    resource_type="terraform",
                    resource_name="",
                    file_path="",
                    description=description,
                    raw_data={"line": line}
                )
                findings.append(finding)

        return findings


class TFSecParser(ResultParser):
    """Parser for TFSec output"""

    def parse(self, output: str, output_format: str = "json") -> List[Finding]:
        """Parse TFSec output"""
        findings = []

        if output_format == "json":
            findings = self._parse_json(output)
        else:
            findings = self._parse_text(output)

        return findings

    def _parse_json(self, output: str) -> List[Finding]:
        """Parse TFSec JSON output"""
        findings = []

        try:
            data = json.loads(output)
            results = data.get("results", [])

            for result in results:
                severity_str = result.get("severity", "MEDIUM").upper()
                severity = SeverityLevel[severity_str] if severity_str in SeverityLevel.__members__ else SeverityLevel.MEDIUM

                finding = Finding(
                    tool="tfsec",
                    severity=severity,
                    category=AnalysisCategory.SECURITY,
                    check_id=result.get("rule_id", ""),
                    check_name=result.get("rule_description", ""),
                    resource_type=result.get("resource", ""),
                    resource_name=result.get("resource", ""),
                    file_path=result.get("location", {}).get("filename", ""),
                    line_number=result.get("location", {}).get("start_line", 0),
                    description=result.get("description", ""),
                    remediation=result.get("links", [""])[0] if result.get("links") else "",
                    raw_data=result
                )
                findings.append(finding)

        except json.JSONDecodeError:
            pass

        return findings

    def _parse_text(self, output: str) -> List[Finding]:
        """Parse TFSec text output"""
        findings = []
        # Simplified text parsing
        return findings


class CFNLintParser(ResultParser):
    """Parser for CFN-Lint output"""

    LEVEL_MAP = {
        "Error": SeverityLevel.HIGH,
        "Warning": SeverityLevel.MEDIUM,
        "Informational": SeverityLevel.LOW,
    }

    def parse(self, output: str, output_format: str = "json") -> List[Finding]:
        """Parse CFN-Lint output"""
        findings = []

        if output_format == "json":
            findings = self._parse_json(output)
        else:
            findings = self._parse_text(output)

        return findings

    def _parse_json(self, output: str) -> List[Finding]:
        """Parse CFN-Lint JSON output"""
        findings = []

        try:
            data = json.loads(output) if isinstance(output, str) else output

            for violation in data:
                level = violation.get("Level", "Warning")
                severity = self.LEVEL_MAP.get(level, SeverityLevel.MEDIUM)

                finding = Finding(
                    tool="cfn-lint",
                    severity=severity,
                    category=AnalysisCategory.BEST_PRACTICE,
                    check_id=violation.get("Rule", {}).get("Id", ""),
                    check_name=violation.get("Rule", {}).get("Description", ""),
                    resource_type=violation.get("Resource", ""),
                    resource_name=violation.get("Resource", ""),
                    file_path=violation.get("Filename", ""),
                    line_number=violation.get("Location", {}).get("Start", {}).get("LineNumber", 0),
                    description=violation.get("Message", ""),
                    raw_data=violation
                )
                findings.append(finding)

        except (json.JSONDecodeError, TypeError):
            pass

        return findings

    def _parse_text(self, output: str) -> List[Finding]:
        """Parse CFN-Lint text output"""
        findings = []
        return findings


class TrivyParser(ResultParser):
    """Parser for Trivy output"""

    SEVERITY_MAP = {
        "CRITICAL": SeverityLevel.CRITICAL,
        "HIGH": SeverityLevel.HIGH,
        "MEDIUM": SeverityLevel.MEDIUM,
        "LOW": SeverityLevel.LOW,
        "UNKNOWN": SeverityLevel.INFO,
    }

    def parse(self, output: str, output_format: str = "json") -> List[Finding]:
        """Parse Trivy JSON output"""
        findings = []

        try:
            data = json.loads(output)
            results = data.get("Results", [])

            for result in results:
                vulnerabilities = result.get("Vulnerabilities", [])

                for vuln in vulnerabilities:
                    severity = self.SEVERITY_MAP.get(
                        vuln.get("Severity", "MEDIUM"),
                        SeverityLevel.MEDIUM
                    )

                    finding = Finding(
                        tool="trivy",
                        severity=severity,
                        category=AnalysisCategory.SECURITY,
                        check_id=vuln.get("VulnerabilityID", ""),
                        check_name=vuln.get("Title", ""),
                        resource_type=result.get("Target", ""),
                        resource_name=vuln.get("PkgName", ""),
                        file_path=result.get("Target", ""),
                        description=vuln.get("Description", ""),
                        remediation=vuln.get("FixedVersion", "Update to fixed version if available"),
                        raw_data=vuln
                    )
                    findings.append(finding)

        except json.JSONDecodeError:
            pass

        return findings


# Parser registry
PARSER_REGISTRY: Dict[str, ResultParser] = {
    "checkov": CheckovParser(),
    "tflint": TFLintParser(),
    "tfsec": TFSecParser(),
    "cfn-lint": CFNLintParser(),
    "trivy": TrivyParser(),
}


def get_parser(tool_name: str) -> Optional[ResultParser]:
    """Get parser for a tool"""
    return PARSER_REGISTRY.get(tool_name.lower())


def parse_tool_output(tool_name: str, output: str, output_format: str = "text") -> List[Finding]:
    """
    Parse tool output into normalized findings

    Args:
        tool_name: Name of the tool (e.g., 'checkov', 'tflint')
        output: Raw output from the tool
        output_format: Output format ('json' or 'text')

    Returns:
        List of normalized Finding objects
    """
    parser = get_parser(tool_name)
    if parser:
        return parser.parse(output, output_format)
    return []
