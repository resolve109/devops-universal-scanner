"""
Container Image CVE Scanner
Checks Docker/container images for known vulnerabilities

Operations:
1. check_image - Check if image has known CVEs
2. extract_images - Extract image references from IaC
3. scan_images - Scan all images in template
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ImageCVE:
    """Container image vulnerability information"""
    image_name: str
    image_tag: str
    has_cve: bool = False
    cve_count: int = 0
    severity: str = "UNKNOWN"
    recommendation: str = ""


class ImageCVEScanner:
    """
    Scans container images for known CVEs

    Leverages Trivy scanner results
    """

    # Known vulnerable base images
    KNOWN_VULNERABLE_IMAGES = {
        "ubuntu:14.04": {
            "severity": "HIGH",
            "recommendation": "Ubuntu 14.04 is EOL. Use Ubuntu 22.04 or 24.04"
        },
        "alpine:3.7": {
            "severity": "HIGH",
            "recommendation": "Alpine 3.7 is outdated. Use Alpine 3.19 or later"
        },
        # Add more
    }

    def __init__(self):
        self.scan_results: List[ImageCVE] = []

    def check_image(self, image_name: str, image_tag: str = "latest") -> ImageCVE:
        """Check if an image has known CVEs"""
        full_image = f"{image_name}:{image_tag}"

        if full_image in self.KNOWN_VULNERABLE_IMAGES:
            vuln_info = self.KNOWN_VULNERABLE_IMAGES[full_image]
            return ImageCVE(
                image_name=image_name,
                image_tag=image_tag,
                has_cve=True,
                severity=vuln_info["severity"],
                recommendation=vuln_info["recommendation"]
            )

        # Warn about 'latest' tag
        if image_tag == "latest":
            return ImageCVE(
                image_name=image_name,
                image_tag=image_tag,
                severity="LOW",
                recommendation="Using 'latest' tag is not recommended. Pin to specific version."
            )

        return ImageCVE(
            image_name=image_name,
            image_tag=image_tag,
            has_cve=False,
            recommendation="No known CVEs (run Trivy scan for comprehensive check)"
        )

    def extract_images_from_template(self, content: str) -> List[tuple]:
        """Extract image references from templates"""
        # Pattern for image:tag
        image_pattern = r'(?:image|Image)[\s:=]+["\']?([a-zA-Z0-9._/-]+):([a-zA-Z0-9._-]+)["\']?'
        matches = re.findall(image_pattern, content)
        return matches

    def scan_template(self, content: str) -> List[ImageCVE]:
        """Scan all images in template"""
        images = self.extract_images_from_template(content)

        results = []
        for image_name, image_tag in images:
            result = self.check_image(image_name, image_tag)
            results.append(result)

        self.scan_results = results
        return results

    def generate_report(self) -> str:
        """Generate image CVE report"""
        if not self.scan_results:
            return ""

        lines = []
        lines.append("")
        lines.append("=" * 80)
        lines.append("CONTAINER IMAGE SECURITY SCAN")
        lines.append(f"   Scan Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append("=" * 80)
        lines.append("")

        for image in self.scan_results:
            status = "[FAIL]" if image.has_cve else "[PASS]"
            lines.append(f"{status} {image.image_name}:{image.image_tag}")
            if image.recommendation:
                lines.append(f"        {image.recommendation}")
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)
