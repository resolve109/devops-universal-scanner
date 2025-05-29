@echo off
echo Building DevOps Universal Scanner...

:: Set your Docker Hub username
set DOCKER_USERNAME=spd109

:: Build the image
echo Building Docker image...
docker build -t %DOCKER_USERNAME%/devops-uat:latest .

IF %ERRORLEVEL% NEQ 0 (
    echo Build failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Build completed successfully!

:: Test the image with basic commands
echo.
echo === Testing all scanners and tools ===
echo.

echo Testing Terraform scanner...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest scan-terraform --help

echo Testing Checkov scanner...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest checkov --version

echo Testing TFLint...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest tflint --version

echo Testing TFSec...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest tfsec --version

echo Testing Trivy scanner...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest trivy --version

echo Testing CloudFormation Linter...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest cfn-lint --version

echo Testing Azure Bicep CLI...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest bicep --version

echo Testing Google Cloud libraries...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest python -c "import google.cloud.storage; print('Google Cloud libraries imported successfully')"

echo.
echo === Testing scanner commands ===
echo.

echo Testing scan-docker command...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest scan-docker --help

echo Testing scan-terraform command...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest scan-terraform --help

echo Testing scan-cloudformation command...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest scan-cloudformation --help

echo Testing scan-azure-arm command...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest scan-azure-arm --help

echo Testing scan-azure-bicep command...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest scan-azure-bicep --help

echo Testing scan-gcp command...
docker run --rm %DOCKER_USERNAME%/devops-uat:latest scan-gcp --help

echo.
echo === Testing with sample files ===
echo.

echo Testing scan-terraform with sample files...
docker run --rm -v "%cd%\test-files:/work" %DOCKER_USERNAME%/devops-uat:latest scan-terraform /work/terraform

echo All tests completed. Image is ready to push.
echo To push to Docker Hub, run: docker push %DOCKER_USERNAME%/devops-uat:latest
