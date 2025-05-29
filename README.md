# DevOps Universal Scanner

**🚀 Comprehensive DevOps Security Scanner**

A comprehensive Docker-based security scanner for your infrastructure code with intelligent error handling and helpful command suggestions.
This scanner supports multiple formats including Terraform, CloudFormation, Docker images, Azure ARM/Bicep templates, and GCP Deployment Manager configurations. It uses industry-standard tools like TFLint, TFSec, Checkov, Trivy, and more to ensure your infrastructure is secure and compliant.

## What Makes This Different

✅ **One simple command structure** for all scan types  
✅ **Comprehensive LOG format** with full terminal output capture  
✅ **Intelligent error handling** with helpful command suggestions  
✅ **Cross-platform Docker commands** with clear examples  

**Simple usage with Docker:**
```bash
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/
```

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

# Windows (Command Prompt)
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-terraform terraform/

# Linux/macOS
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/
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
    - docker(most likely your runner name)  
  variables:
    DOCKER_DRIVER: overlay2
    DOCKER_TLS_CERTDIR: ""
  before_script:
    - docker pull spd109/devops-uat:latest  script:
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
        stage('Security Scan') {            steps {
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

```
test-files/
├── terraform/              # Terraform configurations with vulnerabilities
├── cloudformation/         # AWS CloudFormation templates with issues
├── azure-arm/              # Azure ARM templates with misconfigurations
├── azure-bicep/            # Azure Bicep templates with security issues
└── gcp-deployment-manager/ # GCP templates with vulnerabilities
```

### Test File Details

**Terraform (`terraform/`):**
- `main.tf` - Multi-cloud infrastructure with hardcoded credentials, unencrypted resources
- `variables.tf` - Sensitive data in defaults, no input validation
- `outputs.tf` - Outputting credentials and sensitive information
- `providers.tf` - Hardcoded credentials, weak security settings

**CloudFormation (`cloudformation/`):**
- `ec2-instance.yaml` - Unencrypted storage, overly permissive security groups
- `rds-database.json` - Public access, weak passwords, no encryption
- `s3-iam-vulnerable.json` - Public bucket access, overly permissive IAM
- `networking-vulnerable.yaml` - Wide-open security groups and network ACLs

**Azure ARM (`azure-arm/`):**
- `vm-with-storage.json` - Unencrypted storage, weak authentication
- `keyvault-sql-vulnerable.json` - Weak access policies, public network access

**Azure Bicep (`azure-bicep/`):**
- `storage-account.bicep` - Public access, no encryption, weak TLS
- `web-app.bicep` - HTTPS not enforced, hardcoded secrets

**GCP Deployment Manager (`gcp-deployment-manager/`):**
- `vulnerable-infrastructure.yaml` - Overly permissive firewall rules, public storage
- `vm-template.jinja` - Default service accounts, no shielded VM

### Security Issues Tested

✅ **Authentication & Authorization** - Hardcoded credentials, weak passwords, overly permissive IAM  
✅ **Network Security** - 0.0.0.0/0 access, public subnets, missing VPC flow logs  
✅ **Data Protection** - Unencrypted storage, public read/write access, no backup encryption  
✅ **Monitoring & Logging** - Disabled audit logging, no security monitoring  
✅ **Configuration Security** - Debug modes enabled, default configurations, insecure protocols  
✅ **Information Disclosure** - Outputting sensitive data, storing secrets in plain text  

### Run Tests

```bash
# Test all scanners with included sample files
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform test-files/terraform/
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-cloudformation test-files/cloudformation/
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-arm test-files/azure-arm/
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-bicep test-files/azure-bicep/
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-gcp test-files/gcp-deployment-manager/
docker run -it --rm spd109/devops-uat:latest scan-docker nginx:latest
```

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

---

**🚀 Ready to scan? Start with:** `docker run -it --rm spd109/devops-uat:latest scan-docker nginx:latest`
