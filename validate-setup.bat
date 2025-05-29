@echo off
REM DevOps Universal Scanner - Quick Validation Test
REM This script tests all scanner capabilities with sample files

echo ============================================================
echo DevOps Universal Scanner - Validation Test
echo ============================================================
echo.

REM Check if Docker is available
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Docker is not installed or not running
    echo Please install Docker Desktop and ensure it's running
    pause
    exit /b 1
)

echo ✅ Docker is available
echo.

REM Pull the latest image
echo 📥 Pulling latest scanner image...
docker pull spd109/devops-uat:latest

if %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Failed to pull Docker image
    pause
    exit /b 1
)

echo ✅ Scanner image pulled successfully
echo.

echo 🧪 Running validation tests...
echo.

REM Test Docker scanning (no volume mount needed)
echo 🐳 Testing Docker scanner...
docker run -it --rm spd109/devops-uat:latest scan-docker nginx:latest
echo.

REM Test Terraform scanner with sample files
echo 🏗️ Testing Terraform scanner...
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-terraform test-files/terraform/
echo.

REM Test CloudFormation scanner
echo ☁️ Testing CloudFormation scanner...
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-cloudformation test-files/cloudformation/
echo.

REM Test Azure ARM scanner
echo 🔷 Testing Azure ARM scanner...
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-arm test-files/azure-arm/
echo.

REM Test Azure Bicep scanner
echo 💙 Testing Azure Bicep scanner...
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-bicep test-files/azure-bicep/
echo.

REM Test GCP scanner
echo 🌐 Testing GCP scanner...
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-gcp test-files/gcp-deployment-manager/
echo.

echo ============================================================
echo 🎉 Validation tests completed!
echo ============================================================
echo.
echo Check the generated report files:
dir *-scan-report.log /B 2>nul
echo.
echo Check the generated summary files:
dir *-summary.txt /B 2>nul
echo.
pause
