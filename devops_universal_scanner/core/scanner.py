"""
Main Scanner - Orchestrates all scanning operations
Replaces all .sh scanner scripts with pure Python
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from devops_universal_scanner.core.logger import ScanLogger
from devops_universal_scanner.core.tool_runner import ToolRunner
from devops_universal_scanner.core.analyzers.finops.cost_analyzer import CostAnalyzer
from devops_universal_scanner.core.analyzers.finops.optimization import OptimizationRecommender
from devops_universal_scanner.core.analyzers.finops.idle_detector import IdleResourceDetector
from devops_universal_scanner.core.analyzers.aiml.gpu_cost_analyzer import GPUCostAnalyzer
from devops_universal_scanner.core.analyzers.security.enhanced_checks import EnhancedSecurityChecker
from devops_universal_scanner.core.cve.tool_cve_scanner import ToolCVEScanner
from devops_universal_scanner.core.cve.ami_cve_scanner import AMICVEScanner
from devops_universal_scanner.core.cve.image_cve_scanner import ImageCVEScanner
from devops_universal_scanner.core.pricing.aws_pricing import AWSPricingAPI
from devops_universal_scanner.core.knowledge import get_policy_loader, get_custom_rules_engine


class Scanner:
    """
    Main scanner orchestrator
    Replaces: scan-terraform.sh, scan-cloudformation.sh, etc.
    """

    def __init__(self, scan_type: str, target: Path, environment: str = "development"):
        """
        Initialize scanner

        Args:
            scan_type: Type of scan ('terraform', 'cloudformation', etc.)
            target: Target file or directory
            environment: Environment type (dev, staging, prod)
        """
        self.scan_type = scan_type
        self.target = Path(target)
        self.environment = environment

        # Generate log file name
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        self.log_file = Path(f"{scan_type}-scan-report-{timestamp}.log")

        # Initialize logger
        self.logger = ScanLogger(self.log_file)

        # Initialize tool runner
        self.tool_runner = ToolRunner(self.logger)

        # Initialize analyzers
        self.cost_analyzer = CostAnalyzer()
        self.optimization_recommender = OptimizationRecommender()
        self.idle_detector = IdleResourceDetector()
        self.gpu_analyzer = GPUCostAnalyzer()
        self.security_checker = EnhancedSecurityChecker()
        self.tool_cve_scanner = ToolCVEScanner()
        self.ami_cve_scanner = AMICVEScanner()
        self.image_cve_scanner = ImageCVEScanner()
        self.pricing_api = AWSPricingAPI()

    def scan(self) -> int:
        """
        Run complete scan

        Returns:
            Exit code (0 = success, >0 = issues found)
        """
        try:
            self.logger.section(f"🚀 {self.scan_type.title()} Scanner v3.0 - Pure Python Engine")
            self.logger.message(f"📁 Target: {self.target}")
            self.logger.message(f"📍 Working directory: {Path.cwd()}")
            self.logger.message(f"🕐 Scan started: {datetime.now()}")
            self.logger.message(f"🏷️  Environment: {self.environment}")

            # Validate target
            if not self.target.exists():
                self.logger.error(f"Target '{self.target}' not found!")
                return 1

            self.logger.success(f"Target '{self.target}' found and accessible")

            # Run appropriate scan
            if self.scan_type == "terraform":
                exit_code = self._scan_terraform()
            elif self.scan_type == "cloudformation":
                exit_code = self._scan_cloudformation()
            elif self.scan_type == "docker":
                exit_code = self._scan_docker()
            elif self.scan_type == "kubernetes":
                exit_code = self._scan_kubernetes()
            elif self.scan_type == "arm":
                exit_code = self._scan_azure_arm()
            elif self.scan_type == "bicep":
                exit_code = self._scan_azure_bicep()
            elif self.scan_type == "gcp":
                exit_code = self._scan_gcp()
            else:
                self.logger.error(f"Unsupported scan type: {self.scan_type}")
                return 1

            # Generate summary
            self._generate_summary()

            self.logger.message(f"📄 Complete scan log saved to: {self.log_file}")
            self.logger.message(f"🎯 All tool outputs captured with timestamps and exit codes")

            print(f"\n✅ {self.scan_type.title()} scan completed!")
            print(f"📄 Detailed log: {self.log_file}")

            return exit_code

        finally:
            self.logger.close()

    def _scan_terraform(self) -> int:
        """Scan Terraform files"""
        # Determine if directory or file
        if self.target.is_dir():
            self.logger.message(f"📂 Scanning Terraform directory: {self.target}")
        else:
            self.logger.message(f"📄 Scanning single Terraform file: {self.target}")

        # Run base tools
        tflint_result = self.tool_runner.run_tflint(self.target)
        tfsec_result = self.tool_runner.run_tfsec(self.target)
        checkov_result = self.tool_runner.run_checkov(self.target, "terraform")

        # Run native intelligence
        self._run_native_intelligence("terraform")

        # Determine exit code
        tools_with_issues = sum(1 for r in [tflint_result, tfsec_result, checkov_result] if not r.success)
        return 1 if tools_with_issues > 0 else 0

    def _scan_cloudformation(self) -> int:
        """Scan CloudFormation template"""
        self.logger.message(f"📄 Scanning CloudFormation template: {self.target}")

        # Run base tools
        cfnlint_result = self.tool_runner.run_cfn_lint(self.target)
        checkov_result = self.tool_runner.run_checkov(self.target, "cloudformation")
        aws_result = self.tool_runner.run_aws_cfn_validate(self.target)

        # Run native intelligence
        self._run_native_intelligence("cloudformation")

        # Determine exit code (AWS validation failure doesn't count as failure)
        tools_with_issues = sum(1 for r in [cfnlint_result, checkov_result] if not r.success)
        return 1 if tools_with_issues > 0 else 0

    def _scan_docker(self) -> int:
        """Scan Docker image or Dockerfile"""
        self.logger.message(f"📄 Scanning Docker: {self.target}")

        # For Dockerfile, use checkov
        if self.target.is_file():
            checkov_result = self.tool_runner.run_checkov(self.target, "dockerfile")
            return 1 if not checkov_result.success else 0

        # For images, would use trivy (but we removed it)
        self.logger.warning("Docker image scanning requires Trivy (not included in slim build)")
        self.logger.message("Recommendation: Use standalone trivy image:")
        self.logger.message(f"  docker run --rm aquasec/trivy image {self.target}")
        return 0

    def _scan_kubernetes(self) -> int:
        """Scan Kubernetes manifests"""
        self.logger.message(f"📄 Scanning Kubernetes manifest: {self.target}")

        # Run checkov
        checkov_result = self.tool_runner.run_checkov(self.target, "kubernetes")

        return 1 if not checkov_result.success else 0

    def _scan_azure_arm(self) -> int:
        """Scan Azure ARM template"""
        self.logger.message(f"📄 Scanning Azure ARM template: {self.target}")

        # Run checkov
        checkov_result = self.tool_runner.run_checkov(self.target, "arm")

        return 1 if not checkov_result.success else 0

    def _scan_azure_bicep(self) -> int:
        """Scan Azure Bicep template"""
        self.logger.message(f"📄 Scanning Azure Bicep template: {self.target}")

        # Run checkov
        checkov_result = self.tool_runner.run_checkov(self.target, "bicep")

        return 1 if not checkov_result.success else 0

    def _scan_gcp(self) -> int:
        """Scan GCP Deployment Manager template"""
        self.logger.message(f"📄 Scanning GCP template: {self.target}")

        # Run checkov
        checkov_result = self.tool_runner.run_checkov(self.target, "googledeploymentmanager")

        return 1 if not checkov_result.success else 0

    def _run_native_intelligence(self, template_type: str):
        """Run native intelligence analysis"""
        self.logger.section("🎯 Running Native Intelligence Analysis")
        self.logger.message("Running enhanced FinOps, Security, and AI/ML analysis...")

        try:
            # Read file content
            file_content = self.target.read_text()

            # Run cost analysis
            if template_type == "terraform":
                cost_breakdowns = self.cost_analyzer.analyze_terraform(file_content)
            elif template_type == "cloudformation":
                cost_breakdowns = self.cost_analyzer.analyze_cloudformation(file_content)
            else:
                cost_breakdowns = []

            # Run optimization analysis
            optimizations = self.optimization_recommender.analyze_all(cost_breakdowns, self.environment)

            # Run GPU analysis
            gpu_recommendations = self.gpu_analyzer.analyze(cost_breakdowns)

            # Run security analysis
            if template_type == "terraform":
                resources = self.cost_analyzer._extract_terraform_resources(file_content)
            elif template_type == "cloudformation":
                resources = self.cost_analyzer._extract_cloudformation_resources(file_content)
            else:
                resources = []

            security_insights = self.security_checker.analyze(resources)

            # Run idle detection
            idle_warnings = self.idle_detector.analyze(resources, cost_breakdowns)

            # Run CVE scans
            tool_cves = self.tool_cve_scanner.scan_all_tools()
            ami_cves = self.ami_cve_scanner.scan_template(file_content, template_type)
            image_cves = self.image_cve_scanner.scan_template(file_content)

            # Get pricing status
            pricing_status = self.pricing_api.get_pricing_status()

            # Generate reports
            self.logger.tool_output(self.tool_cve_scanner.generate_report())

            if ami_cves:
                self.logger.tool_output(self.ami_cve_scanner.generate_report())

            if image_cves:
                self.logger.tool_output(self.image_cve_scanner.generate_report())

            if cost_breakdowns:
                self.logger.tool_output(self.cost_analyzer.generate_cost_report())
                self.logger.tool_output("")
                self.logger.tool_output("💵 PRICING DATA SOURCE:")
                self.logger.tool_output(f"   Provider: {pricing_status['provider']}")
                self.logger.tool_output(f"   Region: {pricing_status['region']}")
                self.logger.tool_output(f"   API Status: {'✅ Live' if pricing_status.get('api_available') else '⚠️  Using Fallback'}")
                self.logger.tool_output(f"   {pricing_status.get('note', '')}")
                self.logger.tool_output("")

            if optimizations:
                self.logger.tool_output(self.optimization_recommender.generate_optimization_report())

            if gpu_recommendations:
                self.logger.tool_output(self.gpu_analyzer.generate_gpu_report())

            if idle_warnings:
                self.logger.tool_output(self.idle_detector.generate_idle_report())

            if security_insights:
                self.logger.tool_output(self.security_checker.generate_security_report())

            self.logger.success("Enhanced intelligence analysis completed")

        except Exception as e:
            self.logger.error(f"Native intelligence analysis failed: {e}")

    def _generate_summary(self):
        """Generate final summary"""
        self.logger.section("📊 Scan Summary and Results")

        # Get tool results
        tool_summary = self.tool_runner.get_summary()

        self.logger.message(f"Target: {self.target}")
        self.logger.message(f"🕐 Scan completed: {datetime.now()}")
        self.logger.message("=" * 60)
        self.logger.message("TOOL EXECUTION RESULTS:")

        for tool_name, result in tool_summary["results"].items():
            status = "✅ PASSED" if result["success"] else f"⚠️  ISSUES (exit {result['exit_code']})"
            self.logger.message(f"- {tool_name}: {status}")

        self.logger.message("=" * 60)

        if tool_summary["failed"] > 0:
            self.logger.warning("Overall scan result: ISSUES FOUND - Review the detailed output above")
            self.logger.message(f"Tools with issues: {tool_summary['failed']} out of {tool_summary['total_tools']}")
        else:
            self.logger.success("Overall scan result: ALL TOOLS PASSED - No critical issues found!")
