# DevOps Universal Scanner

**🚀 Zero Configuration DevOps Security Scanner with Auto-Mounting**

A comprehensive Docker-based security scanner that **automatically handles all volume mounting** - no more complex Docker commands!

## What Makes This Different

✅ **Auto-detects your working directory** - no manual volume mounts  
✅ **One simple command structure** for all scan types  
✅ **Comprehensive LOG format** with full terminal output capture  
✅ **Cross-platform** Python orchestrator for Windows/macOS/Linux  

**Before:** `docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-terraform terraform/`  
**Now:** `python devops-scanner.py scan-terraform terraform/`

## Scanner Commands Available

All commands generate detailed `.log` files with full terminal output:

| Command | Purpose | Tools Used |
|---------|---------|------------|
| `scan-terraform` | Terraform configurations | TFLint, TFSec, Checkov |
| `scan-cloudformation` | CloudFormation templates | CFN-Lint, Checkov |
| `scan-docker` | Container images | Trivy (vulnerabilities, secrets, misconfigurations) |
| `scan-arm` | Azure ARM templates | ARM-TTK, Checkov |
| `scan-bicep` | Azure Bicep templates | Bicep CLI, Checkov |
| `scan-gcp` | GCP Deployment Manager | Checkov, GCloud validation |

## Quick Start

### 1. Get the Scanner

```bash
# Pull the Docker image
docker pull spd109/devops-uat:latest

# Clone this repo for the Python wrapper (recommended)
git clone <this-repo>
cd devops-universal-scanner
```

### 2. Use the Auto-Mounting Commands

**🎯 Recommended: Python Wrapper (Cross-Platform)**

```bash
# Scan Terraform configurations  
python devops-scanner.py scan-terraform terraform/

# Scan CloudFormation templates
python devops-scanner.py scan-cloudformation template.yaml

# Scan container images for vulnerabilities
python devops-scanner.py scan-docker nginx:latest

# Scan Azure ARM templates
python devops-scanner.py scan-arm template.json

# Scan Azure Bicep templates  
python devops-scanner.py scan-bicep template.bicep

# Scan GCP templates
python devops-scanner.py scan-gcp template.yaml
```

**🐚 Alternative: Shell Wrapper (Linux/macOS)**

```bash
./devops-scanner scan-terraform terraform/
./devops-scanner scan-cloudformation template.yaml
./devops-scanner scan-docker nginx:latest
```

**💻 Alternative: Batch Wrapper (Windows)**

```cmd
devops-scanner.bat scan-terraform terraform\
devops-scanner.bat scan-cloudformation template.yaml
devops-scanner.bat scan-docker nginx:latest
```

## Output Files Generated

Each scan creates two files:

1. **Detailed Log File** (`*-scan-report.log`) - Full terminal output with timestamps
2. **Summary Report** (`*-summary.txt`) - Human-readable findings overview

### Example Log Output

```log
=================================================================
              DOCKER SECURITY SCAN REPORT  
=================================================================
Target: nginx:latest
Scan Started: Thu Dec 26 15:30:45 UTC 2024
Scanner: Trivy (Vulnerabilities + Secrets + Misconfigurations)
=================================================================

[2024-12-26 15:30:45] ✅ SUCCESS: Target image found: nginx:latest
[2024-12-26 15:30:46] ⚠️  WARNING: 17 vulnerabilities found
[2024-12-26 15:30:46] ✅ SUCCESS: No secrets detected
[2024-12-26 15:30:46] ✅ SUCCESS: Scan completed successfully
```

## Advanced Usage

### Direct Docker Commands (If Needed)

If you prefer using Docker directly without the wrapper scripts:

```bash
# Note: You'll need to handle volume mounting manually
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-docker nginx:latest
```

**⚠️ Warning:** Manual volume mounting can be complex on Windows. The Python wrapper is recommended.

### Environment Variables

Set these for cloud provider authentication:

```bash
# AWS (for CloudFormation validation)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Azure (for ARM/Bicep validation)  
export AZURE_CLIENT_ID=your_client_id
export AZURE_CLIENT_SECRET=your_secret

# GCP (for Deployment Manager validation)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### CI/CD Integration

#### GitHub Actions

```yaml
name: Infrastructure Security Scan
on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Scanner
        run: |
          docker pull spd109/devops-uat:latest
          
      - name: Scan Infrastructure
        run: |
          python devops-scanner.py scan-terraform terraform/
          python devops-scanner.py scan-cloudformation cloudformation/
          
      - name: Upload Reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            *-scan-report.log
            *-summary.txt
```

#### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - security-scan

infrastructure-security:
  stage: security-scan
  image: python:3.9
  services:
    - docker:dind
  variables:
    DOCKER_DRIVER: overlay2
    DOCKER_TLS_CERTDIR: ""
  before_script:
    - docker pull spd109/devops-uat:latest
  script:
    - python devops-scanner.py scan-terraform terraform/
    - python devops-scanner.py scan-cloudformation cloudformation/
    - python devops-scanner.py scan-docker $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  artifacts:
    reports:
      # GitLab will parse these as security reports
      sast: "*-scan-report.log"
    paths:
      - "*-scan-report.log"
      - "*-summary.txt"
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

#### Azure DevOps Pipeline

```yaml
# azure-pipelines.yml
trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

stages:
- stage: SecurityScan
  displayName: 'Infrastructure Security Scan'
  jobs:
  - job: SecurityAnalysis
    displayName: 'Run Security Scanners'
    steps:
    - task: Docker@2
      displayName: 'Pull Scanner Image'
      inputs:
        command: 'pull'
        arguments: 'spd109/devops-uat:latest'
    
    - task: PythonScript@0
      displayName: 'Scan Terraform'
      inputs:
        scriptSource: 'inline'
        script: |
          import subprocess
          result = subprocess.run(['python', 'devops-scanner.py', 'scan-terraform', 'terraform/'], 
                                capture_output=True, text=True)
          print(result.stdout)
          if result.stderr:
              print("STDERR:", result.stderr)
    
    - task: PythonScript@0
      displayName: 'Scan CloudFormation'
      inputs:
        scriptSource: 'inline'
        script: |
          import subprocess
          result = subprocess.run(['python', 'devops-scanner.py', 'scan-cloudformation', 'cloudformation/'], 
                                capture_output=True, text=True)
          print(result.stdout)
          if result.stderr:
              print("STDERR:", result.stderr)
    
    - task: PublishBuildArtifacts@1
      displayName: 'Publish Security Reports'
      inputs:
        pathToPublish: '.'
        artifactName: 'security-reports'
        artifactType: 'container'
        includeRootFolder: false
        # Only include scan reports and summaries
        contents: |
          *-scan-report.log
          *-summary.txt
    
    - task: PublishTestResults@2
      displayName: 'Publish Security Test Results'
      condition: always()
      inputs:
        testResultsFormat: 'JUnit'
        testResultsFiles: '*-scan-report.log'
        failTaskOnFailedTests: false
        testRunTitle: 'Infrastructure Security Scan Results'
```

#### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Security Scan') {
            steps {
                sh 'docker pull spd109/devops-uat:latest'
                sh 'python devops-scanner.py scan-terraform terraform/'
                sh 'python devops-scanner.py scan-cloudformation cloudformation/'
                
                archiveArtifacts artifacts: '*-scan-report.log, *-summary.txt'
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: '*-summary.txt',
                    reportName: 'Security Scan Report'
                ])
            }
        }
    }
}
```

## Test Files Included

The repository includes test files for all scanner types:

```
test-files/
├── terraform/          # Sample Terraform configurations
├── cloudformation/     # Sample CloudFormation templates  
├── azure-arm/          # Sample ARM templates
├── azure-bicep/        # Sample Bicep templates
└── gcp-deployment-manager/  # Sample GCP templates
```

Run tests with:

```bash
python devops-scanner.py scan-terraform test-files/terraform/
python devops-scanner.py scan-cloudformation test-files/cloudformation/
python devops-scanner.py scan-arm test-files/azure-arm/
```

## Architecture

### Python Orchestrator Modules

- `devops-scanner.py` - Main orchestrator script
- `helpers/docker_manager.py` - Docker command construction and execution
- `helpers/path_detector.py` - Cross-platform path detection and formatting
- `helpers/scanner_orchestrator.py` - Scanner coordination and execution
- `helpers/result_processor.py` - Log analysis and summary generation

### Scanner Scripts (Inside Docker)

- `scanners/scan-terraform.sh` - TFLint + TFSec + Checkov
- `scanners/scan-cloudformation.sh` - CFN-Lint + Checkov
- `scanners/scan-docker.sh` - Trivy comprehensive scanning
- `scanners/scan-arm.sh` - ARM-TTK + Checkov
- `scanners/scan-bicep.sh` - Bicep CLI + Checkov
- `scanners/scan-gcp.sh` - Checkov + GCloud validation

## Troubleshooting

### Common Issues

**"Docker not found"**
```bash
# Ensure Docker is installed and running
docker --version
docker info
```

**"Permission denied"**
```bash
# On Linux/macOS, make scripts executable
chmod +x devops-scanner
chmod +x devops-scanner.py
```

**"Volume mount failed"**
```bash
# Use the Python wrapper - it handles path formatting automatically
python devops-scanner.py scan-terraform terraform/
```

### Debug Mode

Enable verbose output:

```bash
# Add debug flag to see Docker commands being executed
python devops-scanner.py --debug scan-terraform terraform/
```

## Contributing

1. Fork the repository
2. Test your changes with all scanner types
3. Ensure log output format consistency
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

---

**🚀 Ready to scan? Start with:** `python devops-scanner.py scan-docker nginx:latest`
