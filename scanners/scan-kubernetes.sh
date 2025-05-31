#!/bin/bash
# Enhanced Kubernetes Scanner with Comprehensive Logging
# Usage: scan-kubernetes <file_or_directory>

set +e  # Handle errors gracefully

cd /work

TARGET="$1"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
OUTPUT_PATH="/work/kubernetes-scan-report-${TIMESTAMP}.log"

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

if [ -z "$TARGET" ]; then
    echo "❌ Usage: scan-kubernetes <file_or_directory>"
    echo "   Examples:"
    echo "     scan-kubernetes deployment.yaml"
    echo "     scan-kubernetes manifests/"
    exit 1
fi

TARGET=$(echo "$TARGET" | sed 's|^/work/||')

echo "=================================================================" > "$OUTPUT_PATH"
echo "        KUBERNETES MANIFEST SECURITY SCAN REPORT" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "Target: $TARGET" >> "$OUTPUT_PATH"
echo "Scan Started: $(date)" >> "$OUTPUT_PATH"
echo "Scanners: kube-score + kubescape" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"

log_section "KUBE-SCORE ANALYSIS"
FILES="$TARGET"
if [ -d "$TARGET" ]; then
    FILES=$(find "$TARGET" -name '*.yaml' -o -name '*.yml' 2>/dev/null)
fi

if command -v kube-score >/dev/null 2>&1; then
    log_message "Running kube-score analysis..."
    kube-score score $FILES 2>&1 | tee -a "$OUTPUT_PATH"
    KUBESCORE_EXIT=${PIPESTATUS[0]}
    if [ $KUBESCORE_EXIT -eq 0 ]; then
        log_success "kube-score analysis completed"
    else
        log_warning "kube-score completed with issues (exit code: $KUBESCORE_EXIT)"
    fi
else
    log_error "kube-score not found in container"
fi

log_section "KUBESCAPE SECURITY SCAN"
if command -v kubescape >/dev/null 2>&1; then
    log_message "Running kubescape scan..."
    kubescape scan "$TARGET" 2>&1 | tee -a "$OUTPUT_PATH"
    KUBESCAPE_EXIT=${PIPESTATUS[0]}
    if [ $KUBESCAPE_EXIT -eq 0 ]; then
        log_success "kubescape scan completed"
    else
        log_warning "kubescape scan completed with issues (exit code: $KUBESCAPE_EXIT)"
    fi
else
    log_error "kubescape not found in container"
fi

log_section "SCAN COMPLETE"
log_message "Scan finished: $(date)"

echo "" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"
echo "                    SCAN COMPLETED" >> "$OUTPUT_PATH"
echo "              $(date)" >> "$OUTPUT_PATH"
echo "=================================================================" >> "$OUTPUT_PATH"

echo "✅ Kubernetes scan completed! Report saved to: kubernetes-scan-report-${TIMESTAMP}.log"
