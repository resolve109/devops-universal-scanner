"""
Tool Runner - Executes base scanning tools
Runs: checkov, cfn-lint, terraform, tflint, tfsec, etc.
"""

import subprocess
import shutil
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from devops_universal_scanner.core.logger import ScanLogger


class ToolResult:
    """Result from a tool execution"""

    def __init__(self, tool_name: str, exit_code: int, stdout: str, stderr: str):
        self.tool_name = tool_name
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.success = exit_code == 0

    @property
    def output(self) -> str:
        """Combined output"""
        return self.stdout + self.stderr


class ToolRunner:
    """
    Runs scanning tools and captures output

    Operations:
    1. Check tool availability
    2. Execute tool with arguments
    3. Capture and return output
    4. Track exit codes
    """

    def __init__(self, logger: ScanLogger):
        self.logger = logger
        self.results: Dict[str, ToolResult] = {}

    def is_available(self, tool_name: str) -> bool:
        """Check if tool is available in PATH"""
        return shutil.which(tool_name) is not None

    def run(
        self,
        tool_name: str,
        args: list,
        cwd: Optional[Path] = None,
        check: bool = False
    ) -> ToolResult:
        """
        Run a tool and capture output

        Args:
            tool_name: Name of the tool (e.g., 'checkov')
            args: Command-line arguments
            cwd: Working directory
            check: Raise exception on non-zero exit code

        Returns:
            ToolResult with output and exit code
        """
        command = [tool_name] + args

        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            tool_result = ToolResult(
                tool_name=tool_name,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr
            )

            self.results[tool_name] = tool_result
            return tool_result

        except subprocess.TimeoutExpired:
            self.logger.error(f"{tool_name} timed out after 5 minutes")
            tool_result = ToolResult(tool_name, -1, "", "Timeout")
            self.results[tool_name] = tool_result
            return tool_result

        except FileNotFoundError:
            self.logger.error(f"{tool_name} not found in PATH")
            tool_result = ToolResult(tool_name, -1, "", "Not found")
            self.results[tool_name] = tool_result
            return tool_result

        except Exception as e:
            self.logger.error(f"{tool_name} execution failed: {e}")
            tool_result = ToolResult(tool_name, -1, "", str(e))
            self.results[tool_name] = tool_result
            return tool_result

    def run_cfn_lint(self, target: Path) -> ToolResult:
        """Run cfn-lint on CloudFormation template"""
        self.logger.section("CFN-Lint - CloudFormation Linter", style="single")
        self.logger.info("Running validation")

        result = self.run("cfn-lint", [str(target)])

        # Log output
        if result.output:
            self.logger.tool_output(result.output)

        # Log result based on CFN-Lint exit codes:
        # 0 = No issues
        # 2 = Errors found (template syntax/validation errors)
        # 4 = Warnings found (best practice violations)
        # 6 = Both errors and warnings
        # 8 = Informational messages
        # 10+ = Combination of above
        if result.exit_code == 0:
            self.logger.success("No issues found")
        elif result.exit_code == 4 or result.exit_code == 8:
            # Warnings/Info only - not a failure
            self.logger.warning(f"Warnings found (exit {result.exit_code})")
            # Override success flag for warnings-only
            result.success = True
        elif result.exit_code in [2, 6, 10, 12, 14]:
            # Errors found (with or without warnings)
            self.logger.warning(f"Validation errors found (exit {result.exit_code})")
        else:
            self.logger.error(f"Tool execution failed (exit {result.exit_code})")

        return result

    def run_checkov(self, target: Path, framework: str) -> ToolResult:
        """Run Checkov security scanner"""
        self.logger.section("Checkov - Infrastructure Security Scanner", style="single")
        self.logger.info(f"Running security scan (framework: {framework})")

        # Determine scan type
        if target.is_dir():
            args = ["-d", str(target), "--framework", framework]
        else:
            args = ["-f", str(target), "--framework", framework]

        result = self.run("checkov", args)

        # Log output
        if result.output:
            self.logger.tool_output(result.output)

        # Log result
        if result.exit_code == 0:
            self.logger.success("No security issues found")
        elif result.exit_code == 1:
            self.logger.warning(f"Security issues found (exit {result.exit_code})")
        else:
            self.logger.error(f"Tool execution failed (exit {result.exit_code})")

        return result

    def run_terraform_validate(self, target_dir: Path) -> ToolResult:
        """Run terraform validate"""
        self.logger.section("Terraform Validate", style="single")
        self.logger.info("Validating Terraform configuration")

        # Initialize first (required for validate)
        init_result = self.run("terraform", ["init", "-backend=false"], cwd=target_dir)

        if init_result.exit_code != 0:
            self.logger.warning("Terraform init failed, skipping validate")
            return init_result

        # Now validate
        result = self.run("terraform", ["validate"], cwd=target_dir)

        if result.output:
            self.logger.tool_output(result.output)

        if result.exit_code == 0:
            self.logger.success("Validation passed")
        else:
            self.logger.error(f"Validation failed (exit {result.exit_code})")

        return result

    def run_tflint(self, target: Path) -> ToolResult:
        """Run TFLint on Terraform files"""
        self.logger.section("TFLint - Terraform Linter", style="single")

        # Initialize TFLint
        if target.is_dir():
            self.logger.info("Initializing TFLint")
            init_result = self.run("tflint", ["--init"], cwd=target)
            if init_result.output:
                self.logger.tool_output(init_result.output)

            if init_result.exit_code == 0:
                self.logger.info("Initialization complete")

            # Run scan
            self.logger.info("Running scan")
            result = self.run("tflint", ["--chdir=."], cwd=target)
        else:
            self.logger.info("Running scan")
            result = self.run("tflint", [
                f"--chdir={target.parent}",
                f"--filter={target.name}"
            ])

        if result.output:
            self.logger.tool_output(result.output)

        if result.exit_code == 0:
            self.logger.success("No issues found")
        elif result.exit_code == 2:
            self.logger.warning(f"Issues found (exit {result.exit_code})")
        else:
            self.logger.error(f"Tool execution failed (exit {result.exit_code})")

        return result

    def run_tfsec(self, target: Path) -> ToolResult:
        """Run TFSec security scanner"""
        self.logger.section("TFSec - Terraform Security Scanner", style="single")
        self.logger.info("Running security scan")

        result = self.run("tfsec", [str(target)])

        if result.output:
            self.logger.tool_output(result.output)

        if result.exit_code == 0:
            self.logger.success("No security issues found")
        elif result.exit_code == 1:
            self.logger.warning(f"Security issues found (exit {result.exit_code})")
        else:
            self.logger.error(f"Tool execution failed (exit {result.exit_code})")

        return result

    def run_aws_cfn_validate(self, target: Path) -> ToolResult:
        """Run AWS CloudFormation validation (if AWS CLI available)"""
        if not self.is_available("aws"):
            self.logger.warning("AWS CLI not available - skipping AWS validation")
            return ToolResult("aws", 127, "", "AWS CLI not available")

        self.logger.section("AWS CloudFormation Validation", style="single")
        self.logger.info("Attempting template validation")

        result = self.run("aws", [
            "cloudformation", "validate-template",
            "--template-body", f"file://{target}"
        ])

        if result.output:
            self.logger.tool_output(result.output)

        if result.exit_code == 0:
            self.logger.success("Validation passed")
        else:
            self.logger.warning(
                f"Validation failed (exit {result.exit_code}) - may be due to credentials or connectivity"
            )

        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all tool results"""
        summary = {
            "total_tools": len(self.results),
            "passed": sum(1 for r in self.results.values() if r.success),
            "failed": sum(1 for r in self.results.values() if not r.success),
            "results": {}
        }

        for tool_name, result in self.results.items():
            summary["results"][tool_name] = {
                "exit_code": result.exit_code,
                "success": result.success
            }

        return summary
