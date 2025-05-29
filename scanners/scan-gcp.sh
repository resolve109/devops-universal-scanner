#!/bin/bash
# Enhanced GCP Scanner with Comprehensive Logging
# Usage: scan-gcp template.yaml

set +e  # Handle errors gracefully

# Working directory setup
cd /work

TARGET="$1"
OUTPUT_PATH="/work/gcp-scan-report.log"

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
    echo "❌ Usage: scan-gcp <template.yaml|template.jinja>"
    echo "   Examples:"
    echo "     scan-gcp deployment.yaml"
    echo "     scan-gcp vm-template.jinja"
    exit 1
fi

# Remove /work/ prefix if provided
TARGET=$(echo "$TARGET" | sed 's|^/work/||')

# Initialize log file with header
echo "=================================================================" > "$OUTPUT_PATH"
echo "              GCP DEPLOYMENT SECURITY SCAN REPORT" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "Target: $TARGET" >> "$OUTPUT_PATH"
echo "Scan Started: $(date)" >> "$OUTPUT_PATH"
echo "Scanner: Checkov + GCloud validation" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"

log_section "GCP DEPLOYMENT SCAN STARTING"
log_message "Scanning GCP deployment template: $TARGET"

# Check if target exists
if [ ! -f "$TARGET" ]; then
    log_error "Target file not found: $TARGET"
    log_message "Available files in current directory:"
    ls -la | tee -a "$OUTPUT_PATH"
    exit 1
fi

log_success "Target file found: $TARGET"

# File analysis
log_section "FILE ANALYSIS"
log_message "Analyzing file type and content..."
echo "" >> "$OUTPUT_PATH"
echo "File: $TARGET" >> "$OUTPUT_PATH"
echo "Size: $(stat -c%s "$TARGET" 2>/dev/null || echo "unknown") bytes" >> "$OUTPUT_PATH"
echo "Type: $(file "$TARGET" | cut -d: -f2)" >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"
echo "--- File Preview (first 20 lines) ---" >> "$OUTPUT_PATH"
head -20 "$TARGET" >> "$OUTPUT_PATH"
echo "--- End Preview ---" >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"

# Checkov Security Scan
log_section "CHECKOV SECURITY SCAN"
log_message "Running Checkov security analysis on GCP template..."
echo "" >> "$OUTPUT_PATH"

if command -v checkov &> /dev/null; then
    log_success "Checkov found, starting scan..."
    echo "" >> "$OUTPUT_PATH"
    
    # Run Checkov with comprehensive output
    if checkov -f "$TARGET" --framework gcp 2>&1 | tee -a "$OUTPUT_PATH"; then
        log_success "Checkov scan completed"
    else
        log_warning "Checkov scan completed with issues"
    fi
else
    log_error "Checkov not found in container"
fi

# GCloud Validation (if available)
log_section "GCLOUD DEPLOYMENT VALIDATION"
log_message "Attempting GCloud deployment validation..."
echo "" >> "$OUTPUT_PATH"

if command -v python &> /dev/null && python -c "import google.cloud.deployment_manager" &> /dev/null; then
    log_success "Google Cloud Deployment Manager module found"
    
    # Check if it's a Deployment Manager template
    if [[ "$TARGET" == *.yaml ]] || [[ "$TARGET" == *.yml ]]; then
        log_message "Validating Deployment Manager template structure..."
        echo "" >> "$OUTPUT_PATH"
        
        # Simplified validation - check for required sections
        if grep -q "resources:" "$TARGET"; then
            log_success "Template contains resources section"
            cat "$TARGET" | grep -A20 "resources:" | tee -a "$OUTPUT_PATH"
        else
            log_warning "Template missing resources section"
        fi
    else
        log_warning "File type not suitable for deployment validation"
    fi
else
    log_warning "Google Cloud Deployment Manager module not available for validation"
fi

# Additional Security Checks
log_section "ADDITIONAL SECURITY ANALYSIS"
log_message "Performing additional security checks..."
echo "" >> "$OUTPUT_PATH"

# Check for common security issues
log_message "Checking for common GCP security issues:"
echo "" >> "$OUTPUT_PATH"

echo "--- Checking for public access configurations ---" >> "$OUTPUT_PATH"
if grep -i "allUsers\|allAuthenticatedUsers" "$TARGET" >> "$OUTPUT_PATH" 2>&1; then
    log_warning "Found potential public access configurations"
else
    log_success "No obvious public access configurations found"
fi

echo "" >> "$OUTPUT_PATH"
echo "--- Checking for default service accounts ---" >> "$OUTPUT_PATH"
if grep -i "default.*service.*account" "$TARGET" >> "$OUTPUT_PATH" 2>&1; then
    log_warning "Found references to default service accounts"
else
    log_success "No default service account references found"
fi

echo "" >> "$OUTPUT_PATH"
echo "--- Checking for firewall rules ---" >> "$OUTPUT_PATH"
if grep -i "firewall\|0\.0\.0\.0" "$TARGET" >> "$OUTPUT_PATH" 2>&1; then
    log_warning "Found firewall rules - review for overly permissive access"
else
    log_success "No obvious firewall configuration issues found"
fi

log_section "GCP SCAN SUMMARY"
log_message "Scan completed for: $TARGET"
log_message "Full report saved to: $OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "                    SCAN COMPLETED" >> "$OUTPUT_PATH"
echo "              $(date)" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"

echo "✅ GCP scan completed! Report saved to: gcp-scan-report.log"