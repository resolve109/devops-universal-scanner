#!/bin/bash
# Enhanced Azure Bicep Scanner with Comprehensive Logging
# Usage: scan-bicep template.bicep

set +e  # Handle errors gracefully

# Working directory setup
cd /work

TARGET="$1"
OUTPUT_PATH="/work/azure-bicep-scan-report.log"

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
    echo "❌ Usage: scan-bicep <template.bicep>"
    echo "   Examples:"
    echo "     scan-bicep main.bicep"
    echo "     scan-bicep storage-account.bicep"
    exit 1
fi

# Remove /work/ prefix if provided
TARGET=$(echo "$TARGET" | sed 's|^/work/||')

# Initialize log file with header
echo "=================================================================" > "$OUTPUT_PATH"
echo "              AZURE BICEP TEMPLATE SECURITY SCAN REPORT" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "Target: $TARGET" >> "$OUTPUT_PATH"
echo "Scan Started: $(date)" >> "$OUTPUT_PATH"
echo "Scanner: Bicep CLI + Checkov" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"

log_section "AZURE BICEP TEMPLATE SCAN STARTING"
log_message "Scanning Azure Bicep template: $TARGET"

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
log_message "Analyzing Bicep template structure..."
echo "" >> "$OUTPUT_PATH"
echo "File: $TARGET" >> "$OUTPUT_PATH"
echo "Size: $(stat -c%s "$TARGET" 2>/dev/null || echo "unknown") bytes" >> "$OUTPUT_PATH"
echo "Type: $(file "$TARGET" | cut -d: -f2)" >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"
echo "--- Bicep Template Preview (first 30 lines) ---" >> "$OUTPUT_PATH"
head -30 "$TARGET" >> "$OUTPUT_PATH"
echo "--- End Preview ---" >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"

# Bicep CLI Validation
log_section "BICEP CLI VALIDATION"
log_message "Running Bicep CLI build and validation..."
echo "" >> "$OUTPUT_PATH"

if command -v bicep &> /dev/null; then
    log_success "Bicep CLI found, starting validation..."
    echo "" >> "$OUTPUT_PATH"
    
    # Bicep build (compile to ARM)
    log_message "Compiling Bicep to ARM template..."
    if bicep build "$TARGET" 2>&1 | tee -a "$OUTPUT_PATH"; then
        log_success "Bicep compilation successful"
        
        # Check if ARM file was generated
        ARM_FILE="${TARGET%.bicep}.json"
        if [ -f "$ARM_FILE" ]; then
            log_success "ARM template generated: $ARM_FILE"
        fi
    else
        log_error "Bicep compilation failed"
    fi
else
    log_error "Bicep CLI not found in container"
fi

# Checkov Security Scan
log_section "CHECKOV SECURITY SCAN"
log_message "Running Checkov security analysis on Bicep template..."
echo "" >> "$OUTPUT_PATH"

if command -v checkov &> /dev/null; then
    log_success "Checkov found, starting scan..."
    echo "" >> "$OUTPUT_PATH"
    
    # Run Checkov with Bicep/ARM framework
    if checkov -f "$TARGET" --framework bicep 2>&1 | tee -a "$OUTPUT_PATH"; then
        log_success "Checkov Bicep scan completed"
    else
        log_warning "Checkov Bicep scan completed with issues"
    fi
    
    # If ARM file exists, also scan it
    ARM_FILE="${TARGET%.bicep}.json"
    if [ -f "$ARM_FILE" ]; then
        log_message "Also scanning generated ARM template..."
        echo "" >> "$OUTPUT_PATH"
        if checkov -f "$ARM_FILE" --framework arm 2>&1 | tee -a "$OUTPUT_PATH"; then
            log_success "Checkov ARM scan completed"
        else
            log_warning "Checkov ARM scan completed with issues"
        fi
    fi
else
    log_error "Checkov not found in container"
fi

# Additional Security Checks
log_section "ADDITIONAL SECURITY ANALYSIS"
log_message "Performing additional Bicep template security checks..."
echo "" >> "$OUTPUT_PATH"

echo "--- Checking for hardcoded values ---" >> "$OUTPUT_PATH"
if grep -n "password\|secret\|key" "$TARGET" | grep -v "@secure\|param" >> "$OUTPUT_PATH" 2>&1; then
    log_warning "Found potential hardcoded secrets (should use @secure parameters)"
else
    log_success "No obvious hardcoded secrets found"
fi

echo "" >> "$OUTPUT_PATH"
echo "--- Checking for @secure parameter usage ---" >> "$OUTPUT_PATH"
if grep -n "@secure" "$TARGET" >> "$OUTPUT_PATH" 2>&1; then
    log_success "Found secure parameters - good practice"
else
    log_warning "No @secure parameters found - consider for sensitive values"
fi

echo "" >> "$OUTPUT_PATH"
echo "--- Checking for public access configurations ---" >> "$OUTPUT_PATH"
if grep -i "publicAccess\|allowBlobPublicAccess\|publicNetworkAccess" "$TARGET" >> "$OUTPUT_PATH" 2>&1; then
    log_warning "Found public access configurations - review settings"
else
    log_success "No obvious public access configurations found"
fi

echo "" >> "$OUTPUT_PATH"
echo "--- Checking for resource naming and tagging ---" >> "$OUTPUT_PATH"
if grep -n "tags:" "$TARGET" >> "$OUTPUT_PATH" 2>&1; then
    log_success "Found resource tagging - good practice"
else
    log_warning "No resource tags found - consider adding for governance"
fi

echo "" >> "$OUTPUT_PATH"
echo "--- Checking for outputs with sensitive data ---" >> "$OUTPUT_PATH"
if grep -A5 "output.*password\|output.*secret\|output.*key" "$TARGET" >> "$OUTPUT_PATH" 2>&1; then
    log_warning "Found outputs that may contain sensitive data"
else
    log_success "No obvious sensitive data in outputs"
fi

log_section "AZURE BICEP SCAN SUMMARY"
log_message "Scan completed for: $TARGET"
ARM_FILE="${TARGET%.bicep}.json"
if [ -f "$ARM_FILE" ]; then
    log_message "Generated ARM template: $ARM_FILE"
fi
log_message "Full report saved to: $OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "                    SCAN COMPLETED" >> "$OUTPUT_PATH"
echo "              $(date)" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"

echo "✅ Azure Bicep scan completed! Report saved to: azure-bicep-scan-report.log"