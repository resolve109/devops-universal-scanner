#!/bin/bash
# Simple Docker container image scanner script
# Usage: scan-docker nginx:latest
# Usage: scan-docker myapp:1.0.0

# Don't exit on errors, handle them gracefully  
set +e

TARGET="$1"

if [ -z "$TARGET" ]; then
    echo "Usage: scan-docker [image-name:tag]"
    echo "Examples:"
    echo "  scan-docker nginx:latest"
    echo "  scan-docker ubuntu:22.04"
    echo "  scan-docker myapp:1.0.0"
    exit 1
fi

echo "===== Scanning Docker Image: $TARGET ====="

# Check if Docker is available (for local scanning)
if command -v docker &> /dev/null; then
    echo "Docker CLI detected - checking if image exists locally..."
    if docker image inspect "$TARGET" &> /dev/null; then
        echo "✓ Image found locally"
    else
        echo "⚠ Image not found locally - Trivy will attempt to pull from registry"
    fi
else
    echo "Docker CLI not available - Trivy will attempt to pull from registry"
fi

echo ""
echo "===== Running Trivy Vulnerability Scan ====="
echo "Scanning for vulnerabilities, secrets, and misconfigurations..."
trivy image --severity HIGH,CRITICAL --format table "$TARGET" || echo "Trivy vulnerability scan completed with warnings"

echo ""
echo "===== Running Trivy Secret Detection ====="
trivy image --scanners secret --format table "$TARGET" || echo "Trivy secret scan completed with warnings"

echo ""
echo "===== Running Trivy Configuration Scan ====="
trivy image --scanners config --format table "$TARGET" || echo "Trivy config scan completed with warnings"

echo ""
echo "===== Running Comprehensive Trivy Scan ====="
echo "Full scan with all available scanners..."

# Determine output path - use /work if mounted, otherwise current directory
if [ -d "/work" ] && [ -w "/work" ]; then
    OUTPUT_PATH="/work/trivy-report.json"
    echo "✓ Saving report to mounted volume: /work/trivy-report.json"
else
    OUTPUT_PATH="trivy-report.json"
    echo "✓ Saving report to: trivy-report.json"
fi

trivy image --format json --output "$OUTPUT_PATH" "$TARGET" 2>/dev/null || echo "Full scan completed with warnings"

if [ -f "$OUTPUT_PATH" ]; then
    echo "✓ Detailed JSON report saved as $OUTPUT_PATH"
    
    # Extract summary information
    vulnerabilities=$(jq -r '.Results[]?.Vulnerabilities | length' "$OUTPUT_PATH" 2>/dev/null | awk '{sum += $1} END {print sum+0}')
    secrets=$(jq -r '.Results[]?.Secrets | length' "$OUTPUT_PATH" 2>/dev/null | awk '{sum += $1} END {print sum+0}')
    misconfigs=$(jq -r '.Results[]?.Misconfigurations | length' "$OUTPUT_PATH" 2>/dev/null | awk '{sum += $1} END {print sum+0}')
    
    echo ""
    echo "===== Scan Summary ====="
    echo "Vulnerabilities found: $vulnerabilities"
    echo "Secrets found: $secrets" 
    echo "Misconfigurations found: $misconfigs"
    
    # Show critical/high vulnerabilities count
    critical=$(jq -r '.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL") | .VulnerabilityID' "$OUTPUT_PATH" 2>/dev/null | wc -l)
    high=$(jq -r '.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH") | .VulnerabilityID' "$OUTPUT_PATH" 2>/dev/null | wc -l)
    
    echo "Critical vulnerabilities: $critical"
    echo "High vulnerabilities: $high"
    
    if [ "$critical" -gt 0 ] || [ "$high" -gt 0 ]; then
        echo ""
        echo "⚠ WARNING: Critical or High severity vulnerabilities found!"
        echo "Review the detailed report in $OUTPUT_PATH"
    fi
else
    echo "⚠ Could not generate detailed report"
fi

echo ""
echo "===== Scan Complete ====="
echo "Image: $TARGET"
echo "Tools used: Trivy (vulnerability, secret, and configuration scanning)"
