#!/usr/bin/env python3
"""
DevOps Universal Scanner - CLI Entry Point
Pure Python 3.13 scanning engine for Infrastructure as Code

Usage:
    python3 cli.py <scan-type> <target> [options]

Scan Types:
    terraform       - Scan Terraform files/directories
    cloudformation  - Scan AWS CloudFormation templates
    docker          - Scan Dockerfiles or Docker images
    kubernetes      - Scan Kubernetes manifests
    arm             - Scan Azure ARM templates
    bicep           - Scan Azure Bicep templates
    gcp             - Scan GCP Deployment Manager templates

Examples:
    python3 cli.py terraform ./infrastructure
    python3 cli.py cloudformation template.yaml
    python3 cli.py docker Dockerfile
    python3 cli.py kubernetes deployment.yaml
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from devops_universal_scanner.core.scanner import Scanner


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="DevOps Universal Scanner - Pure Python 3.13 Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Scan Types:
  terraform       - Scan Terraform files/directories (TFLint, TFSec, Checkov)
  cloudformation  - Scan AWS CloudFormation templates (CFN-Lint, Checkov, AWS Validate)
  docker          - Scan Dockerfiles or Docker images (Checkov)
  kubernetes      - Scan Kubernetes manifests (Checkov)
  arm             - Scan Azure ARM templates (Checkov)
  bicep           - Scan Azure Bicep templates (Checkov)
  gcp             - Scan GCP Deployment Manager templates (Checkov)

Examples:
  python3 cli.py terraform ./infrastructure
  python3 cli.py cloudformation template.yaml
  python3 cli.py docker Dockerfile
  python3 cli.py kubernetes deployment.yaml

Environment:
  Set environment type with --environment (development, staging, production)
  Default: development
        """
    )

    parser.add_argument(
        "scan_type",
        choices=["terraform", "cloudformation", "docker", "kubernetes", "arm", "bicep", "gcp"],
        help="Type of scan to perform"
    )

    parser.add_argument(
        "target",
        help="Target file or directory to scan"
    )

    parser.add_argument(
        "--environment",
        "-e",
        choices=["development", "staging", "production"],
        default="development",
        help="Environment type (affects optimization recommendations)"
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="DevOps Universal Scanner v3.0 - Pure Python Engine"
    )

    return parser.parse_args()


def validate_target(target: str) -> Optional[Path]:
    """
    Validate target path exists

    Args:
        target: Target file or directory path

    Returns:
        Path object if valid, None otherwise
    """
    target_path = Path(target)

    if not target_path.exists():
        print(f"❌ Error: Target '{target}' not found")
        print(f"   Current directory: {Path.cwd()}")
        return None

    return target_path


def display_banner():
    """Display scanner banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                   DevOps Universal Scanner v3.0                           ║
║                     Pure Python 3.13 Engine                               ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def main() -> int:
    """
    Main CLI entry point

    Returns:
        Exit code (0 = success, >0 = issues found)
    """
    # Parse arguments
    args = parse_arguments()

    # Display banner
    display_banner()

    # Validate target
    target_path = validate_target(args.target)
    if not target_path:
        return 1

    try:
        # Create scanner instance
        scanner = Scanner(
            scan_type=args.scan_type,
            target=target_path,
            environment=args.environment
        )

        # Run scan
        exit_code = scanner.scan()

        return exit_code

    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
        return 130

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
