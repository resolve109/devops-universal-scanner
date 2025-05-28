#!/bin/bash
# Simple Terraform scanner script
# Usage: scan-terraform terraform
# Usage: scan-terraform terraform/provider.tf

# Don't exit on errors, handle them gracefully
set +e

# Always work from /work directory (where volume is mounted)
cd /work

TARGET="$1"
OUTPUT_PATH="/work/terraform-scan-report.json"

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
    tflint --chdir=. --format=json > /tmp/tflint-report.json 2>/dev/null || echo "TFLint completed with warnings"
    tflint --chdir=. || echo "TFLint completed with warnings (console output)"
    
    echo ""
    echo "===== Running TFSec Security Scan ====="
    tfsec . --format=json --out=/tmp/tfsec-report.json 2>/dev/null || echo "TFSec JSON report generated"
    tfsec . || echo "TFSec completed with warnings"
    
    echo ""
    echo "===== Running Checkov Security Scan ====="
    checkov -d . --framework terraform --output=json --output-file=/tmp/checkov-report.json --quiet 2>/dev/null || echo "Checkov JSON report generated"
    checkov -d . --framework terraform --quiet || echo "Checkov completed with warnings"
else
    echo "Scanning Terraform file: $TARGET"
    
    echo "===== Running TFLint ====="
    tflint --chdir="$(dirname "$TARGET")" --filter="$TARGET" --format=json > /tmp/tflint-report.json 2>/dev/null || echo "TFLint JSON report generated"
    tflint --chdir="$(dirname "$TARGET")" --filter="$TARGET" || echo "TFLint completed with warnings"
    
    echo ""
    echo "===== Running TFSec Security Scan ====="
    tfsec "$TARGET" --format=json --out=/tmp/tfsec-report.json 2>/dev/null || echo "TFSec JSON report generated"
    tfsec "$TARGET" || echo "TFSec completed with warnings"
    
    echo ""
    echo "===== Running Checkov Security Scan ====="
    checkov -f "$TARGET" --output=json --output-file=/tmp/checkov-report.json --quiet 2>/dev/null || echo "Checkov JSON report generated"
    checkov -f "$TARGET" --quiet || echo "Checkov completed with warnings"
fi

echo "===== Generating Consolidated JSON Report ====="

# Create consolidated JSON report
cat > "$OUTPUT_PATH" << EOF
{
  "scan_info": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "target": "$TARGET",
    "scanner": "terraform-scan",
    "tools_used": ["tflint", "tfsec", "checkov"]
  },
  "tflint": $(cat /tmp/tflint-report.json 2>/dev/null || echo '{"issues": [], "errors": []}'),
  "tfsec": $(cat /tmp/tfsec-report.json 2>/dev/null || echo '{"results": []}'),
  "checkov": $(cat /tmp/checkov-report.json 2>/dev/null || echo '{"results": {"failed_checks": [], "passed_checks": []}}')
}
EOF

if [ -f "$OUTPUT_PATH" ]; then
    echo "✓ Detailed JSON report saved as terraform-scan-report.json"
    
    # Extract summary information using jq if available
    if command -v jq &> /dev/null; then
        tflint_issues=$(jq -r '.tflint.issues | length' "$OUTPUT_PATH" 2>/dev/null || echo "0")
        tfsec_results=$(jq -r '.tfsec.results | length' "$OUTPUT_PATH" 2>/dev/null || echo "0")
        checkov_failed=$(jq -r '.checkov.results.failed_checks | length' "$OUTPUT_PATH" 2>/dev/null || echo "0")
        checkov_passed=$(jq -r '.checkov.results.passed_checks | length' "$OUTPUT_PATH" 2>/dev/null || echo "0")
        
        echo ""
        echo "===== Scan Summary ====="
        echo "TFLint issues found: $tflint_issues"
        echo "TFSec security issues found: $tfsec_results"
        echo "Checkov failed checks: $checkov_failed"
        echo "Checkov passed checks: $checkov_passed"
        
        total_issues=$((tflint_issues + tfsec_results + checkov_failed))
        echo "Total issues found: $total_issues"
        
        if [ "$total_issues" -gt 0 ]; then
            echo ""
            echo "⚠ WARNING: Issues found in Terraform code!"
            echo "Review the detailed report in terraform-scan-report.json"
        else
            echo ""
            echo "✅ No critical issues found!"
        fi
    else
        echo "jq not available - install jq for summary statistics"
    fi
else
    echo "⚠ Could not generate detailed report"
fi

# Cleanup temporary files
rm -f /tmp/tflint-report.json /tmp/tfsec-report.json /tmp/checkov-report.json

echo ""
echo "===== Scan Complete ====="
echo "Target: $TARGET"
echo "Tools used: TFLint, TFSec, Checkov"
echo "Report saved: terraform-scan-report.json"
