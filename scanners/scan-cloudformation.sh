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

# Count the actual errors and warnings in the output for better reporting
CFNLINT_ERRORS=$(grep -c "^E[0-9]\{4\}" "$OUTPUT_PATH" || echo "0")
CFNLINT_WARNINGS=$(grep -c "^W[0-9]\{4\}" "$OUTPUT_PATH" || echo "0")

# CFN-Lint exit codes: 0=no issues, 2=warnings, 4=errors, 6=warnings+errors
if [ $CFNLINT_EXIT -eq 0 ]; then
    log_success "CFN-Lint validation completed successfully - no issues found"
elif [ $CFNLINT_EXIT -eq 2 ]; then
    log_warning "CFN-Lint found $CFNLINT_WARNINGS warning(s) (exit code: $CFNLINT_EXIT)"
elif [ $CFNLINT_EXIT -eq 4 ]; then
    log_error "CFN-Lint found $CFNLINT_ERRORS error(s) (exit code: $CFNLINT_EXIT)"
elif [ $CFNLINT_EXIT -eq 6 ]; then
    log_error "CFN-Lint found $CFNLINT_ERRORS error(s) and $CFNLINT_WARNINGS warning(s) (exit code: $CFNLINT_EXIT)"
else
    log_error "CFN-Lint scan failed unexpectedly (exit code: $CFNLINT_EXIT)"
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

# Enhanced Native Intelligence Section
log_section "🎯 Running Native Intelligence Analysis"

log_message "Running enhanced FinOps, Security, and AI/ML analysis..."

# Detect environment from tags or default to development
ENVIRONMENT="${ENVIRONMENT:-development}"

# Run enhanced scanner (Python)
if [ -f "/usr/local/bin/analyzers/enhanced_scanner.py" ]; then
    python3 /usr/local/bin/analyzers/enhanced_scanner.py cloudformation "$TARGET" --environment "$ENVIRONMENT" 2>&1 | tee -a "$OUTPUT_PATH"
    ENHANCED_EXIT=$?

    if [ $ENHANCED_EXIT -eq 0 ]; then
        log_success "Enhanced intelligence analysis completed"
    else
        log_warning "Enhanced intelligence analysis completed with warnings (exit code: $ENHANCED_EXIT)"
    fi
else
    log_warning "Enhanced scanner not found - skipping native intelligence analysis"
    ENHANCED_EXIT=127
fi

# Summary Section
log_section "📊 Scan Summary and Results"

log_message "Target: $TARGET"
log_message "🕐 Scan completed: $(date)"

# Calculate overall status
TOTAL_ISSUES=0
OVERALL_STATUS="SUCCESS"

# CFN-Lint contributes to issues if warnings or errors found
if [ $CFNLINT_EXIT -eq 2 ] || [ $CFNLINT_EXIT -eq 4 ] || [ $CFNLINT_EXIT -eq 6 ]; then
    TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
    OVERALL_STATUS="ISSUES_FOUND"
fi

# Checkov contributes to issues if exit code is non-zero
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

# CFN-Lint detailed status
if [ $CFNLINT_EXIT -eq 0 ]; then
    log_message "- CFN-Lint: ✅ PASSED (no issues found)"
elif [ $CFNLINT_EXIT -eq 2 ]; then
    log_message "- CFN-Lint: ⚠️  WARNINGS FOUND ($CFNLINT_WARNINGS warnings, exit $CFNLINT_EXIT)"
elif [ $CFNLINT_EXIT -eq 4 ]; then
    log_message "- CFN-Lint: ❌ ERRORS FOUND ($CFNLINT_ERRORS errors, exit $CFNLINT_EXIT)"
elif [ $CFNLINT_EXIT -eq 6 ]; then
    log_message "- CFN-Lint: ❌ WARNINGS + ERRORS FOUND ($CFNLINT_ERRORS errors, $CFNLINT_WARNINGS warnings, exit $CFNLINT_EXIT)"
else
    log_message "- CFN-Lint: ❌ FAILED (exit $CFNLINT_EXIT)"
fi

log_message "- Checkov: $([ $CHECKOV_EXIT -eq 0 ] && echo "✅ PASSED" || echo "⚠️  ISSUES (exit $CHECKOV_EXIT)")"
log_message "- AWS Validation: $([ $AWS_EXIT -eq 0 ] && echo "✅ PASSED" || [ $AWS_EXIT -eq 127 ] && echo "⏭️  SKIPPED" || echo "⚠️  FAILED (exit $AWS_EXIT)")"
log_message "============================================================"

if [ "$OVERALL_STATUS" = "SUCCESS" ]; then
    log_success "Overall scan result: ALL TOOLS PASSED - No critical issues found!"
else
    log_warning "Overall scan result: ISSUES FOUND - Review the detailed output above"
    log_message "Tools with issues: $TOTAL_ISSUES out of 2"
    
    # List top issues for better visibility
    if [ $CFNLINT_EXIT -ne 0 ]; then
        log_message "CFN-Lint Issues Summary:"
        if [ $CFNLINT_ERRORS -gt 0 ]; then
            log_message "  - $CFNLINT_ERRORS error(s) found"
            # Extract and show the first 3 errors
            grep "^E[0-9]\{4\}" "$OUTPUT_PATH" | head -3 | while read -r line; do
                log_message "    ❌ $line"
            done
            if [ $CFNLINT_ERRORS -gt 3 ]; then
                log_message "    ... and more (see detailed log)"
            fi
        fi
        if [ $CFNLINT_WARNINGS -gt 0 ]; then
            log_message "  - $CFNLINT_WARNINGS warning(s) found"
            # Extract and show the first 3 warnings
            grep "^W[0-9]\{4\}" "$OUTPUT_PATH" | head -3 | while read -r line; do
                log_message "    ⚠️ $line"
            done
            if [ $CFNLINT_WARNINGS -gt 3 ]; then
                log_message "    ... and more (see detailed log)"
            fi
        fi
    fi
fi

log_message "📄 Complete scan log saved to: cloudformation-scan-report-${TIMESTAMP}.log"
log_message "🎯 All tool outputs captured with timestamps and exit codes"

echo ""
echo "✅ CloudFormation scan completed! Report saved to: cloudformation-scan-report-${TIMESTAMP}.log"
echo "🎉 CloudFormation Scan Complete!"
echo "📄 Detailed log: cloudformation-scan-report-${TIMESTAMP}.log"
echo "🎯 Target: $TARGET"
echo "📊 Overall Status: $OVERALL_STATUS"
