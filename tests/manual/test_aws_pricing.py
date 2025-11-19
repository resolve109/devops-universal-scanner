#!/usr/bin/env python3
"""
Test AWS Pricing API Integration
Verifies boto3 detection, credential validation, and live pricing retrieval
"""

import sys
import os
from pathlib import Path

# Add the package to Python path
sys.path.insert(0, str(Path(__file__).parent))

from devops_universal_scanner.core.pricing.aws_pricing import AWSPricingAPI


def test_pricing_api():
    """Test AWS Pricing API integration"""

    print("=" * 80)
    print("AWS PRICING API INTEGRATION TEST")
    print("=" * 80)
    print()

    # Initialize pricing client
    print("1. Initializing AWS Pricing API client...")
    pricing = AWSPricingAPI(region="us-east-1")
    print("   ✓ Client initialized")
    print()

    # Check status
    print("2. Checking API status...")
    status = pricing.get_pricing_status()
    print()
    print("   PRICING API STATUS:")
    print("   " + "-" * 76)
    for key, value in status.items():
        print(f"   {key:25s}: {value}")
    print("   " + "-" * 76)
    print()

    # Test credential detection
    if status['boto3_available']:
        print("   ✓ boto3 is installed")
    else:
        print("   ✗ boto3 is NOT installed")
        print("     Install with: pip install boto3")
        return

    if status['credentials_available']:
        print("   ✓ AWS credentials are configured and valid")
    else:
        print("   ✗ AWS credentials are NOT configured")
        print(f"     Reason: {status.get('note', 'Unknown')}")
        print(f"     Help: {status.get('how_to_configure', 'N/A')}")

    print()

    # Test EC2 pricing
    print("3. Testing EC2 instance pricing...")
    test_instances = ["t3.micro", "t3.large", "m5.xlarge", "p3.2xlarge"]

    for instance_type in test_instances:
        result = pricing.get_ec2_pricing(instance_type, region="us-east-1")

        if result:
            source = result.get('source', 'unknown')
            monthly = result.get('monthly_cost', 0.0)
            hourly = result.get('hourly_cost', 0.0)
            note = result.get('note', '')

            icon = "✓" if source == "aws_pricing_api" else "⚠"
            print(f"   {icon} {instance_type:15s}: ${monthly:8.2f}/mo  ${hourly:6.4f}/hr  ({source})")

            if source == "static_fallback":
                fallback_reason = result.get('fallback_reason', 'unknown')
                print(f"     → Fallback reason: {fallback_reason}")
        else:
            print(f"   ✗ {instance_type:15s}: No pricing data available")

    print()

    # Test RDS pricing
    print("4. Testing RDS instance pricing...")
    test_rds = ["db.t3.micro", "db.m5.large"]

    for instance_class in test_rds:
        result = pricing.get_rds_pricing(instance_class, engine="mysql", region="us-east-1")

        if result:
            source = result.get('source', 'unknown')
            monthly = result.get('monthly_cost', 0.0)
            hourly = result.get('hourly_cost', 0.0)

            icon = "✓" if source == "aws_pricing_api" else "⚠"
            print(f"   {icon} {instance_class:15s}: ${monthly:8.2f}/mo  ${hourly:6.4f}/hr  ({source})")
        else:
            print(f"   ✗ {instance_class:15s}: No pricing data available")

    print()

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    if status['credentials_available']:
        print("✓ AWS Pricing API is ACTIVE - Live pricing data is being used")
        print()
        print("  Your scans will use REAL-TIME pricing from AWS.")
        print("  Pricing data is cached for 1 hour to minimize API calls.")
    else:
        print("⚠ AWS Pricing API is NOT ACTIVE - Using fallback pricing data")
        print()
        print("  Your scans will use STATIC pricing from:")
        print(f"    {status.get('fallback_data_source', 'Unknown source')}")
        print()
        print("  To enable live pricing:")
        print("  1. Configure AWS credentials:")
        print("     export AWS_ACCESS_KEY_ID='your-access-key'")
        print("     export AWS_SECRET_ACCESS_KEY='your-secret-key'")
        print("     OR")
        print("     aws configure")
        print()
        print("  2. Re-run the scanner")

    print("=" * 80)
    print()


if __name__ == "__main__":
    try:
        test_pricing_api()
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
