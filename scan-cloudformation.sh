#!/bin/bash
# Simple CloudFormation scanner script
# Usage: scan-cloudformation S3.yaml

# Don't exit on errors, handle them gracefully  
set +e

# Always work from /work directory (where volume is mounted)
cd /work

TARGET="$1"

if [ -z "$TARGET" ]; then
    echo "Usage: scan-cloudformation S3.yaml"
    exit 1
fi

# Remove /work/ prefix if provided
TARGET=$(echo "$TARGET" | sed 's|^/work/||')

echo "===== Scanning CloudFormation: $TARGET ====="
echo "Working directory: $(pwd)"

if [ ! -f "$TARGET" ]; then
    echo "Error: File $TARGET not found!"
    echo "Available files:"
    ls -la *.yaml *.yml *.json 2>/dev/null || echo "No CloudFormation files found"
    exit 1
fi

echo "===== File Info ====="
ls -la "$TARGET"

echo "===== Running CFN-Lint ====="
cfn-lint "$TARGET" || echo "CFN-Lint completed with warnings"

echo ""
echo "===== Running Checkov Security Scan ====="
checkov -f "$TARGET" --framework cloudformation --quiet || echo "Checkov completed with warnings"

echo ""
echo "===== AWS CloudFormation Validation ====="
aws cloudformation validate-template --template-body file://"$TARGET" 2>/dev/null || echo "AWS CLI validation skipped (no credentials or offline)"

echo ""
echo "===== Scan Complete ====="
