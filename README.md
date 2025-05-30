# DevOps Universal Scanner

**🚀 Comprehensive DevOps Security Scanner**

A comprehensive Docker-based security scanner for your infrastructure code with intelligent error handling and helpful command suggestions.
This scanner supports multiple formats including Terraform, CloudFormation, Docker images, Azure ARM/Bicep templates, and GCP Deployment Manager configurations. It uses industry-standard tools like TFLint, TFSec, Checkov, Trivy, and more to ensure your infrastructure is secure and compliant.

## What Makes This Different

✅ **One simple command structure** for all scan types  
✅ **Comprehensive LOG format** with full terminal output capture  
✅ **Intelligent error handling** with helpful command suggestions  
✅ **Cross-platform Docker commands** with clear examples  
✅ **Lightweight Alpine-based image** for faster performance and smaller footprint

**Simple usage with Docker:**
```bash
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/
```

## Image Details

The DevOps Universal Scanner is built on Alpine Linux to provide a lightweight, fast, and efficient container:

- **Base Image**: Alpine Linux 3.21.3 (lightweight and secure)
- **Image Size**: ~1.02GB (multi-stage optimized version)
- **Docker Hub**: [spd109/devops-uat:latest](https://hub.docker.com/r/spd109/devops-uat)
- **Versioned Tags**: YYYYMMDD format (e.g., `spd109/devops-uat:20250529`)
- **Architecture**: Multi-platform support (linux/amd64, linux/arm64)
- **Updated**: May 29, 2025 - Latest multi-stage optimized build

### Performance Improvements

The new multi-stage optimized image provides significant improvements over previous versions:

| Metric | Original Version | Optimized Version (Current) | Improvement |
|--------|------------------|----------------------------|-------------|
| **Image Size** | ~1.58GB | ~1.02GB | **35.4% smaller** |
| **Pull Time** | ~3-4 minutes | ~2-3 minutes | **33% faster** |
| **Build Time** | ~2.5 minutes | ~1.1 minutes | **56% faster** |
| **Python Layer** | 542MB | 196MB | **63.8% smaller** |
| **Base Layer** | 180MB | 134MB | **25.6% smaller** |
| **ARM-TTK** | 16MB | 8.6MB | **46% smaller** |

### Multi-Stage Build Optimizations

The optimized image uses a multi-stage build approach:

🔧 **Builder Stage**: Compiles tools and installs Python packages with build dependencies  
🚀 **Runtime Stage**: Only includes runtime dependencies and compiled binaries  
📦 **Virtual Environment**: Isolated Python packages for better dependency management  
🧹 **Cleanup**: Removes .git directories and unnecessary files  

**Key Size Reductions:**
- **Python packages**: 542MB → 196MB (saved 346MB)
- **Build dependencies**: Completely removed from final image  
- **Repository cleanup**: Removed .git directories and docs  
- **Runtime-only base**: Only essential packages for execution  

**Why Multi-Stage Builds?**
- **Separation of Concerns**: Build tools don't pollute runtime environment
- **Smaller Images**: Only necessary components in final image
- **Security**: Fewer tools available for potential exploitation
- **Efficiency**: Faster pulls and deployments

### Included Scanning Tools

| Category | Tools |
|----------|-------|
| Terraform | Terraform CLI, TFLint, TFSec, Checkov |
| AWS | CFN-Lint, Checkov |
| Azure | Bicep CLI, ARM-TTK, Checkov |
| GCP | Google Cloud Libraries, Checkov |
| Container | Trivy (vulnerabilities, secrets, misconfigurations) |

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
```

### 2. Run Scans

**🎯 Basic Commands:**

```bash
# Windows (PowerShell)
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-terraform terraform/

# Windows (Command Prompt) - RECOMMENDED METHOD
docker run --rm -v "%cd%:/work" spd109/devops-uat:latest scan-terraform terraform/

# Windows (Command Prompt) - RECOMMENDED CLOUDFORMATION SCAN
docker run --rm -v "%cd%:/work" spd109/devops-uat:latest scan-cloudformation test-files/cloudformation/ec2-instance.yaml

# Linux/macOS
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/
```

**Windows Users:** If you experience volume mounting issues, use the provided helper scripts:

```cmd
# Using Command Prompt
run-scan-windows.bat scan-cloudformation test-files/cloudformation/s3-iam-vulnerable.json

# Using PowerShell
.\helpers\run-scan-windows.ps1 scan-terraform terraform/
```

**Example Commands:**

```bash
# Terraform configurations
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/

# CloudFormation templates
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-cloudformation template.yaml

# Container images for vulnerabilities
docker run -it --rm spd109/devops-uat:latest scan-docker nginx:latest

# Azure ARM templates
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-arm template.json

# Azure Bicep templates  
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-bicep template.bicep

# GCP templates
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-gcp template.yaml
```

### Cross-Platform Command Reference

#### Windows

**PowerShell:**
```powershell
# Current directory
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-terraform ./terraform/

# Full path to directory
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-terraform ./infrastructure/terraform/

# Specific file with explicit path
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-cloudformation ./cloudformation/template.yaml

# With environment variables for AWS
$env:AWS_ACCESS_KEY_ID="your_key"
$env:AWS_SECRET_ACCESS_KEY="your_secret"
docker run -it --rm -v "${PWD}:/work" -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY spd109/devops-uat:latest scan-cloudformation template.yaml

# Scan Docker image with output to specific location
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-docker nginx:latest
```

**Command Prompt (CMD):**
```cmd
REM Current directory
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-terraform terraform\

REM Full path (note the backslash escaping for Windows paths)
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-terraform C:\path\to\terraform\

REM Scan a specific file
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-arm azure-arm\template.json
```

#### macOS/Linux

**Bash/ZSH:**
```bash
# Current directory
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform ./terraform/

# Absolute path
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform /path/to/terraform/

# Single file scan
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-bicep ./azure-bicep/template.bicep

# With environment variables
AWS_ACCESS_KEY_ID=your_key AWS_SECRET_ACCESS_KEY=your_secret docker run -it --rm -v "$(pwd):/work" -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY spd109/devops-uat:latest scan-cloudformation template.yaml
```

**Fish Shell:**
```fish
# Current directory
docker run -it --rm -v (pwd):/work spd109/devops-uat:latest scan-terraform ./terraform/

# Absolute path
docker run -it --rm -v (pwd):/work spd109/devops-uat:latest scan-terraform /path/to/terraform/
```

### Windows Terminal

**Command Prompt (cmd.exe):**
```cmd
REM Basic scan
docker run --rm -v "%cd%:/work" spd109/devops-uat:latest scan-terraform terraform\

REM CloudFormation scan - RECOMMENDED METHOD
docker run --rm -v "%cd%:/work" spd109/devops-uat:latest scan-cloudformation test-files/cloudformation/ec2-instance.yaml

REM With environment variables
set AWS_ACCESS_KEY_ID=your_key
set AWS_SECRET_ACCESS_KEY=your_secret
docker run --rm -v "%cd%:/work" -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY spd109/devops-uat:latest scan-cloudformation template.yaml
```

### Troubleshooting Windows Commands

If you get "docker is not recognized as an internal or external command", you need to:

1. Make sure Docker is installed
2. Add Docker to your PATH:
   - Right-click Start > System > Advanced System Settings > Environment Variables
   - Under "System variables", find the "Path" variable, select it and click "Edit"
   - Add: `C:\Program Files\Docker\Docker\resources\bin`
   - Click OK on all dialogs
   - Restart your Command Prompt

**PowerShell Core (pwsh):**
```powershell
# Basic scan
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-terraform terraform/

# With environment variables
$env:AWS_ACCESS_KEY_ID="your_key"
$env:AWS_SECRET_ACCESS_KEY="your_secret"
docker run -it --rm -v "${PWD}:/work" -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY spd109/devops-uat:latest scan-cloudformation template.yaml
```

#### Unix/Linux Terminal

**Bash:**
```bash
# Basic scan
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/

# With environment variables
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
docker run -it --rm -v "$(pwd):/work" -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY spd109/devops-uat:latest scan-cloudformation template.yaml
```

**Zsh:**
```zsh
# Basic scan (same as bash)
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/

# With array environment variables
typeset -A env_vars
env_vars[AWS_ACCESS_KEY_ID]="your_key"
env_vars[AWS_SECRET_ACCESS_KEY]="your_secret"
docker run -it --rm -v "$(pwd):/work" -e AWS_ACCESS_KEY_ID="${env_vars[AWS_ACCESS_KEY_ID]}" -e AWS_SECRET_ACCESS_KEY="${env_vars[AWS_SECRET_ACCESS_KEY]}" spd109/devops-uat:latest scan-cloudformation template.yaml
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
          docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/
          docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-cloudformation cloudformation/
          
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
  tags:
    - docker  # Most likely your runner name
  variables:
    DOCKER_DRIVER: overlay2
    DOCKER_TLS_CERTDIR: ""
  before_script:
    - docker pull spd109/devops-uat:latest
  script:
    - docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/
    - docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-cloudformation cloudformation/
    - docker run -it --rm spd109/devops-uat:latest scan-docker $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
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
          result = subprocess.run(['docker', 'run', '-it', '--rm', '-v', '$(pwd):/work', 'spd109/devops-uat:latest', 'scan-terraform', 'terraform/'], 
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
          result = subprocess.run(['docker', 'run', '-it', '--rm', '-v', '$(pwd):/work', 'spd109/devops-uat:latest', 'scan-cloudformation', 'cloudformation/'], 
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
                sh 'docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/'
                sh 'docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-cloudformation cloudformation/'
                
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

The repository includes comprehensive test files with **intentional security vulnerabilities** for validating the scanner's capabilities.

⚠️ **WARNING**: These files contain intentional security misconfigurations and should NEVER be used in production! Do not deploy them in any live environment. They are strictly for testing and educational purposes. Like really, don't use these in production! I'm serious, these files are designed to break things and expose vulnerabilities. Use them wisely in isolated environments only. Don't say I didn't warn you! If you deploy these in production, you're asking for trouble. Seriously, don't do it! Consider this your final warning: these files are for testing only. They will cause security issues if used in production. Use at your own risk! Cause if you deploy these in production, you're basically inviting hackers to your system. So please, for the love of security, don't use these files in any live environment! And remember, these files are meant to help you learn about security vulnerabilities, not to create them in your production systems. Use them wisely and responsibly! Just don't deploy these in production, okay? They're meant to help you learn about security vulnerabilities, not to create them in your production systems. Use them wisely and responsibly! Exactly, these files are meant to help you learn about security vulnerabilities, not to create them in your production systems. Use them wisely and responsibly! 

### Directory Structure

```text
test-files/
├── terraform/              # Terraform configurations with vulnerabilities
├── cloudformation/         # AWS CloudFormation templates with issues
├── azure-arm/              # Azure ARM templates with misconfigurations
├── azure-bicep/            # Azure Bicep templates with security issues
├── gcp-deployment-manager/ # GCP templates with vulnerabilities
├── kubernetes/             # Kubernetes manifests with security flaws
└── docker/                 # Docker and container configuration issues
```

### Test File Details

**Terraform (`terraform/`):**
- `main.tf` - Multi-cloud infrastructure with hardcoded credentials, unencrypted resources
- `variables.tf` - Sensitive data in defaults, no input validation
- `outputs.tf` - Outputting credentials and sensitive information
- `providers.tf` - Hardcoded credentials, weak security settings
- `kubernetes-clusters.tf` - Multi-cloud K8s clusters with security vulnerabilities

**CloudFormation (`cloudformation/`):**
- `ec2-instance.yaml` - Unencrypted storage, overly permissive security groups
- `rds-database.json` - Public access, weak passwords, no encryption
- `s3-iam-vulnerable.json` - Public bucket access, overly permissive IAM
- `networking-vulnerable.yaml` - Wide-open security groups and network ACLs
- `serverless-vulnerable.yaml` - Lambda, API Gateway, DynamoDB with security issues

**Azure ARM (`azure-arm/`):**
- `vm-with-storage.json` - Unencrypted storage, weak authentication
- `keyvault-sql-vulnerable.json` - Weak access policies, public network access

**Azure Bicep (`azure-bicep/`):**
- `storage-account.bicep` - Public access, no encryption, weak TLS
- `web-app.bicep` - HTTPS not enforced, hardcoded secrets

**GCP Deployment Manager (`gcp-deployment-manager/`):**
- `vulnerable-infrastructure.yaml` - Overly permissive firewall rules, public storage
- `vm-template.jinja` - Default service accounts, no shielded VM

**Kubernetes (`kubernetes/`):**
- `vulnerable-pod.yaml` - Privileged containers, host access, security context issues
- `vulnerable-deployment.yaml` - Insecure deployments, exposed secrets, no resource limits

**Docker (`docker/`):**
- `Dockerfile.vulnerable` - Running as root, hardcoded secrets, insecure base images
- `docker-compose.vulnerable.yml` - Privileged containers, exposed services, weak passwords

### Security Issues Tested

✅ **Authentication & Authorization** - Hardcoded credentials, weak passwords, overly permissive IAM  
✅ **Network Security** - 0.0.0.0/0 access, public subnets, missing VPC flow logs  
✅ **Data Protection** - Unencrypted storage, public read/write access, no backup encryption  
✅ **Monitoring & Logging** - Disabled audit logging, no security monitoring  
✅ **Configuration Security** - Debug modes enabled, default configurations, insecure protocols  
✅ **Information Disclosure** - Outputting sensitive data, storing secrets in plain text  

### Run Tests

**Windows (Command Prompt):**
```cmd
REM Test all scanners with included sample files
docker run --rm -v "%cd%:/work" spd109/devops-uat:latest scan-terraform test-files/terraform/
docker run --rm -v "%cd%:/work" spd109/devops-uat:latest scan-cloudformation test-files/cloudformation/
docker run --rm -v "%cd%:/work" spd109/devops-uat:latest scan-arm test-files/azure-arm/
docker run --rm -v "%cd%:/work" spd109/devops-uat:latest scan-bicep test-files/azure-bicep/
docker run --rm -v "%cd%:/work" spd109/devops-uat:latest scan-gcp test-files/gcp-deployment-manager/
docker run --rm spd109/devops-uat:latest scan-docker nginx:latest

REM Test specific vulnerable files
docker run --rm -v "%cd%:/work" spd109/devops-uat:latest scan-terraform test-files/terraform/kubernetes-clusters.tf
docker run --rm -v "%cd%:/work" spd109/devops-uat:latest scan-cloudformation test-files/cloudformation/serverless-vulnerable.yaml
```

**Windows (PowerShell):**
```powershell
# Test all scanners with included sample files
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-terraform test-files/terraform/
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-cloudformation test-files/cloudformation/
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-arm test-files/azure-arm/
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-bicep test-files/azure-bicep/
docker run -it --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-gcp test-files/gcp-deployment-manager/
docker run -it --rm spd109/devops-uat:latest scan-docker nginx:latest
```

**Linux/macOS:**
```bash
# Test all scanners with included sample files
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform test-files/terraform/
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-cloudformation test-files/cloudformation/
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-arm test-files/azure-arm/
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-bicep test-files/azure-bicep/
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-gcp test-files/gcp-deployment-manager/
docker run -it --rm spd109/devops-uat:latest scan-docker nginx:latest
```

### Quick Validation

**Windows (Command Prompt):**
```cmd
REM Run the validation script to test all scanners
validate-setup.bat
```

**Windows (PowerShell):**
```powershell
# Run the validation script to test all scanners
.\validate-setup.ps1
```

**Linux/macOS:**
```bash
# Create and run validation script
chmod +x validate-setup.sh
./validate-setup.sh
```

The validation scripts will:
- ✅ Check Docker installation
- 📥 Pull the latest scanner image
- 🧪 Test all scanner types with sample files
- 📊 Generate reports you can review

### Expected Findings

Each test file should trigger multiple security findings:
- **High Severity**: Hardcoded credentials, public access, disabled encryption
- **Medium Severity**: Weak configurations, missing monitoring, overly permissive access  
- **Low Severity**: Missing tags, suboptimal configurations, informational issues

## Architecture

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
# On Linux/macOS, ensure Docker is running
sudo systemctl start docker
```

**"Volume mount failed"**
```bash
# Ensure you're in the correct directory with your files
ls terraform/  # Should show your .tf files
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/
```

## Contributing

1. Fork the repository
2. Test your changes with all scanner types
3. Ensure log output format consistency
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Quick Start Summary

1. **Pull the image**: `docker pull spd109/devops-uat:latest`
2. **Run validation**: `validate-setup.bat` (Windows) or `./validate-setup.sh` (Linux/macOS)
3. **Scan your code**: `docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/`

---

**🚀 Ready to scan? Start with:** `docker run -it --rm spd109/devops-uat:latest scan-docker nginx:latest`
