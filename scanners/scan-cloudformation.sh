#!/bin/bash
# Enhanced CloudFormation Scanner with Comprehensive Logging
# Usage: scan-cloudformation template.yaml

set +e  # Handle errors gracefully

# Working directory setup
cd /work

TARGET="$1"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
OUTPUT_PATH="/work/cloudformation-scan-report-${TIMESTAMP}.log"

# Helper functions for logging with timestamps
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$OUTPUT_PATH"
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ SUCCESS: $1" | tee -a "$OUTPUT_PATH"
}

log_warning() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  WARNING: $1" | tee -a "$OUTPUT_PATH"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ ERROR: $1" | tee -a "$OUTPUT_PATH"
}

log_section() {
    echo "" | tee -a "$OUTPUT_PATH"
    echo "============================================================" | tee -a "$OUTPUT_PATH"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$OUTPUT_PATH"
    echo "============================================================" | tee -a "$OUTPUT_PATH"
}

# Input validation
if [ -z "$TARGET" ]; then
    echo "❌ Usage: scan-cloudformation <template.yaml|template.json>"
    echo "   Examples:"
    echo "     scan-cloudformation template.yaml"
    echo "     scan-cloudformation stack.json"
    exit 1
fi

# Remove /work/ prefix if provided
TARGET=$(echo "$TARGET" | sed 's|^/work/||')

# Initialize log file with header
echo "=================================================================" > "$OUTPUT_PATH"
echo "        CLOUDFORMATION SECURITY SCAN REPORT" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"

log_section "🚀 CloudFormation Scanner v2.0 - Comprehensive Logging"
log_message "📄 Target: $TARGET"
log_message "📍 Working directory: $(pwd)"
log_message "🕐 Scan started: $(date)"
log_message "📊 Output format: Comprehensive log with all tool outputs"

# Check if target exists
if [ ! -f "$TARGET" ]; then
    log_error "Target file '$TARGET' not found!"
    log_message "📂 Available CloudFormation files:"
    ls -la *.yaml *.yml *.json 2>/dev/null | tee -a "$OUTPUT_PATH" || echo "No CloudFormation files found" | tee -a "$OUTPUT_PATH"
    exit 1
fi

log_success "Target file '$TARGET' found and accessible"

# Show file details
log_message "📋 File information:"
ls -la "$TARGET" | tee -a "$OUTPUT_PATH"

# CFN-Lint Section
log_section "🔧 Running CFN-Lint - CloudFormation Linter"

log_message "Running CFN-Lint validation on template..."
cfn-lint "$TARGET" 2>&1 | tee -a "$OUTPUT_PATH"
CFNLINT_EXIT=$?

if [ $CFNLINT_EXIT -eq 0 ]; then
    log_success "CFN-Lint validation completed successfully - no issues found"
elif [ $CFNLINT_EXIT -eq 2 ]; then
    log_warning "CFN-Lint found warnings (exit code: $CFNLINT_EXIT)"
elif [ $CFNLINT_EXIT -eq 4 ]; then
    log_error "CFN-Lint found errors (exit code: $CFNLINT_EXIT)"
else
    log_error "CFN-Lint scan failed (exit code: $CFNLINT_EXIT)"
fi

# Checkov Section
log_section "🛡️ Running Checkov - Infrastructure Security Scanner"

log_message "Running Checkov security scan on CloudFormation template..."
checkov -f "$TARGET" --framework cloudformation 2>&1 | tee -a "$OUTPUT_PATH"
CHECKOV_EXIT=$?

if [ $CHECKOV_EXIT -eq 0 ]; then
    log_success "Checkov scan completed - no issues found"
elif [ $CHECKOV_EXIT -eq 1 ]; then
    log_warning "Checkov found security/compliance issues (exit code: $CHECKOV_EXIT)"
else
    log_error "Checkov scan failed (exit code: $CHECKOV_EXIT)"
fi

# AWS CLI Validation Section
log_section "☁️ Running AWS CloudFormation Validation"

log_message "Attempting AWS CloudFormation template validation..."
if command -v aws >/dev/null 2>&1; then
    aws cloudformation validate-template --template-body "file://$TARGET" 2>&1 | tee -a "$OUTPUT_PATH"
    AWS_EXIT=$?
    
    if [ $AWS_EXIT -eq 0 ]; then
        log_success "AWS CloudFormation validation completed successfully"
    else
        log_warning "AWS CloudFormation validation failed (exit code: $AWS_EXIT) - may be due to credentials or connectivity"
    fi
else
    AWS_EXIT=127
    log_warning "AWS CLI not available - skipping AWS validation"
fi

# Summary Section
log_section "📊 Scan Summary and Results"

log_message "Target: $TARGET"
log_message "🕐 Scan completed: $(date)"

# Calculate overall status
TOTAL_ISSUES=0
OVERALL_STATUS="SUCCESS"

if [ $CFNLINT_EXIT -ne 0 ]; then
    TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
    OVERALL_STATUS="ISSUES_FOUND"
fi

if [ $CHECKOV_EXIT -ne 0 ]; then
    TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
    OVERALL_STATUS="ISSUES_FOUND"
fi

# Note: AWS validation failure doesn't necessarily indicate template issues
if [ $AWS_EXIT -ne 0 ] && [ $AWS_EXIT -ne 127 ]; then
    log_message "Note: AWS validation failed but may be due to credentials/connectivity"
fi

# Final status
log_message "============================================================"
log_message "TOOL EXECUTION RESULTS:"
log_message "- CFN-Lint: $([ $CFNLINT_EXIT -eq 0 ] && echo "✅ PASSED" || echo "⚠️  ISSUES (exit $CFNLINT_EXIT)")"
log_message "- Checkov: $([ $CHECKOV_EXIT -eq 0 ] && echo "✅ PASSED" || echo "⚠️  ISSUES (exit $CHECKOV_EXIT)")"
log_message "- AWS Validation: $([ $AWS_EXIT -eq 0 ] && echo "✅ PASSED" || [ $AWS_EXIT -eq 127 ] && echo "⏭️  SKIPPED" || echo "⚠️  FAILED (exit $AWS_EXIT)")"
log_message "============================================================"

if [ "$OVERALL_STATUS" = "SUCCESS" ]; then
    log_success "Overall scan result: ALL TOOLS PASSED - No critical issues found!"
else
    log_warning "Overall scan result: ISSUES FOUND - Review the detailed output above"
fi

log_message "📄 Complete scan log saved to: cloudformation-scan-report-${TIMESTAMP}.log"
log_message "🎯 All tool outputs captured with timestamps and exit codes"

echo ""
echo "✅ CloudFormation scan completed! Report saved to: cloudformation-scan-report-${TIMESTAMP}.log"
else
    log_warning "Overall scan result: ISSUES FOUND - Review the detailed output above"
    log_message "Tools with issues: $TOTAL_ISSUES out of 2"
fi

log_message "📄 Complete scan log saved to: cloudformation-scan-report.log"
log_message "🎯 All tool outputs captured with timestamps and exit codes"

echo ""
echo "🎉 CloudFormation Scan Complete!"
echo "📄 Detailed log: cloudformation-scan-report.log"
echo "🎯 Target: $TARGET"
echo "📊 Overall Status: $OVERALL_STATUS"
