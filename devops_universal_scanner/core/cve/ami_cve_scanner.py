"""
AMI CVE Scanner
Checks AWS AMIs for known vulnerabilities and outdated versions

Operations:
1. check_ami - Check if AMI has known issues
2. check_ami_age - Check if AMI is outdated
3. scan_template_amis - Scan all AMIs in a template
4. Provides specific AMI ID alternatives when issues detected
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class AMICVE:
    """AMI vulnerability information"""
    ami_id: str
    ami_name: Optional[str] = None
    region: str = "unknown"
    has_cve: bool = False
    cve_ids: List[str] = None
    is_outdated: bool = False
    age_days: Optional[int] = None
    severity: str = "UNKNOWN"
    recommendation: str = ""
    suggested_alternatives: List = None  # Will contain AMIAlternative objects

    def __post_init__(self):
        if self.cve_ids is None:
            self.cve_ids = []
        if self.suggested_alternatives is None:
            self.suggested_alternatives = []


class AMICVEScanner:
    """
    Scans AWS AMIs for known CVEs and outdated versions

    Operations:
    1. Detects AMI IDs in IaC templates
    2. Checks against known vulnerable AMIs
    3. Provides specific AMI ID recommendations
    """

    # Known vulnerable AMIs (example data)
    # In production, this would be fetched from a CVE database
    KNOWN_VULNERABLE_AMIS = {
        "ami-0abcdef1234567890": {
            "cves": ["CVE-2024-12345"],
            "severity": "HIGH",
            "description": "Outdated Amazon Linux with known vulnerabilities",
            "recommendation": "Use latest Amazon Linux 2023 AMI"
        },
        # Add more as discovered
    }

    # AMI name patterns that indicate outdated images
    OUTDATED_PATTERNS = [
        r"amazon.*linux.*2018",
        r"ubuntu.*14\.04",
        r"ubuntu.*16\.04",
        r"centos.*6",
        r"rhel.*6",
    ]

    def __init__(self, region: str = "us-east-1"):
        self.scan_results: List[AMICVE] = []
        self.region = region
        # Import and initialize AMI alternative finder
        try:
            from devops_universal_scanner.core.cve.ami_alternative_finder import AMIAlternativeFinder
            self.ami_finder = AMIAlternativeFinder(region=region)
        except ImportError:
            self.ami_finder = None

    def check_ami(self, ami_id: str, ami_name: Optional[str] = None) -> AMICVE:
        """
        Check if an AMI has known CVEs

        Args:
            ami_id: AMI ID (e.g., 'ami-0abcdef1234567890')
            ami_name: Optional AMI name for pattern matching

        Returns:
            AMICVE object with results
        """
        result = None

        # Check against known vulnerable AMIs
        if ami_id in self.KNOWN_VULNERABLE_AMIS:
            vuln_info = self.KNOWN_VULNERABLE_AMIS[ami_id]
            result = AMICVE(
                ami_id=ami_id,
                ami_name=ami_name,
                region=self.region,
                has_cve=True,
                cve_ids=vuln_info["cves"],
                severity=vuln_info["severity"],
                recommendation=vuln_info["recommendation"]
            )

        # Check AMI name for outdated patterns
        elif ami_name:
            for pattern in self.OUTDATED_PATTERNS:
                if re.search(pattern, ami_name, re.IGNORECASE):
                    result = AMICVE(
                        ami_id=ami_id,
                        ami_name=ami_name,
                        region=self.region,
                        is_outdated=True,
                        severity="MEDIUM",
                        recommendation=f"AMI appears outdated based on name pattern. Consider using latest version."
                    )
                    break

        # Placeholder AMI (commonly used in examples)
        if not result and re.match(r'ami-0[a-f0-9]{16}$', ami_id) and ami_id.endswith('0'):
            result = AMICVE(
                ami_id=ami_id,
                ami_name=ami_name,
                region=self.region,
                severity="LOW",
                recommendation="AMI appears to be a placeholder. Use actual AMI ID for deployment."
            )

        # No known issues
        if not result:
            result = AMICVE(
                ami_id=ami_id,
                ami_name=ami_name,
                region=self.region,
                has_cve=False,
                is_outdated=False,
                severity="INFO",
                recommendation="No known CVEs detected (note: comprehensive check requires AWS API access)"
            )

        # Fetch alternative AMIs if there are issues
        if (result.has_cve or result.is_outdated) and self.ami_finder:
            try:
                alternatives = self.ami_finder.get_recommendation_for_ami(ami_id)
                result.suggested_alternatives = alternatives
            except Exception:
                # Gracefully handle alternative finding errors
                pass

        return result

    def extract_amis_from_template(self, content: str, template_type: str = "cloudformation") -> List[str]:
        """
        Extract AMI IDs from IaC template

        Args:
            content: Template content
            template_type: 'cloudformation' or 'terraform'

        Returns:
            List of AMI IDs found
        """
        ami_pattern = r'ami-[a-f0-9]{8,17}'
        amis = re.findall(ami_pattern, content, re.IGNORECASE)
        return list(set(amis))  # Remove duplicates

    def scan_template(self, content: str, template_type: str = "cloudformation") -> List[AMICVE]:
        """
        Scan all AMIs in a template

        Args:
            content: Template content
            template_type: 'cloudformation' or 'terraform'

        Returns:
            List of AMICVE objects
        """
        ami_ids = self.extract_amis_from_template(content, template_type)

        results = []
        for ami_id in ami_ids:
            result = self.check_ami(ami_id)
            results.append(result)

        self.scan_results = results
        return results

    def generate_report(self) -> str:
        """Generate AMI CVE report"""
        if not self.scan_results:
            return ""

        lines = []
        lines.append("")
        lines.append("=" * 80)
        lines.append("AMI SECURITY SCAN")
        lines.append(f"   Scan Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append("=" * 80)
        lines.append("")

        # Categorize
        amis_with_cves = [r for r in self.scan_results if r.has_cve]
        amis_outdated = [r for r in self.scan_results if r.is_outdated and not r.has_cve]
        amis_clean = [r for r in self.scan_results if not r.has_cve and not r.is_outdated]

        if amis_with_cves:
            lines.append("AMIs WITH KNOWN CVEs:")
            lines.append("")
            for ami in amis_with_cves:
                lines.append(f"   [FAIL] {ami.ami_id}")
                if ami.ami_name:
                    lines.append(f"          Name: {ami.ami_name}")
                if ami.cve_ids:
                    lines.append(f"          CVEs: {', '.join(ami.cve_ids)}")
                lines.append(f"          Severity: {ami.severity}")
                lines.append(f"          Recommendation: {ami.recommendation}")

                # Display suggested alternatives if available
                if ami.suggested_alternatives:
                    lines.append("")
                    lines.append("          SUGGESTED ALTERNATIVES:")
                    for idx, alt in enumerate(ami.suggested_alternatives[:3], 1):
                        lines.append(f"          {idx}. {alt.ami_id}")
                        lines.append(f"             Distribution: {alt.distribution} {alt.version}")
                        lines.append(f"             Region: {alt.region}")
                        lines.append(f"             Architecture: {alt.architecture}")
                        if alt.last_updated:
                            lines.append(f"             Last Updated: {alt.last_updated}")
                        lines.append(f"             Source: {alt.source}")
                        if idx < len(ami.suggested_alternatives[:3]):
                            lines.append("")

                lines.append("")

        if amis_outdated:
            lines.append("OUTDATED AMIs:")
            lines.append("")
            for ami in amis_outdated:
                lines.append(f"   [WARN] {ami.ami_id}")
                if ami.ami_name:
                    lines.append(f"          Name: {ami.ami_name}")
                lines.append(f"          Recommendation: {ami.recommendation}")

                # Display suggested alternatives if available
                if ami.suggested_alternatives:
                    lines.append("")
                    lines.append("          SUGGESTED ALTERNATIVES:")
                    for idx, alt in enumerate(ami.suggested_alternatives[:3], 1):
                        lines.append(f"          {idx}. {alt.ami_id}")
                        lines.append(f"             Distribution: {alt.distribution} {alt.version}")
                        lines.append(f"             Region: {alt.region}")
                        if alt.last_updated:
                            lines.append(f"             Last Updated: {alt.last_updated}")
                        lines.append(f"             Source: {alt.source}")
                        if idx < len(ami.suggested_alternatives[:3]):
                            lines.append("")

                lines.append("")

        if amis_clean:
            lines.append("AMIs WITH NO KNOWN ISSUES:")
            lines.append("")
            for ami in amis_clean:
                lines.append(f"   [PASS] {ami.ami_id}")
                if ami.recommendation:
                    lines.append(f"          {ami.recommendation}")
            lines.append("")

        # Summary
        lines.append("=" * 80)
        lines.append("SUMMARY:")
        lines.append(f"   Total AMIs Scanned: {len(self.scan_results)}")
        lines.append(f"   AMIs with CVEs: {len(amis_with_cves)}")
        lines.append(f"   Outdated AMIs: {len(amis_outdated)}")
        lines.append(f"   Clean AMIs: {len(amis_clean)}")
        lines.append("=" * 80)

        return "\n".join(lines)
