#!/bin/bash
# DevOps Universal Scanner - Quick Validation Test
# This script tests all scanner capabilities with sample files

echo "============================================================"
echo "DevOps Universal Scanner - Validation Test"
echo "============================================================"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker is not installed or not running"
    echo "Please install Docker and ensure it's running"
    read -p "Press Enter to exit"
    exit 1
fi

echo "✅ Docker is available: $(docker --version)"
echo ""

# Pull the latest image
echo "📥 Pulling latest scanner image..."
if ! docker pull spd109/devops-uat:latest; then
    echo "❌ ERROR: Failed to pull Docker image"
    read -p "Press Enter to exit"
    exit 1
fi

echo "✅ Scanner image pulled successfully"
echo ""

echo "🧪 Running validation tests..."
echo ""

# Test Docker scanning (no volume mount needed)
echo "🐳 Testing Docker scanner..."
docker run -it --rm spd109/devops-uat:latest scan-docker nginx:latest
echo ""

# Test Terraform scanner with sample files
echo "🏗️ Testing Terraform scanner..."
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform test-files/terraform/
echo ""

# Test CloudFormation scanner
echo "☁️ Testing CloudFormation scanner..."
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-cloudformation test-files/cloudformation/
echo ""

# Test Azure ARM scanner
echo "🔷 Testing Azure ARM scanner..."
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-arm test-files/azure-arm/
echo ""

# Test Azure Bicep scanner
echo "💙 Testing Azure Bicep scanner..."
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-bicep test-files/azure-bicep/
echo ""

# Test GCP scanner
echo "🌐 Testing GCP scanner..."
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-gcp test-files/gcp-deployment-manager/
echo ""

echo "============================================================"
echo "🎉 Validation tests completed!"
echo "============================================================"
echo ""

echo "📊 Generated report files:"
ls -la *-scan-report.log 2>/dev/null || echo "No report files found"
echo ""

echo "📋 Generated summary files:"
ls -la *-summary.txt 2>/dev/null || echo "No summary files found"
echo ""

read -p "Press Enter to exit"
