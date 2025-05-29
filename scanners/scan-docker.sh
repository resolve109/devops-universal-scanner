#!/bin/bash
# Enhanced Docker Scanner with Comprehensive Logging
# Usage: scan-docker nginx:latest

set +e  # Handle errors gracefully

# Working directory setup
cd /work

TARGET="$1"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
OUTPUT_PATH="/work/docker-scan-report-${TIMESTAMP}.log"

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
    echo "❌ Usage: scan-docker <image:tag>"
    echo "   Examples:"
    echo "     scan-docker nginx:latest"
    echo "     scan-docker ubuntu:22.04"
    echo "     scan-docker myapp:1.0.0"
    exit 1
fi

# Initialize log file with header
echo "=================================================================" > "$OUTPUT_PATH"
echo "              DOCKER IMAGE SECURITY SCAN REPORT" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "Target: $TARGET" >> "$OUTPUT_PATH"
echo "Scan Started: $(date)" >> "$OUTPUT_PATH"
echo "Scanner: Trivy (Multi-purpose vulnerability scanner)" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"

log_section "DOCKER IMAGE SCAN STARTING"
log_message "Scanning Docker image: $TARGET"

# Check if Docker is available
log_section "DOCKER ENVIRONMENT CHECK"
if command -v docker &> /dev/null; then
    log_success "Docker CLI detected"
    if docker image inspect "$TARGET" &> /dev/null; then
        log_success "Image found locally: $TARGET"
    else
        log_warning "Image not found locally - Trivy will pull from registry: $TARGET"
    fi
else
    log_warning "Docker CLI not available - Trivy will pull from registry"
fi

# Vulnerability Scan
log_section "TRIVY VULNERABILITY SCAN (HIGH & CRITICAL)"
log_message "Scanning for HIGH and CRITICAL vulnerabilities..."
echo "" >> "$OUTPUT_PATH"
if trivy image --severity HIGH,CRITICAL --format table "$TARGET" 2>&1 | tee -a "$OUTPUT_PATH"; then
    log_success "Vulnerability scan completed"
else
    log_warning "Vulnerability scan completed with warnings"
fi

# Secret Detection
log_section "TRIVY SECRET DETECTION"
log_message "Scanning for exposed secrets and sensitive data..."
echo "" >> "$OUTPUT_PATH"
if trivy image --scanners secret --format table "$TARGET" 2>&1 | tee -a "$OUTPUT_PATH"; then
    log_success "Secret detection scan completed"
else
    log_warning "Secret detection scan completed with warnings"
fi

# Configuration Scan
log_section "TRIVY CONFIGURATION SCAN"
log_message "Scanning for misconfigurations..."
echo "" >> "$OUTPUT_PATH"
if trivy image --scanners config --format table "$TARGET" 2>&1 | tee -a "$OUTPUT_PATH"; then
    log_success "Configuration scan completed"
else
    log_warning "Configuration scan completed with warnings"
fi

# Comprehensive JSON Report
log_section "COMPREHENSIVE TRIVY SCAN (JSON OUTPUT)"
log_message "Generating detailed JSON report..."
echo "" >> "$OUTPUT_PATH"
if trivy image --format json "$TARGET" 2>&1 | tee -a "$OUTPUT_PATH"; then
    log_success "Comprehensive scan completed"
else
    log_warning "Comprehensive scan completed with warnings"
fi

log_section "DOCKER SCAN SUMMARY"
log_message "Scan completed for image: $TARGET"
log_message "Full report saved to: $OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "                    SCAN COMPLETED" >> "$OUTPUT_PATH"
echo "              $(date)" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"

echo "✅ Docker scan completed! Report saved to: docker-scan-report-${TIMESTAMP}.log"