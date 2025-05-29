# DevOps Universal Scanner - Quick Validation Test (PowerShell)
# This script tests all scanner capabilities with sample files

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "DevOps Universal Scanner - Validation Test" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is available
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker is available: $dockerVersion" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ ERROR: Docker is not installed or not running" -ForegroundColor Red
    Write-Host "Please install Docker Desktop and ensure it's running" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Pull the latest image
Write-Host "📥 Pulling latest scanner image..." -ForegroundColor Yellow
try {
    docker pull spd109/devops-uat:latest
    Write-Host "✅ Scanner image pulled successfully" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ ERROR: Failed to pull Docker image" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "🧪 Running validation tests..." -ForegroundColor Cyan
Write-Host ""

# Test Docker scanning (no volume mount needed)
Write-Host "🐳 Testing Docker scanner..." -ForegroundColor Blue
docker run -it --rm spd109/devops-uat:latest scan-docker nginx:latest
Write-Host ""

# Test Terraform scanner with sample files
Write-Host "🏗️ Testing Terraform scanner..." -ForegroundColor Blue
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-terraform test-files/terraform/
Write-Host ""

# Test CloudFormation scanner
Write-Host "☁️ Testing CloudFormation scanner..." -ForegroundColor Blue
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-cloudformation test-files/cloudformation/
Write-Host ""

# Test Azure ARM scanner
Write-Host "🔷 Testing Azure ARM scanner..." -ForegroundColor Blue
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-arm test-files/azure-arm/
Write-Host ""

# Test Azure Bicep scanner
Write-Host "💙 Testing Azure Bicep scanner..." -ForegroundColor Blue
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-bicep test-files/azure-bicep/
Write-Host ""

# Test GCP scanner
Write-Host "🌐 Testing GCP scanner..." -ForegroundColor Blue
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-gcp test-files/gcp-deployment-manager/
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🎉 Validation tests completed!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 Generated report files:" -ForegroundColor Yellow
Get-ChildItem -Name "*-scan-report.log" -ErrorAction SilentlyContinue
Write-Host ""

Write-Host "📋 Generated summary files:" -ForegroundColor Yellow
Get-ChildItem -Name "*-summary.txt" -ErrorAction SilentlyContinue
Write-Host ""

Read-Host "Press Enter to exit"
