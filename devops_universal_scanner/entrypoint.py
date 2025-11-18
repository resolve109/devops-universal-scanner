#!/usr/bin/env python3
"""
Docker Entrypoint - Pure Python
Handles container startup and command routing
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import List, Optional


class DockerEntrypoint:
    """Docker container entrypoint handler"""

    # Supported commands
    SCAN_COMMANDS = {
        "scan-terraform": "terraform",
        "scan-cloudformation": "cloudformation",
        "scan-docker": "docker",
        "scan-kubernetes": "kubernetes",
        "scan-arm": "arm",
        "scan-bicep": "bicep",
        "scan-gcp": "gcp",
    }

    # Help commands
    HELP_COMMANDS = ["help", "--help", "-h"]
    VERSION_COMMANDS = ["version", "--version", "-v"]

    def __init__(self):
        self.work_dir = Path("/work")

    def validate_volume_mount(self) -> bool:
        """
        Validate /work volume is mounted

        Returns:
            True if volume is properly mounted
        """
        if not self.work_dir.exists():
            return False

        # Check if volume is actually mounted (not just the empty directory)
        try:
            # Try to list contents - if volume not mounted, this will show empty
            list(self.work_dir.iterdir())
            return True
        except PermissionError:
            return False

    def display_volume_error(self):
        """Display helpful error message for volume mount issues"""
        print("\n" + "=" * 80)
        print("❌ ERROR: /work volume not mounted or empty")
        print("=" * 80)
        print()
        print("The scanner requires your files to be mounted at /work inside the container.")
        print()
        print("SOLUTIONS:")
        print()
        print("1. Mount your current directory:")
        print()
        print("   Linux/macOS:")
        print("   docker run --rm -v \"$(pwd):/work\" spd109/devops-uat:latest scan-terraform .")
        print()
        print("   Windows PowerShell:")
        print("   docker run --rm -v \"${PWD}:/work\" spd109/devops-uat:latest scan-terraform .")
        print()
        print("   Windows CMD:")
        print("   docker run --rm -v \"%cd%:/work\" spd109/devops-uat:latest scan-terraform .")
        print()
        print("2. Mount a specific directory:")
        print("   docker run --rm -v \"/path/to/your/files:/work\" spd109/devops-uat:latest scan-terraform .")
        print()
        print("=" * 80)
        print()

    def display_help(self):
        """Display help information"""
        help_text = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                   DevOps Universal Scanner v3.0                           ║
║                     Pure Python 3.13 Engine                               ║
╚═══════════════════════════════════════════════════════════════════════════╝

USAGE:
    docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest <command> <target>

SCAN COMMANDS:
    scan-terraform <target>       - Scan Terraform files/directories
    scan-cloudformation <target>  - Scan AWS CloudFormation templates
    scan-docker <target>          - Scan Dockerfiles or images
    scan-kubernetes <target>      - Scan Kubernetes manifests
    scan-arm <target>             - Scan Azure ARM templates
    scan-bicep <target>           - Scan Azure Bicep templates
    scan-gcp <target>             - Scan GCP Deployment Manager templates

EXAMPLES:
    # Scan Terraform directory
    docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform ./infrastructure

    # Scan CloudFormation template
    docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-cloudformation template.yaml

    # Scan Dockerfile
    docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-docker Dockerfile

    # Scan Kubernetes manifest
    docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-kubernetes deployment.yaml

FEATURES:
    ✅ Multi-tool scanning (Checkov, TFLint, TFSec, CFN-Lint, etc.)
    ✅ Native intelligence layer with FinOps analysis
    ✅ Live AWS/Azure/GCP pricing integration
    ✅ CVE scanning for tools, AMIs, and container images
    ✅ AI/ML GPU cost analysis
    ✅ Enhanced security insights
    ✅ Optimization recommendations
    ✅ Single consolidated log file per scan

OUTPUT:
    Each scan generates a timestamped log file:
    - terraform-scan-report-YYYYMMDD-HHMMSS.log
    - cloudformation-scan-report-YYYYMMDD-HHMMSS.log
    - etc.

ENVIRONMENT OPTIONS:
    Set environment type for optimization recommendations:
    docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform . --environment production

    Options: development (default), staging, production

MORE INFO:
    docker run --rm spd109/devops-uat:latest version
    docker run --rm spd109/devops-uat:latest help

"""
        print(help_text)

    def display_version(self):
        """Display version information"""
        print("\n" + "=" * 80)
        print("DevOps Universal Scanner v3.0")
        print("Pure Python 3.13 Engine")
        print("=" * 80)
        print()
        print("INSTALLED TOOLS:")
        print()

        # Check tool versions
        tools = [
            ("checkov", ["checkov", "--version"]),
            ("cfn-lint", ["cfn-lint", "--version"]),
            ("terraform", ["terraform", "--version"]),
            ("tflint", ["tflint", "--version"]),
            ("tfsec", ["tfsec", "--version"]),
            ("bicep", ["bicep", "--version"]),
        ]

        for tool_name, command in tools:
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                output = result.stdout.strip() or result.stderr.strip()
                version_line = output.split('\n')[0]
                print(f"  ✅ {tool_name}: {version_line}")
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                print(f"  ⚠️  {tool_name}: Not found or error")

        print()
        print("=" * 80)
        print()

    def route_scan_command(self, command: str, args: List[str]) -> int:
        """
        Route scan command to CLI

        Args:
            command: Scan command (e.g., 'scan-terraform')
            args: Additional arguments

        Returns:
            Exit code from scan
        """
        # Validate volume mount before proceeding
        if not self.validate_volume_mount():
            self.display_volume_error()
            return 1

        # Map command to scan type
        scan_type = self.SCAN_COMMANDS.get(command)
        if not scan_type:
            print(f"❌ Unknown command: {command}")
            self.display_help()
            return 1

        # Get target (first arg after command)
        if not args:
            print(f"❌ Error: No target specified for {command}")
            print(f"Usage: {command} <target>")
            return 1

        target = args[0]
        extra_args = args[1:]

        # Change to /work directory
        os.chdir(self.work_dir)

        # Build CLI command using Python module
        cli_command = [
            "python3",
            "-m",
            "devops_universal_scanner",
            scan_type,
            target
        ] + extra_args

        # Execute CLI
        try:
            result = subprocess.run(cli_command)
            return result.returncode
        except KeyboardInterrupt:
            print("\n⚠️  Scan interrupted")
            return 130
        except Exception as e:
            print(f"❌ Error executing scan: {e}")
            return 1

    def run(self, args: List[str]) -> int:
        """
        Main entrypoint logic

        Args:
            args: Command line arguments

        Returns:
            Exit code
        """
        # No arguments - show help
        if not args:
            self.display_help()
            return 0

        command = args[0].lower()
        remaining_args = args[1:]

        # Handle help commands
        if command in self.HELP_COMMANDS:
            self.display_help()
            return 0

        # Handle version commands
        if command in self.VERSION_COMMANDS:
            self.display_version()
            return 0

        # Handle scan commands
        if command in self.SCAN_COMMANDS:
            return self.route_scan_command(command, remaining_args)

        # Unknown command
        print(f"❌ Unknown command: {command}")
        self.display_help()
        return 1


def main():
    """Main entry point"""
    entrypoint = DockerEntrypoint()
    exit_code = entrypoint.run(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
