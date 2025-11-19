"""
AMI CVE Scanner
Checks AWS AMIs for known vulnerabilities and outdated versions

Operations:
1. check_ami - Check if AMI has known issues
2. check_ami_age - Check if AMI is outdated
3. scan_template_amis - Scan all AMIs in a template

TODO: ENHANCEMENT - AMI Alternative Suggestions (Priority: HIGH)
============================================================
When CVEs are detected in AMIs, provide actionable alternatives with specific AMI IDs.

IMPLEMENTATION PLAN:
-------------------
1. Create AMIAlternativeFinder class in new file: ami_alternative_finder.py
   - Integration with AWS SSM Parameter Store for official AMIs
   - Query latest AMI IDs for common distributions
   - Fallback to curated AMI database when AWS API unavailable

2. AMI Distribution Patterns to Support:
   - Amazon Linux 2023 (AL2023)
   - Amazon Linux 2 (AL2)
   - Ubuntu 24.04 LTS, 22.04 LTS, 20.04 LTS
   - RHEL 9.x, 8.x
   - Windows Server 2022, 2019
   - Debian 12, 11
   - SUSE Linux Enterprise Server

3. AWS SSM Parameter Paths (Official AMIs):
   /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64
   /aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2
   /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp2/ami-id
   /aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id

4. Enhanced AMICVE Dataclass:
   - Add suggested_alternatives: List[AMIAlternative]
   - AMIAlternative: ami_id, name, distribution, version, region, last_updated

5. Enhanced Recommendation Output:
   Current:  "Recommendation: Use latest Amazon Linux 2023 AMI"
   Enhanced: "Recommended Alternatives:
              - ami-0abc123def456789a (Amazon Linux 2023.3.20250115, us-east-1)
              - ami-0xyz987uvw654321b (Ubuntu 24.04 LTS, us-east-1)
              Updated: 2025-01-15"

6. CVE Verification for Suggestions:
   - Verify suggested AMIs don't have known CVEs before recommending
   - Cross-reference with NVD/CVE databases
   - Only suggest AMIs with clean security posture

7. Region-Aware Suggestions:
   - Detect region from template context
   - Provide AMI IDs specific to detected region
   - Support multi-region recommendations

8. Offline Fallback Database:
   - Maintain curated list in data/ami_alternatives.json
   - Update monthly via CI/CD pipeline
   - Include last known good AMIs for each distribution

9. Integration Points:
   - Modify check_ami() to call AMIAlternativeFinder
   - Update generate_report() to display alternatives
   - Add --suggest-alternatives CLI flag

10. Testing Requirements:
    - Unit tests for AMI pattern detection
    - Mock AWS SSM responses
    - Test offline fallback
    - Validate multi-region support

DEPENDENCIES:
- boto3 (already in requirements.txt)
- SSM parameter access (optional, gracefully degrade)
- NVD API for CVE verification (optional)

FILES TO CREATE/MODIFY:
- NEW: core/cve/ami_alternative_finder.py (main logic)
- NEW: core/data/ami_alternatives.json (fallback database)
- MODIFY: core/cve/ami_cve_scanner.py (integration)
- MODIFY: requirements.txt (add requests-cache for NVD API)

ESTIMATED EFFORT: 8-12 hours
RISK: Low (all changes additive, no breaking changes)
VALUE: High (makes recommendations actionable)
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class AMIAlternative:
    """
    AMI alternative suggestion

    TODO: Full implementation when AMIAlternativeFinder is created
    """
    ami_id: str
    name: str
    distribution: str  # e.g., "Amazon Linux 2023", "Ubuntu 24.04 LTS"
    version: str
    region: str
    architecture: str = "x86_64"  # or "arm64"
    last_updated: Optional[str] = None  # ISO format date
    verified_cve_free: bool = False


@dataclass
class AMICVE:
    """
    AMI vulnerability information

    TODO: Add suggested_alternatives field when enhancement is implemented
    """
    ami_id: str
    ami_name: Optional[str] = None
    region: str = "unknown"
    has_cve: bool = False
    cve_ids: List[str] = None
    is_outdated: bool = False
    age_days: Optional[int] = None
    severity: str = "UNKNOWN"
    recommendation: str = ""
    # TODO: Uncomment when AMIAlternativeFinder is implemented
    # suggested_alternatives: List[AMIAlternative] = field(default_factory=list)

    def __post_init__(self):
        if self.cve_ids is None:
            self.cve_ids = []


class AMICVEScanner:
    """
    Scans AWS AMIs for known CVEs and outdated versions

    Operations:
    1. Detects AMI IDs in IaC templates
    2. Checks against known vulnerable AMIs
    3. Recommends using latest AMIs
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

    def __init__(self):
        self.scan_results: List[AMICVE] = []

    def check_ami(self, ami_id: str, ami_name: Optional[str] = None) -> AMICVE:
        """
        Check if an AMI has known CVEs

        Args:
            ami_id: AMI ID (e.g., 'ami-0abcdef1234567890')
            ami_name: Optional AMI name for pattern matching

        Returns:
            AMICVE object with results
        """
        # Check against known vulnerable AMIs
        if ami_id in self.KNOWN_VULNERABLE_AMIS:
            vuln_info = self.KNOWN_VULNERABLE_AMIS[ami_id]
            return AMICVE(
                ami_id=ami_id,
                ami_name=ami_name,
                has_cve=True,
                cve_ids=vuln_info["cves"],
                severity=vuln_info["severity"],
                recommendation=vuln_info["recommendation"]
            )

        # Check AMI name for outdated patterns
        if ami_name:
            for pattern in self.OUTDATED_PATTERNS:
                if re.search(pattern, ami_name, re.IGNORECASE):
                    return AMICVE(
                        ami_id=ami_id,
                        ami_name=ami_name,
                        is_outdated=True,
                        severity="MEDIUM",
                        recommendation=f"AMI appears outdated based on name pattern. Consider using latest version."
                    )

        # Placeholder AMI (commonly used in examples)
        if re.match(r'ami-0[a-f0-9]{16}$', ami_id) and ami_id.endswith('0'):
            return AMICVE(
                ami_id=ami_id,
                ami_name=ami_name,
                severity="LOW",
                recommendation="AMI appears to be a placeholder. Use actual AMI ID for deployment."
            )

        # No known issues
        return AMICVE(
            ami_id=ami_id,
            ami_name=ami_name,
            has_cve=False,
            is_outdated=False,
            severity="INFO",
            recommendation="No known CVEs detected (note: comprehensive check requires AWS API access)"
        )

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

                # TODO: ENHANCEMENT - Display suggested alternatives
                # When AMIAlternativeFinder is implemented, add:
                # if ami.suggested_alternatives:
                #     lines.append("          Suggested Alternatives:")
                #     for alt in ami.suggested_alternatives[:3]:  # Show top 3
                #         lines.append(f"            - {alt.ami_id}")
                #         lines.append(f"              {alt.distribution} {alt.version} ({alt.region})")
                #         if alt.last_updated:
                #             lines.append(f"              Last Updated: {alt.last_updated}")
                #         if alt.verified_cve_free:
                #             lines.append(f"              Status: CVE-free (verified)")
                #     lines.append("")

                lines.append("")

        if amis_outdated:
            lines.append("OUTDATED AMIs:")
            lines.append("")
            for ami in amis_outdated:
                lines.append(f"   [WARN] {ami.ami_id}")
                if ami.ami_name:
                    lines.append(f"          Name: {ami.ami_name}")
                lines.append(f"          Recommendation: {ami.recommendation}")
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
