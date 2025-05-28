#!/bin/bash
# Simple CloudFormation scanner script
# Usage: scan-cloudformation S3.yaml

# Don't exit on errors, handle them gracefully  
set +e

# Always work from /work directory (where volume is mounted)
cd /work

TARGET="$1"
OUTPUT_PATH="/work/cloudformation-scan-report.json"

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
cfn-lint "$TARGET" --format=json > /tmp/cfn-lint-report.json 2>/dev/null || echo "CFN-Lint JSON report generated"
cfn-lint "$TARGET" || echo "CFN-Lint completed with warnings"

echo ""
echo "===== Running Checkov Security Scan ====="
checkov -f "$TARGET" --framework cloudformation --output=json --output-file=/tmp/checkov-report.json --quiet 2>/dev/null || echo "Checkov JSON report generated"
checkov -f "$TARGET" --framework cloudformation --quiet || echo "Checkov completed with warnings"

echo ""
echo "===== AWS CloudFormation Validation ====="
aws cloudformation validate-template --template-body file://"$TARGET" > /tmp/aws-cfn-validate.json 2>/dev/null || echo "AWS CLI validation skipped (no credentials or offline)"

echo "===== Generating Consolidated JSON Report ====="

# Create consolidated JSON report
cat > "$OUTPUT_PATH" << EOF
{
  "scan_info": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "target": "$TARGET",
    "scanner": "cloudformation-scan",
    "tools_used": ["cfn-lint", "checkov", "aws-cli-validate"]
  },
  "cfn_lint": $(cat /tmp/cfn-lint-report.json 2>/dev/null || echo '[]'),
  "checkov": $(cat /tmp/checkov-report.json 2>/dev/null || echo '{"results": {"failed_checks": [], "passed_checks": []}}'),
  "aws_validation": $(cat /tmp/aws-cfn-validate.json 2>/dev/null || echo '{"status": "skipped", "reason": "AWS CLI not configured or offline"}')
}
EOF

if [ -f "$OUTPUT_PATH" ]; then
    echo "✓ Detailed JSON report saved as cloudformation-scan-report.json"
    
    # Extract summary information using jq if available
    if command -v jq &> /dev/null; then
        cfn_lint_issues=$(jq -r 'length' "$OUTPUT_PATH" 2>/dev/null || echo "0")
        checkov_failed=$(jq -r '.checkov.results.failed_checks | length' "$OUTPUT_PATH" 2>/dev/null || echo "0")
        checkov_passed=$(jq -r '.checkov.results.passed_checks | length' "$OUTPUT_PATH" 2>/dev/null || echo "0")
        aws_status=$(jq -r '.aws_validation.status // "unknown"' "$OUTPUT_PATH" 2>/dev/null)
        
        echo ""
        echo "===== Scan Summary ====="
        echo "CFN-Lint issues found: $cfn_lint_issues"
        echo "Checkov failed checks: $checkov_failed"
        echo "Checkov passed checks: $checkov_passed"
        echo "AWS validation status: $aws_status"
        
        total_issues=$((cfn_lint_issues + checkov_failed))
        echo "Total issues found: $total_issues"
        
        if [ "$total_issues" -gt 0 ]; then
            echo ""
            echo "⚠ WARNING: Issues found in CloudFormation template!"
            echo "Review the detailed report in cloudformation-scan-report.json"
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
rm -f /tmp/cfn-lint-report.json /tmp/checkov-report.json /tmp/aws-cfn-validate.json

echo ""
echo "===== Scan Complete ====="
echo "Target: $TARGET"
echo "Tools used: CFN-Lint, Checkov, AWS CLI Validation"
echo "Report saved: cloudformation-scan-report.json"
