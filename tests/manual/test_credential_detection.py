#!/usr/bin/env python3
"""
Test script to verify cloud credential detection

Tests the new CLI-based credential detection for AWS, Azure, and GCP
"""

import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent))

from devops_universal_scanner.core.pricing.aws_pricing import AWSPricingAPI
from devops_universal_scanner.core.pricing.azure_pricing import AzurePricingAPI
from devops_universal_scanner.core.pricing.gcp_pricing import GCPPricingAPI


def test_aws_credentials():
    """Test AWS credential detection"""
    print("\n" + "=" * 60)
    print("Testing AWS Credential Detection")
    print("=" * 60)

    api = AWSPricingAPI()
    status = api.get_pricing_status()

    print(f"Provider: {status['provider']}")
    print(f"boto3 available: {status.get('boto3_available', 'N/A')}")
    print(f"Credentials available: {status['credentials_available']}")
    print(f"API available: {status['api_available']}")
    print(f"Using fallback: {status['using_fallback']}")
    print(f"Status: {status['status']}")

    if 'note' in status:
        print(f"Note: {status['note']}")

    if 'how_to_configure' in status:
        print(f"How to configure: {status['how_to_configure']}")

    return status['credentials_available']


def test_azure_credentials():
    """Test Azure credential detection"""
    print("\n" + "=" * 60)
    print("Testing Azure Credential Detection")
    print("=" * 60)

    api = AzurePricingAPI()
    status = api.get_pricing_status()

    print(f"Provider: {status['provider']}")
    print(f"Credentials available: {status['credentials_available']}")
    print(f"API available: {status['api_available']}")
    print(f"Using fallback: {status['using_fallback']}")
    print(f"Status: {status['status']}")

    if 'note' in status:
        print(f"Note: {status['note']}")

    if 'how_to_configure' in status:
        print(f"How to configure: {status['how_to_configure']}")

    return status['credentials_available']


def test_gcp_credentials():
    """Test GCP credential detection"""
    print("\n" + "=" * 60)
    print("Testing GCP Credential Detection")
    print("=" * 60)

    api = GCPPricingAPI()
    status = api.get_pricing_status()

    print(f"Provider: {status['provider']}")
    print(f"Credentials available: {status['credentials_available']}")
    print(f"API available: {status['api_available']}")
    print(f"Using fallback: {status['using_fallback']}")
    print(f"Status: {status['status']}")

    if 'note' in status:
        print(f"Note: {status['note']}")

    if 'how_to_configure' in status:
        print(f"How to configure: {status['how_to_configure']}")

    return status['credentials_available']


def main():
    """Run all credential detection tests"""
    print("\n" + "=" * 60)
    print("Cloud Credential Detection Test")
    print("=" * 60)
    print("\nThis test checks if cloud credentials are configured")
    print("using the CLI-based detection method (simpler and more reliable)")

    # Test all providers
    aws_ok = test_aws_credentials()
    azure_ok = test_azure_credentials()
    gcp_ok = test_gcp_credentials()

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"AWS credentials: {'✓ Found' if aws_ok else '✗ Not configured'}")
    print(f"Azure credentials: {'✓ Found' if azure_ok else '✗ Not configured'}")
    print(f"GCP credentials: {'✓ Found' if gcp_ok else '✗ Not configured'}")

    if not (aws_ok or azure_ok or gcp_ok):
        print("\nNo cloud credentials detected - all pricing will use static fallback data")
        print("\nTo configure credentials:")
        print("  AWS:   aws configure")
        print("  Azure: az login")
        print("  GCP:   gcloud auth login")
    else:
        print("\nAt least one cloud provider has credentials configured!")
        print("Live pricing API will be used where available.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
