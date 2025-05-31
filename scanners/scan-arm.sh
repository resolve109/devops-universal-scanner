#!/bin/bash
# Enhanced Azure ARM Scanner with Comprehensive Logging
# Usage: scan-arm template.json

set +e  # Handle errors gracefully

# Working directory setup
cd /work

TARGET="$1"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
OUTPUT_PATH="/work/azure-arm-scan-report-${TIMESTAMP}.log"

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
    echo "❌ Usage: scan-arm <template.json>"
    echo "   Examples:"
    echo "     scan-arm template.json"
    echo "     scan-arm azure-resources.json"
    exit 1
fi

# Remove /work/ prefix if provided
TARGET=$(echo "$TARGET" | sed 's|^/work/||')

# Initialize log file with header
echo "=================================================================" > "$OUTPUT_PATH"
echo "              AZURE ARM TEMPLATE SECURITY SCAN REPORT" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "Target: $TARGET" >> "$OUTPUT_PATH"
echo "Scan Started: $(date)" >> "$OUTPUT_PATH"
echo "Scanner: Checkov + ARM-TTK" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"

log_section "AZURE ARM TEMPLATE SCAN STARTING"
log_message "Scanning Azure ARM template: $TARGET"

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
log_message "Analyzing ARM template structure..."
echo "" >> "$OUTPUT_PATH"
echo "File: $TARGET" >> "$OUTPUT_PATH"
echo "Size: $(stat -c%s "$TARGET" 2>/dev/null || echo "unknown") bytes" >> "$OUTPUT_PATH"
echo "Type: $(file "$TARGET" | cut -d: -f2)" >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"

# Validate JSON structure
if jq empty "$TARGET" 2>/dev/null; then
    log_success "Valid JSON structure"
    echo "" >> "$OUTPUT_PATH"
    echo "--- ARM Template Schema Info ---" >> "$OUTPUT_PATH"
    jq -r '."\$schema" // "No schema found"' "$TARGET" >> "$OUTPUT_PATH"
    echo "Content Version: $(jq -r '.contentVersion // "No version found"' "$TARGET")" >> "$OUTPUT_PATH"
    echo "Parameters: $(jq -r '.parameters | keys | length' "$TARGET" 2>/dev/null || echo "0")" >> "$OUTPUT_PATH"
    echo "Variables: $(jq -r '.variables | keys | length' "$TARGET" 2>/dev/null || echo "0")" >> "$OUTPUT_PATH"
    echo "Resources: $(jq -r '.resources | length' "$TARGET" 2>/dev/null || echo "0")" >> "$OUTPUT_PATH"
    echo "--- End Schema Info ---" >> "$OUTPUT_PATH"
    echo "" >> "$OUTPUT_PATH"
else
    log_error "Invalid JSON structure in ARM template"
fi

# Checkov Security Scan
log_section "CHECKOV SECURITY SCAN"
log_message "Running Checkov security analysis on ARM template..."
echo "" >> "$OUTPUT_PATH"

if command -v checkov &> /dev/null; then
    log_success "Checkov found, starting scan..."
    echo "" >> "$OUTPUT_PATH"
    
    # Run Checkov with ARM framework
    if checkov -f "$TARGET" --framework arm 2>&1 | tee -a "$OUTPUT_PATH"; then
        log_success "Checkov scan completed"
    else
        log_warning "Checkov scan completed with issues"
    fi
else
    log_error "Checkov not found in container"
fi

# ARM-TTK Validation
log_section "ARM-TTK VALIDATION"
log_message "Running Azure Resource Manager Template Toolkit (ARM-TTK)..."
echo "" >> "$OUTPUT_PATH"

if [ -f "/opt/arm-ttk/arm-ttk.sh" ]; then
    log_success "ARM-TTK found, starting validation..."
    echo "" >> "$OUTPUT_PATH"
    
    # Create temp directory for ARM-TTK
    TEMP_DIR=$(mktemp -d)
    cp "$TARGET" "$TEMP_DIR/"
    
    if /opt/arm-ttk/arm-ttk.sh -TemplatePath "$TEMP_DIR" 2>&1 | tee -a "$OUTPUT_PATH"; then
        log_success "ARM-TTK validation completed"
    else
        log_warning "ARM-TTK validation found issues"
    fi
    
    # Clean up
    rm -rf "$TEMP_DIR"
else
    log_warning "ARM-TTK not found in container"
fi

# Additional Security Checks
log_section "ADDITIONAL SECURITY ANALYSIS"
log_message "Performing additional ARM template security checks..."
echo "" >> "$OUTPUT_PATH"

echo "--- Checking for hardcoded secrets ---" >> "$OUTPUT_PATH"
if grep -i "password\|secret\|key\|token" "$TARGET" | grep -v "parameters\|variables" >> "$OUTPUT_PATH" 2>&1; then
    log_warning "Found potential hardcoded secrets in template"
else
    log_success "No obvious hardcoded secrets found"
fi

echo "" >> "$OUTPUT_PATH"
echo "--- Checking for public access configurations ---" >> "$OUTPUT_PATH"
if grep -i "0\.0\.0\.0\|\*\|publicAccess\|allowBlobPublicAccess" "$TARGET" >> "$OUTPUT_PATH" 2>&1; then
    log_warning "Found potential public access configurations"
else
    log_success "No obvious public access configurations found"
fi

echo "" >> "$OUTPUT_PATH"
echo "--- Checking for storage account security ---" >> "$OUTPUT_PATH"
if grep -i "Microsoft\.Storage/storageAccounts" "$TARGET" >> "$OUTPUT_PATH" 2>&1; then
    log_message "Storage accounts found - checking security settings..."
    if grep -i "supportsHttpsTrafficOnly.*false\|minimumTlsVersion.*TLS1_0" "$TARGET" >> "$OUTPUT_PATH" 2>&1; then
        log_warning "Storage account security issues found"
    else
        log_success "Storage account security settings appear secure"
    fi
fi

log_section "AZURE ARM SCAN SUMMARY"
log_message "Scan completed for: $TARGET"
log_message "Full report saved to: $OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "                    SCAN COMPLETED" >> "$OUTPUT_PATH"
echo "              $(date)" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"

echo "✅ Azure ARM scan completed! Report saved to: azure-arm-scan-report-${TIMESTAMP}.log"
