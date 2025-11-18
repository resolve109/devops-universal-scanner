"""
Tool CVE Scanner
Checks installed scanning tools for known CVEs

Operations:
1. check_tool_version - Get installed tool version
2. check_cves - Check if tool version has known CVEs
3. scan_all_tools - Scan all installed tools
"""

import subprocess
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ToolCVE:
    """CVE information for a tool"""
    tool_name: str
    current_version: str
    cve_id: Optional[str] = None
    severity: str = "UNKNOWN"
    description: str = ""
    fixed_version: Optional[str] = None
    has_cve: bool = False


class ToolCVEScanner:
    """
    Scans installed DevOps tools for known CVEs

    Checks: checkov, cfn-lint, terraform, tflint, tfsec, trivy, etc.
    """

    # Known CVEs for specific tool versions
    # This would be updated from a CVE database in production
    KNOWN_TOOL_CVES = {
        "checkov": {
            "3.1.0": ["CVE-2024-XXXXX"],  # Example
            "3.0.0": ["CVE-2024-YYYYY"],
        },
        "terraform": {
            "1.5.0": [],  # No known CVEs
        },
        # Add more as discovered
    }

    def __init__(self):
        self.scan_results: List[ToolCVE] = []

    def check_tool_version(self, tool_name: str) -> Optional[str]:
        """
        Get installed version of a tool

        Args:
            tool_name: Name of the tool

        Returns:
            Version string or None if not found
        """
        try:
            # Special handling for bicep (different version command)
            if tool_name == "bicep":
                version_flags = ["--version", "-v"]
            else:
                version_flags = ["--version", "-v", "version"]

            # Try common version flags
            for flag in version_flags:
                try:
                    result = subprocess.run(
                        [tool_name, flag],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    output = result.stdout + result.stderr

                    # Extract version number
                    # Common patterns: v1.2.3, 1.2.3, version 1.2.3, Bicep CLI version 0.x.x
                    version_pattern = r'v?(\d+\.\d+\.\d+(?:\.\d+)?)'
                    match = re.search(version_pattern, output)

                    if match:
                        return match.group(1)

                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue

            return None

        except Exception:
            return None

    def check_cves(self, tool_name: str, version: str) -> List[str]:
        """
        Check if a tool version has known CVEs

        Args:
            tool_name: Name of the tool
            version: Version string

        Returns:
            List of CVE IDs
        """
        tool_cves = self.KNOWN_TOOL_CVES.get(tool_name, {})
        return tool_cves.get(version, [])

    def scan_tool(self, tool_name: str) -> ToolCVE:
        """
        Scan a single tool for CVEs

        Args:
            tool_name: Name of the tool

        Returns:
            ToolCVE object with results
        """
        version = self.check_tool_version(tool_name)

        if not version:
            return ToolCVE(
                tool_name=tool_name,
                current_version="unknown",
                has_cve=False,
                description=f"{tool_name} not found or version not detected"
            )

        cves = self.check_cves(tool_name, version)

        if cves:
            return ToolCVE(
                tool_name=tool_name,
                current_version=version,
                cve_id=cves[0],  # First CVE
                severity="HIGH",  # Would be looked up from CVE database
                description=f"{tool_name} {version} has known CVEs",
                has_cve=True
            )
        else:
            return ToolCVE(
                tool_name=tool_name,
                current_version=version,
                has_cve=False,
                description=f"{tool_name} {version} - No known CVEs ✅"
            )

    def scan_all_tools(self) -> List[ToolCVE]:
        """
        Scan all installed DevOps tools

        Returns:
            List of ToolCVE objects
        """
        tools = [
            "checkov",
            "cfn-lint",
            "terraform",
            "tflint",
            "tfsec",
            "trivy",
            "bicep",
        ]

        results = []
        for tool in tools:
            result = self.scan_tool(tool)
            results.append(result)

        self.scan_results = results
        return results

    def generate_report(self) -> str:
        """Generate CVE report for tools"""
        if not self.scan_results:
            self.scan_all_tools()

        lines = []
        lines.append("")
        lines.append("=" * 80)
        lines.append("🔐 TOOL CVE SECURITY SCAN")
        lines.append(f"   Scan Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append("=" * 80)
        lines.append("")

        # Categorize results
        tools_with_cves = [r for r in self.scan_results if r.has_cve]
        tools_clean = [r for r in self.scan_results if not r.has_cve and r.current_version != "unknown"]
        tools_not_found = [r for r in self.scan_results if r.current_version == "unknown"]

        if tools_with_cves:
            lines.append("🔴 TOOLS WITH KNOWN CVEs:")
            lines.append("")
            for tool in tools_with_cves:
                lines.append(f"   ❌ {tool.tool_name} {tool.current_version}")
                lines.append(f"      CVE: {tool.cve_id}")
                lines.append(f"      Severity: {tool.severity}")
                lines.append(f"      {tool.description}")
                if tool.fixed_version:
                    lines.append(f"      💡 Update to: {tool.fixed_version}")
                lines.append("")

        if tools_clean:
            lines.append("✅ TOOLS WITH NO KNOWN CVEs:")
            lines.append("")
            for tool in tools_clean:
                lines.append(f"   ✅ {tool.tool_name} {tool.current_version} - Secure")
            lines.append("")

        if tools_not_found:
            lines.append("⚠️  TOOLS NOT FOUND:")
            lines.append("")
            for tool in tools_not_found:
                lines.append(f"   ⚠️  {tool.tool_name} - Not installed or not in PATH")
            lines.append("")

        # Summary
        lines.append("=" * 80)
        lines.append("SUMMARY:")
        lines.append(f"   Total Tools Scanned: {len(self.scan_results)}")
        lines.append(f"   🔴 Tools with CVEs: {len(tools_with_cves)}")
        lines.append(f"   ✅ Clean Tools: {len(tools_clean)}")
        lines.append(f"   ⚠️  Not Found: {len(tools_not_found)}")
        lines.append("=" * 80)

        return "\n".join(lines)
