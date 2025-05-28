@echo off
:: DevOps Universal Scanner - Windows Auto-mounting Wrapper
:: Automatically handles volume mounting - no manual setup required!
:: Usage: devops-scanner.bat scan-[type] [target]

setlocal enabledelayedexpansion

set CONTAINER_IMAGE=spd109/devops-uat:latest

:: Show help if no arguments
if "%~1"=="" goto :show_help
if "%~1"=="help" goto :show_help
if "%~1"=="-h" goto :show_help
if "%~1"=="--help" goto :show_help

:: Auto-detect current working directory
set WORK_DIR=%CD%

:: Display what we're doing
echo.
echo 🚀 DevOps Scanner - Auto-mounting wrapper
echo 📁 Mounting: %WORK_DIR% -^> /work
echo 🐳 Executing: docker run -it --rm -v "%WORK_DIR%:/work" %CONTAINER_IMAGE% %*
echo.

:: Execute Docker command with all arguments
docker run -it --rm -v "%WORK_DIR%:/work" %CONTAINER_IMAGE% %*
goto :eof

:show_help
echo.
echo 🚀 DevOps Universal Scanner - Auto-mounting Wrapper
echo.
echo Usage: devops-scanner.bat scan-[type] [target]
echo.
echo Commands:
echo   scan-terraform [dir]         - Scan Terraform configuration
echo   scan-cloudformation [file]   - Scan CloudFormation template
echo   scan-arm [file]             - Scan Azure ARM template
echo   scan-bicep [file]           - Scan Azure Bicep template
echo   scan-gcp [file]             - Scan GCP template
echo   scan-docker [image:tag]     - Scan Docker image
echo.
echo Examples:
echo   devops-scanner.bat scan-terraform terraform\
echo   devops-scanner.bat scan-cloudformation template.yaml
echo   devops-scanner.bat scan-docker nginx:latest
echo.
echo ✨ Features:
echo   • Automatic working directory detection
echo   • No manual volume mounts required!
echo   • Cross-platform support
echo.
goto :eof

docker version >nul 2>&1
if errorlevel 1 (
    echo [31mError: Docker is not running[0m
    echo Please start Docker and try again
    exit /b 1
)

:: Auto-detect working directory
set "WORK_DIR=%CD%"
:: Convert backslashes to forward slashes for Docker
set "WORK_DIR=%WORK_DIR:\=/%"
:: Convert C: to /c/ format
set "WORK_DIR=%WORK_DIR:C:=/c%"
set "WORK_DIR=%WORK_DIR:D:=/d%"
set "WORK_DIR=%WORK_DIR:E:=/e%"
set "WORK_DIR=%WORK_DIR:F:=/f%"
set "WORK_DIR=%WORK_DIR:G:=/g%"

:: Map commands to scanner scripts
if "%COMMAND%"=="terraform" set SCANNER_CMD=scan-terraform
if "%COMMAND%"=="tf" set SCANNER_CMD=scan-terraform
if "%COMMAND%"=="cloudformation" set SCANNER_CMD=scan-cloudformation
if "%COMMAND%"=="cf" set SCANNER_CMD=scan-cloudformation
if "%COMMAND%"=="cfn" set SCANNER_CMD=scan-cloudformation
if "%COMMAND%"=="bicep" set SCANNER_CMD=scan-azure-bicep
if "%COMMAND%"=="arm" set SCANNER_CMD=scan-azure-arm
if "%COMMAND%"=="gcp" set SCANNER_CMD=scan-gcp
if "%COMMAND%"=="docker" set SCANNER_CMD=scan-docker

if "%SCANNER_CMD%"=="" (
    echo [31mError: Unknown command '%COMMAND%'[0m
    echo.
    goto :show_help
)

:: Validate required targets
if "%COMMAND%"=="cloudformation" if "%TARGET%"=="" (
    echo [31mError: CloudFormation file required[0m
    echo Usage: devops-scanner.bat cloudformation template.yaml
    exit /b 1
)
if "%COMMAND%"=="cf" if "%TARGET%"=="" (
    echo [31mError: CloudFormation file required[0m
    echo Usage: devops-scanner.bat cf template.yaml
    exit /b 1
)
if "%COMMAND%"=="cfn" if "%TARGET%"=="" (
    echo [31mError: CloudFormation file required[0m
    echo Usage: devops-scanner.bat cfn template.yaml
    exit /b 1
)
if "%COMMAND%"=="bicep" if "%TARGET%"=="" (
    echo [31mError: Bicep file required[0m
    echo Usage: devops-scanner.bat bicep template.bicep
    exit /b 1
)
if "%COMMAND%"=="arm" if "%TARGET%"=="" (
    echo [31mError: ARM template file required[0m
    echo Usage: devops-scanner.bat arm template.json
    exit /b 1
)
if "%COMMAND%"=="gcp" if "%TARGET%"=="" (
    echo [31mError: GCP template file required[0m
    echo Usage: devops-scanner.bat gcp template.yaml
    exit /b 1
)
if "%COMMAND%"=="docker" if "%TARGET%"=="" (
    echo [31mError: Docker image required[0m
    echo Usage: devops-scanner.bat docker nginx:latest
    exit /b 1
)

:: Set default target for terraform
if "%COMMAND%"=="terraform" if "%TARGET%"=="" set TARGET=terraform
if "%COMMAND%"=="tf" if "%TARGET%"=="" set TARGET=terraform

:: Display scan information
echo.
echo [34mDevOps Universal Scanner v%SCANNER_VERSION%[0m
echo [32mCommand:[0m %COMMAND%
if not "%TARGET%"=="" echo [32mTarget:[0m %TARGET%
echo [32mWorking Directory:[0m %CD%
echo.

:: Build and execute Docker command
if "%TARGET%"=="" (
    set DOCKER_CMD=docker run --rm -v "%WORK_DIR%:/work" %CONTAINER_IMAGE% %SCANNER_CMD%
) else (
    set DOCKER_CMD=docker run --rm -v "%WORK_DIR%:/work" %CONTAINER_IMAGE% %SCANNER_CMD% %TARGET%
)

echo [33mExecuting:[0m !DOCKER_CMD!
echo.

:: Execute the scan
!DOCKER_CMD!
set SCAN_RESULT=%errorlevel%

echo.
if %SCAN_RESULT% equ 0 (
    echo [32mScan completed successfully![0m
    echo [34mReports saved in current directory[0m
    
    :: Try to format results using Python helper if available
    if exist "devops-scanner.py" (
        python --version >nul 2>&1
        if not errorlevel 1 (
            echo [34mProcessing results with Python helper...[0m
            python -c "import sys, os; sys.path.insert(0, os.path.join(os.getcwd(), 'helpers')); from result_processor import ResultProcessor; processor = ResultProcessor(); processor.process_scan_results('%COMMAND%', os.getcwd())" 2>nul
            if not errorlevel 1 echo [32mEnhanced report generated[0m
        )
    )
) else (
    echo [31mScan failed![0m
)

exit /b %SCAN_RESULT%

:show_help
echo.
echo [34mDevOps Universal Scanner v%SCANNER_VERSION%[0m
echo.
echo Simple infrastructure-as-code scanning with auto-detection!
echo.
echo [32mUsage:[0m
echo   devops-scanner.bat [command] [target]
echo.
echo [32mCommands:[0m
echo   terraform [dir]         - Scan Terraform configuration
echo   cloudformation [file]   - Scan CloudFormation template
echo   bicep [file]           - Scan Azure Bicep template
echo   arm [file]             - Scan Azure ARM template
echo   gcp [file]             - Scan GCP Deployment Manager template
echo   docker [image:tag]     - Scan Docker container image
echo.
echo [32mExamples:[0m
echo   devops-scanner.bat terraform ./terraform
echo   devops-scanner.bat cloudformation template.yaml
echo   devops-scanner.bat docker nginx:latest
echo.
echo [32mFeatures:[0m
echo   * Automatic working directory detection
echo   * No manual volume mounts required
echo   * Cross-platform support
echo   * Enhanced result processing
echo.
exit /b 0

:show_version
echo DevOps Universal Scanner v%SCANNER_VERSION%
exit /b 0
