#!/bin/bash
# Enhanced Terraform Scanner with Comprehensive Logging
# Usage: scan-terraform terraform/
# Usage: scan-terraform provider.tf

set +e  # Handle errors gracefully

# Working directory setup
cd /work

TARGET="$1"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
OUTPUT_PATH="/work/terraform-scan-report-${TIMESTAMP}.log"

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
    echo "❌ Usage: scan-terraform <terraform_directory_or_file>"
    echo "   Examples:"
    echo "     scan-terraform terraform/"
    echo "     scan-terraform main.tf"
    exit 1
fi

# Remove /work/ prefix if provided
TARGET=$(echo "$TARGET" | sed 's|^/work/||')

# Initialize log file with header
echo "=================================================================" > "$OUTPUT_PATH"
echo "          TERRAFORM SECURITY SCAN REPORT" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"

log_section "🚀 Terraform Scanner v2.0 - Comprehensive Logging"
log_message "📁 Target: $TARGET"
log_message "📍 Working directory: $(pwd)"
log_message "🕐 Scan started: $(date)"
log_message "📊 Output format: Comprehensive log with all tool outputs"

# Check if target exists
if [ ! -e "$TARGET" ]; then
    log_error "Target '$TARGET' not found!"
    log_message "📂 Available files in current directory:"
    ls -la | tee -a "$OUTPUT_PATH"
    exit 1
fi

log_success "Target '$TARGET' found and accessible"

# Determine scan type
if [ -d "$TARGET" ]; then
    SCAN_TYPE="directory"
    log_message "📂 Scanning Terraform directory: $TARGET"
    
    log_message "📋 Terraform files found:"
    find "$TARGET" -name "*.tf" -type f | tee -a "$OUTPUT_PATH"
    
    cd "$TARGET"
else
    SCAN_TYPE="file"
    log_message "📄 Scanning single Terraform file: $TARGET"
    
    # Show file details
    log_message "📋 File information:"
    ls -la "$TARGET" | tee -a "$OUTPUT_PATH"
fi

# TFLint Section
log_section "🔧 Running TFLint - Terraform Linter"

if [ "$SCAN_TYPE" = "directory" ]; then
    log_message "Initializing TFLint..."
    tflint --init 2>&1 | tee -a "$OUTPUT_PATH"
    TFLINT_INIT_EXIT=$?
    
    if [ $TFLINT_INIT_EXIT -eq 0 ]; then
        log_success "TFLint initialization completed"
    else
        log_warning "TFLint initialization had warnings (exit code: $TFLINT_INIT_EXIT)"
    fi
    
    log_message "Running TFLint scan on directory..."
    tflint --chdir=. 2>&1 | tee -a "$OUTPUT_PATH"
    TFLINT_EXIT=$?
else
    log_message "Running TFLint scan on file..."
    tflint --chdir="$(dirname "$TARGET")" --filter="$TARGET" 2>&1 | tee -a "$OUTPUT_PATH"
    TFLINT_EXIT=$?
fi

if [ $TFLINT_EXIT -eq 0 ]; then
    log_success "TFLint scan completed successfully"
elif [ $TFLINT_EXIT -eq 2 ]; then
    log_warning "TFLint found issues (exit code: $TFLINT_EXIT)"
else
    log_error "TFLint scan failed (exit code: $TFLINT_EXIT)"
fi

# TFSec Section
log_section "🔒 Running TFSec - Terraform Security Scanner"

if [ "$SCAN_TYPE" = "directory" ]; then
    log_message "Running TFSec security scan on directory..."
    tfsec . 2>&1 | tee -a "$OUTPUT_PATH"
    TFSEC_EXIT=$?
else
    log_message "Running TFSec security scan on file..."
    tfsec "$TARGET" 2>&1 | tee -a "$OUTPUT_PATH"
    TFSEC_EXIT=$?
fi

if [ $TFSEC_EXIT -eq 0 ]; then
    log_success "TFSec scan completed - no security issues found"
elif [ $TFSEC_EXIT -eq 1 ]; then
    log_warning "TFSec found security issues (exit code: $TFSEC_EXIT)"
else
    log_error "TFSec scan failed (exit code: $TFSEC_EXIT)"
fi

# Checkov Section
log_section "🛡️ Running Checkov - Infrastructure Security Scanner"

if [ "$SCAN_TYPE" = "directory" ]; then
    log_message "Running Checkov scan on directory..."
    checkov -d . --framework terraform 2>&1 | tee -a "$OUTPUT_PATH"
    CHECKOV_EXIT=$?
else
    log_message "Running Checkov scan on file..."
    checkov -f "$TARGET" --framework terraform 2>&1 | tee -a "$OUTPUT_PATH"
    CHECKOV_EXIT=$?
fi

if [ $CHECKOV_EXIT -eq 0 ]; then
    log_success "Checkov scan completed - no issues found"
elif [ $CHECKOV_EXIT -eq 1 ]; then
    log_warning "Checkov found security/compliance issues (exit code: $CHECKOV_EXIT)"
else
    log_error "Checkov scan failed (exit code: $CHECKOV_EXIT)"
fi

# Enhanced Native Intelligence Section
log_section "🎯 Running Native Intelligence Analysis"

log_message "Running enhanced FinOps, Security, and AI/ML analysis..."

# Detect environment from tags or default to development
ENVIRONMENT="${ENVIRONMENT:-development}"

# Run enhanced scanner (Python)
if [ -f "/usr/local/bin/analyzers/enhanced_scanner.py" ]; then
    python3 /usr/local/bin/analyzers/enhanced_scanner.py terraform "$TARGET" --environment "$ENVIRONMENT" 2>&1 | tee -a "$OUTPUT_PATH"
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
log_message "Scan type: $SCAN_TYPE"
log_message "🕐 Scan completed: $(date)"

# Calculate overall status
TOTAL_ISSUES=0
OVERALL_STATUS="SUCCESS"

if [ $TFLINT_EXIT -ne 0 ]; then
    TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
    OVERALL_STATUS="ISSUES_FOUND"
fi

if [ $TFSEC_EXIT -ne 0 ]; then
    TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
    OVERALL_STATUS="ISSUES_FOUND"
fi

if [ $CHECKOV_EXIT -ne 0 ]; then
    TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
    OVERALL_STATUS="ISSUES_FOUND"
fi

# Final status
log_message "============================================================"
log_message "TOOL EXECUTION RESULTS:"
log_message "- TFLint: $([ $TFLINT_EXIT -eq 0 ] && echo "✅ PASSED" || echo "⚠️  ISSUES (exit $TFLINT_EXIT)")"
log_message "- TFSec: $([ $TFSEC_EXIT -eq 0 ] && echo "✅ PASSED" || echo "⚠️  ISSUES (exit $TFSEC_EXIT)")"
log_message "- Checkov: $([ $CHECKOV_EXIT -eq 0 ] && echo "✅ PASSED" || echo "⚠️  ISSUES (exit $CHECKOV_EXIT)")"
log_message "============================================================"

if [ "$OVERALL_STATUS" = "SUCCESS" ]; then
    log_success "Overall scan result: ALL TOOLS PASSED - No critical issues found!"
else
    log_warning "Overall scan result: ISSUES FOUND - Review the detailed output above"
    log_message "Tools with issues: $TOTAL_ISSUES out of 3"
fi

log_message "📄 Complete scan log saved to: terraform-scan-report-${TIMESTAMP}.log"
log_message "🎯 All tool outputs captured with timestamps and exit codes"

echo ""
echo "✅ Terraform scan completed! Report saved to: terraform-scan-report-${TIMESTAMP}.log"
echo "🎉 Terraform Scan Complete!"
echo "📄 Detailed log: terraform-scan-report-${TIMESTAMP}.log"
echo "🎯 Target: $TARGET ($SCAN_TYPE)"
echo "📊 Overall Status: $OVERALL_STATUS"
