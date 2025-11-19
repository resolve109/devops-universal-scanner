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
# from devops_universal_scanner.core.cve.tool_cve_scanner import ToolCVEScanner  # Removed: Tool CVE scanning
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
        # self.tool_cve_scanner = ToolCVEScanner()  # Removed: Tool CVE scanning
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
            # Print header
            self.logger.section(f"{self.scan_type.upper()} Security Scan")
            self.logger.message(f"Target: {self.target}", timestamp=True)
            self.logger.message(f"Directory: {Path.cwd()}")

            # Validate target
            if not self.target.exists():
                self.logger.error(f"Target '{self.target}' not found")
                return 1

            self.logger.info(f"Target validated and accessible")

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
            self._generate_summary(exit_code)

            return exit_code

        finally:
            self.logger.close()

    def _scan_terraform(self) -> int:
        """Scan Terraform files"""
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
        # Run checkov
        checkov_result = self.tool_runner.run_checkov(self.target, "kubernetes")

        return 1 if not checkov_result.success else 0

    def _scan_azure_arm(self) -> int:
        """Scan Azure ARM template"""
        # Run checkov
        checkov_result = self.tool_runner.run_checkov(self.target, "arm")

        return 1 if not checkov_result.success else 0

    def _scan_azure_bicep(self) -> int:
        """Scan Azure Bicep template"""
        # Run checkov
        checkov_result = self.tool_runner.run_checkov(self.target, "bicep")

        return 1 if not checkov_result.success else 0

    def _scan_gcp(self) -> int:
        """Scan GCP Deployment Manager template"""
        # Run checkov
        checkov_result = self.tool_runner.run_checkov(self.target, "googledeploymentmanager")

        return 1 if not checkov_result.success else 0

    def _run_native_intelligence(self, template_type: str):
        """Run cost analysis and enhanced security checks"""
        self.logger.section("Cost Analysis", style="single")
        self.logger.info("Running cost analysis and security checks")

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
                # Extract parameters for CloudFormation
                import yaml
                try:
                    template = yaml.safe_load(file_content)
                    parameters = template.get("Parameters", {})
                except:
                    parameters = {}
                resources = self.cost_analyzer._extract_cloudformation_resources(file_content, parameters)
            else:
                resources = []

            security_insights = self.security_checker.analyze(resources)

            # Run idle detection
            idle_warnings = self.idle_detector.analyze(resources, cost_breakdowns)

            # Run CVE scans (Tool CVE scan removed for cleaner output)
            # tool_cves = self.tool_cve_scanner.scan_all_tools()  # Removed: Tool CVE scanning
            ami_cves = self.ami_cve_scanner.scan_template(file_content, template_type)
            image_cves = self.image_cve_scanner.scan_template(file_content)

            # Get pricing status
            pricing_status = self.pricing_api.get_pricing_status()

            # Generate reports (Tool CVE report removed)
            # self.logger.tool_output(self.tool_cve_scanner.generate_report())  # Removed: Tool CVE scanning

            if ami_cves:
                self.logger.tool_output(self.ami_cve_scanner.generate_report())

            if image_cves:
                self.logger.tool_output(self.image_cve_scanner.generate_report())

            if cost_breakdowns:
                self.logger.tool_output(self.cost_analyzer.generate_cost_report())
                self.logger.tool_output("")
                self.logger.tool_output("PRICING DATA SOURCE:")
                self.logger.tool_output(f"   Provider: {pricing_status['provider']}")
                self.logger.tool_output(f"   Region: {pricing_status['region']}")
                api_status = "Live" if pricing_status.get('api_available') else "Using Fallback"
                self.logger.tool_output(f"   API Status: {api_status}")
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

            self.logger.info("Cost analysis completed")

        except Exception as e:
            self.logger.error(f"Cost analysis failed: {e}")

    def _generate_summary(self, exit_code: int):
        """Generate final summary"""
        self.logger.section("Scan Summary")

        # Get tool results
        tool_summary = self.tool_runner.get_summary()

        self.logger.message(f"Target:    {self.target}")
        self.logger.message(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.message(f"Duration:  {self._get_scan_duration()}")
        self.logger.message("")
        self.logger.message("Tool Results:")

        for tool_name, result in tool_summary["results"].items():
            if result["success"]:
                status = "PASS"
            elif result["exit_code"] == 1:
                # Exit code 1 typically means security/compliance issues found (not tool failure)
                status = "SECURITY ISSUES"
            elif result["exit_code"] in [2, 6, 10, 12, 14]:
                # CFN-Lint error codes
                status = "VALIDATION ERRORS"
            elif result["exit_code"] == 4:
                # CFN-Lint warnings (should be success but good to note)
                status = "WARNINGS"
            else:
                status = f"FAILED (exit {result['exit_code']})"
            self.logger.message(f"  {tool_name:20s} {status}")

        self.logger.message("")

        if exit_code == 0:
            self.logger.success("Overall Status: PASS")
        else:
            self.logger.warning("Overall Status: ISSUES FOUND")

        self.logger.message(f"Log File: {self.log_file}")
        self.logger.section("")  # Closing divider

    def _get_scan_duration(self) -> str:
        """Calculate scan duration from log file timestamp"""
        try:
            # Get time from log filename
            timestamp_str = str(self.log_file).split('-')[-2] + str(self.log_file).split('-')[-1].replace('.log', '')
            start_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
            duration = (datetime.now() - start_time).total_seconds()
            return f"{int(duration)} seconds"
        except:
            return "N/A"
