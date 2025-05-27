#!/bin/bash
# Simple Terraform scanner script
# Usage: scan-terraform terraform
# Usage: scan-terraform terraform/provider.tf

# Don't exit on errors, handle them gracefully
set +e

# Always work from /work directory (where volume is mounted)
cd /work

TARGET="$1"

if [ -z "$TARGET" ]; then
    echo "Usage: scan-terraform terraform"
    echo "Usage: scan-terraform terraform/provider.tf"
    exit 1
fi

# Remove /work/ prefix if provided
TARGET=$(echo "$TARGET" | sed 's|^/work/||')

echo "===== Scanning Terraform: $TARGET ====="
echo "Working directory: $(pwd)"

if [ ! -e "$TARGET" ]; then
    echo "Error: $TARGET not found!"
    echo "Available files:"
    ls -la
    exit 1
fi

if [ -d "$TARGET" ]; then
    echo "Scanning Terraform directory: $TARGET"
    cd "$TARGET"
    
    echo "Found Terraform files:"
    ls -la *.tf 2>/dev/null || echo "No .tf files found"
    
    echo "===== Running TFLint ====="
    tflint --init 2>/dev/null || echo "TFLint init skipped"
    tflint --chdir=. || echo "TFLint completed with warnings"
    
    echo ""
    echo "===== Running TFSec Security Scan ====="
    tfsec . || echo "TFSec completed with warnings"
    
    echo ""
    echo "===== Running Checkov Security Scan ====="
    checkov -d . --framework terraform --quiet || echo "Checkov completed with warnings"
else
    echo "Scanning Terraform file: $TARGET"
    
    echo "===== Running TFLint ====="
    tflint --chdir="$(dirname "$TARGET")" --filter="$TARGET" || echo "TFLint completed with warnings"
    
    echo ""
    echo "===== Running TFSec Security Scan ====="
    tfsec "$TARGET" || echo "TFSec completed with warnings"
    
    echo ""
    echo "===== Running Checkov Security Scan ====="
    checkov -f "$TARGET" --quiet || echo "Checkov completed with warnings"
fi

echo "===== Scan Complete ====="
