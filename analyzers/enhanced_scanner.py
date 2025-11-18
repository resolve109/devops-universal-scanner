#!/usr/bin/env python3
"""
Enhanced DevOps Scanner - Native Intelligence Layer
Runs base tools (checkov, cfn-lint, etc.) and adds intelligent analysis

Usage:
    python3 enhanced_scanner.py cloudformation <file_path> [--environment dev]
    python3 enhanced_scanner.py terraform <file_or_dir> [--environment prod]
"""

import sys
import os
import subprocess
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Import our analyzers
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.finops.cost_analyzer import CostAnalyzer
from analyzers.finops.optimization import OptimizationRecommender
from analyzers.finops.idle_detector import IdleResourceDetector
from analyzers.aiml.gpu_cost_analyzer import GPUCostAnalyzer
from analyzers.security.enhanced_checks import EnhancedSecurityChecker
from analyzers.reporting.report_generator import EnhancedReportGenerator

# Import pricing and CVE modules
from analyzers.core.pricing.aws_pricing import AWSPricingAPI
from analyzers.core.cve.tool_cve_scanner import ToolCVEScanner
from analyzers.core.cve.ami_cve_scanner import AMICVEScanner
from analyzers.core.cve.image_cve_scanner import ImageCVEScanner


class EnhancedScanner:
    """
    Enhanced scanner that runs base tools + native intelligence

    Operations:
    1. run_base_tools - Run checkov, cfn-lint, etc. with optimal flags
    2. extract_resources - Parse IaC files for resources
    3. analyze_costs - Run FinOps cost analysis
    4. analyze_security - Run enhanced security checks
    5. generate_report - Create comprehensive report
    """

    def __init__(self, scan_type: str, target: str, environment: str = "development"):
        self.scan_type = scan_type  # 'cloudformation', 'terraform', etc.
        self.target = target
        self.environment = environment
        self.file_content = ""

        # Initialize analyzers
        self.cost_analyzer = CostAnalyzer()
        self.optimization_recommender = OptimizationRecommender()
        self.idle_detector = IdleResourceDetector()
        self.gpu_analyzer = GPUCostAnalyzer()
        self.security_checker = EnhancedSecurityChecker()

        # Initialize pricing and CVE scanners
        self.pricing_api = AWSPricingAPI()
        self.tool_cve_scanner = ToolCVEScanner()
        self.ami_cve_scanner = AMICVEScanner()
        self.image_cve_scanner = ImageCVEScanner()

    def scan(self) -> str:
        """Run complete scan with all tools and analyzers"""
        print(f"\n{'='*80}")
        print(f"🚀 ENHANCED DEVOPS SCANNER - Native Intelligence Layer")
        print(f"{'='*80}\n")

        # Read file content
        try:
            with open(self.target, 'r') as f:
                self.file_content = f.read()
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return ""

        # Run analysis based on scan type
        if self.scan_type == "cloudformation":
            return self._scan_cloudformation()
        elif self.scan_type == "terraform":
            return self._scan_terraform()
        else:
            print(f"❌ Unsupported scan type: {self.scan_type}")
            return ""

    def _scan_cloudformation(self) -> str:
        """Scan CloudFormation template"""
        print(f"📄 Scanning CloudFormation template: {self.target}")
        print(f"🏷️  Environment: {self.environment}\n")

        # Step 1: Run cost analysis
        print("💰 Running FinOps cost analysis...")
        cost_breakdowns = self.cost_analyzer.analyze_cloudformation(self.file_content)

        # Step 2: Run optimization analysis
        print("💡 Analyzing optimization opportunities...")
        optimizations = self.optimization_recommender.analyze_all(cost_breakdowns, self.environment)

        # Step 3: Run GPU analysis (if GPU resources found)
        print("⚡ Analyzing GPU resources...")
        gpu_recommendations = self.gpu_analyzer.analyze(cost_breakdowns)

        # Step 4: Run security analysis
        print("🔒 Running enhanced security checks...")
        resources = self.cost_analyzer._extract_cloudformation_resources(self.file_content)
        security_insights = self.security_checker.analyze(resources)

        # Step 5: Run idle resource detection
        print("⚠️  Checking for idle resources...")
        idle_warnings = self.idle_detector.analyze(resources, cost_breakdowns)

        # Step 6: Run CVE scans
        print("🔐 Scanning for CVEs...")
        tool_cves = self.tool_cve_scanner.scan_all_tools()
        ami_cves = self.ami_cve_scanner.scan_template(self.file_content, "cloudformation")
        image_cves = self.image_cve_scanner.scan_template(self.file_content)

        # Step 7: Get pricing API status
        print("💵 Checking live pricing API status...")
        pricing_status = self.pricing_api.get_pricing_status()

        # Generate enhanced report
        print(f"\n{'='*80}")
        print("📊 GENERATING ENHANCED REPORT")
        print(f"{'='*80}\n")

        report = self._generate_enhanced_report(
            cost_breakdowns,
            optimizations,
            gpu_recommendations,
            security_insights,
            idle_warnings,
            tool_cves,
            ami_cves,
            image_cves,
            pricing_status
        )

        return report

    def _scan_terraform(self) -> str:
        """Scan Terraform file/directory"""
        print(f"📄 Scanning Terraform: {self.target}")
        print(f"🏷️  Environment: {self.environment}\n")

        # Step 1: Run cost analysis
        print("💰 Running FinOps cost analysis...")
        cost_breakdowns = self.cost_analyzer.analyze_terraform(self.file_content)

        # Step 2: Run optimization analysis
        print("💡 Analyzing optimization opportunities...")
        optimizations = self.optimization_recommender.analyze_all(cost_breakdowns, self.environment)

        # Step 3: Run GPU analysis
        print("⚡ Analyzing GPU resources...")
        gpu_recommendations = self.gpu_analyzer.analyze(cost_breakdowns)

        # Step 4: Run security analysis
        print("🔒 Running enhanced security checks...")
        resources = self.cost_analyzer._extract_terraform_resources(self.file_content)
        security_insights = self.security_checker.analyze(resources)

        # Step 5: Run idle resource detection
        print("⚠️  Checking for idle resources...")
        idle_warnings = self.idle_detector.analyze(resources, cost_breakdowns)

        # Step 6: Run CVE scans
        print("🔐 Scanning for CVEs...")
        tool_cves = self.tool_cve_scanner.scan_all_tools()
        ami_cves = self.ami_cve_scanner.scan_template(self.file_content, "terraform")
        image_cves = self.image_cve_scanner.scan_template(self.file_content)

        # Step 7: Get pricing API status
        print("💵 Checking live pricing API status...")
        pricing_status = self.pricing_api.get_pricing_status()

        # Generate enhanced report
        print(f"\n{'='*80}")
        print("📊 GENERATING ENHANCED REPORT")
        print(f"{'='*80}\n")

        report = self._generate_enhanced_report(
            cost_breakdowns,
            optimizations,
            gpu_recommendations,
            security_insights,
            idle_warnings,
            tool_cves,
            ami_cves,
            image_cves,
            pricing_status
        )

        return report

    def _generate_enhanced_report(self, cost_breakdowns, optimizations, gpu_recommendations,
                                  security_insights, idle_warnings, tool_cves, ami_cves,
                                  image_cves, pricing_status) -> str:
        """Generate comprehensive enhanced report"""
        lines = []

        # Header
        lines.append("")
        lines.append("=" * 80)
        lines.append("🎯 NATIVE INTELLIGENCE ANALYSIS")
        lines.append("=" * 80)

        # CVE Scans - Show first (security priority)
        lines.append(self.tool_cve_scanner.generate_report())

        if ami_cves:
            lines.append(self.ami_cve_scanner.generate_report())

        if image_cves:
            lines.append(self.image_cve_scanner.generate_report())

        # Cost Analysis (with pricing API status)
        if cost_breakdowns:
            lines.append(self.cost_analyzer.generate_cost_report())
            # Add pricing API status
            lines.append("")
            lines.append("💵 PRICING DATA SOURCE:")
            lines.append(f"   Provider: {pricing_status['provider']}")
            lines.append(f"   Region: {pricing_status['region']}")
            lines.append(f"   API Status: {'✅ Live' if pricing_status.get('api_available') else '⚠️  Using Fallback'}")
            lines.append(f"   {pricing_status.get('note', '')}")
            lines.append("")

        # Optimization Recommendations
        if optimizations:
            lines.append(self.optimization_recommender.generate_optimization_report())

        # GPU Analysis
        if gpu_recommendations:
            lines.append(self.gpu_analyzer.generate_gpu_report())

        # Idle Resources
        if idle_warnings:
            lines.append(self.idle_detector.generate_idle_report())

        # Security Insights
        if security_insights:
            lines.append(self.security_checker.generate_security_report())

        # Summary
        lines.append("")
        lines.append("=" * 80)
        lines.append("📊 ENHANCED SCAN SUMMARY")
        lines.append("=" * 80)
        total_cost = self.cost_analyzer.get_total_monthly_cost()
        total_savings = self.optimization_recommender.get_total_potential_savings()

        # CVE Summary
        tools_with_cves = len([t for t in tool_cves if t.has_cve])
        amis_with_cves = len([a for a in ami_cves if a.has_cve]) if ami_cves else 0
        lines.append(f"🔐 CVE Scan Results:")
        lines.append(f"   Tools with CVEs: {tools_with_cves}/{len(tool_cves)}")
        if ami_cves:
            lines.append(f"   AMIs with CVEs: {amis_with_cves}/{len(ami_cves)}")
        lines.append("")

        # Cost Summary
        if total_cost > 0:
            lines.append(f"💰 Total Monthly Cost: ${total_cost:,.2f}")
        if total_savings > 0:
            lines.append(f"💡 Potential Monthly Savings: ${total_savings:,.2f}")
            lines.append(f"📅 Potential Annual Savings: ${total_savings * 12:,.2f}")

        lines.append(f"🔍 Resources Analyzed: {len(cost_breakdowns)}")
        lines.append(f"💡 Recommendations Generated: {len(optimizations)}")
        if gpu_recommendations:
            lines.append(f"⚡ GPU Resources: {len(gpu_recommendations)}")
        if security_insights:
            lines.append(f"🔒 Security Insights: {len(security_insights)}")
        if idle_warnings:
            lines.append(f"⚠️  Idle Resource Warnings: {len(idle_warnings)}")

        lines.append("=" * 80)

        return "\n".join(lines)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Enhanced DevOps Scanner with Native Intelligence")
    parser.add_argument("scan_type", choices=["cloudformation", "terraform", "cf", "tf"],
                       help="Type of scan to perform")
    parser.add_argument("target", help="File or directory to scan")
    parser.add_argument("--environment", "-e", default="development",
                       choices=["development", "staging", "production", "testing", "demo"],
                       help="Environment type (affects recommendations)")

    args = parser.parse_args()

    # Normalize scan type
    scan_type = args.scan_type
    if scan_type == "cf":
        scan_type = "cloudformation"
    elif scan_type == "tf":
        scan_type = "terraform"

    # Run scanner
    scanner = EnhancedScanner(scan_type, args.target, args.environment)
    report = scanner.scan()

    # Print report
    print(report)


if __name__ == "__main__":
    main()
