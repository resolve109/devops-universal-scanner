# DevOps Universal Scanner

**Multi-cloud infrastructure security scanner with FinOps cost analysis and CVE detection.**

Scans Terraform, CloudFormation, Azure, GCP, Kubernetes, and Docker for security issues, misconfigurations, and provides intelligent cost optimization recommendations.

## Quick Start

```bash
# Pull the image
docker pull spd109/devops-uat:latest

# Scan your infrastructure
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/
```

## What It Does

- **Security Scanning** - Detects vulnerabilities, misconfigurations, and policy violations
- **FinOps Analysis** - Calculates costs and provides optimization recommendations
- **CVE Detection** - Scans tools, AMIs, and container images for known vulnerabilities
- **Multi-Cloud** - AWS, Azure, GCP support in one tool

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Command (CLI)                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Scanner Orchestrator (core/scanner.py)          │
│  • Auto-detects file types                                   │
│  • Manages execution flow                                    │
│  • Coordinates all layers                                    │
└─────┬───────────────────┬───────────────────┬───────────────┘
      │                   │                   │
      ▼                   ▼                   ▼
┌─────────────┐  ┌──────────────────┐  ┌─────────────────┐
│ Tool Runner │  │ Native Analysis  │  │  CVE Scanner    │
├─────────────┤  ├──────────────────┤  ├─────────────────┤
│ • Checkov   │  │ • Cost Analysis  │  │ • Tool CVEs     │
│ • TFLint    │  │ • FinOps Recs    │  │ • AMI CVEs      │
│ • TFSec     │  │ • GPU Analysis   │  │ • Image CVEs    │
│ • CFN-Lint  │  │ • Idle Detection │  │ • Live Updates  │
│ • ARM-TTK   │  │ • Live Pricing   │  │                 │
└─────┬───────┘  └────────┬─────────┘  └────────┬────────┘
      │                   │                      │
      └───────────────────┴──────────────────────┘
                          │
                          ▼
      ┌────────────────────────────────────────────┐
      │       Dual Logger (core/logger.py)         │
      ├────────────────────────────────────────────┤
      │  • Console: Live feedback with colors      │
      │  • Log File: Timestamped complete record   │
      └────────────────────────────────────────────┘
```

## Scan Commands

| Command | What It Scans |
|---------|---------------|
| `scan-terraform` | Terraform configurations |
| `scan-cloudformation` | CloudFormation templates |
| `scan-docker` | Container images |
| `scan-arm` | Azure ARM templates |
| `scan-bicep` | Azure Bicep templates |
| `scan-gcp` | GCP Deployment Manager |
| `scan-kubernetes` | Kubernetes manifests |

## Usage

### Basic Commands

```bash
# Linux/macOS
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/

# Windows PowerShell
docker run --rm -v "${PWD}:/work" spd109/devops-uat:latest scan-terraform terraform/

# Windows CMD
docker run --rm -v "%cd%:/work" spd109/devops-uat:latest scan-terraform terraform/
```

### Examples by Platform

**Terraform**
```bash
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform/
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform main.tf
```

**CloudFormation**
```bash
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-cloudformation template.yaml
```

**Docker Images**
```bash
docker run --rm spd109/devops-uat:latest scan-docker nginx:latest
```

**Azure**
```bash
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-arm template.json
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-bicep template.bicep
```

**GCP & Kubernetes**
```bash
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-gcp template.yaml
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-kubernetes manifests/
```

### With Cloud Credentials

```bash
# AWS
docker run --rm -v "$(pwd):/work" \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  spd109/devops-uat:latest scan-cloudformation template.yaml

# Azure
docker run --rm -v "$(pwd):/work" \
  -e AZURE_CLIENT_ID \
  -e AZURE_CLIENT_SECRET \
  spd109/devops-uat:latest scan-arm template.json

# GCP
docker run --rm -v "$(pwd):/work" \
  -e GOOGLE_APPLICATION_CREDENTIALS=/work/service-account.json \
  spd109/devops-uat:latest scan-gcp template.yaml
```

## Output

Each scan generates timestamped log files with:
- Security findings (vulnerabilities, misconfigurations)
- Cost analysis (monthly/weekly/daily estimates)
- FinOps recommendations (potential savings)
- CVE scan results

Example:
```log
=================================================================
              TERRAFORM SECURITY SCAN REPORT
=================================================================

[2025-11-19 14:30:45] ✅ Running TFLint...
[2025-11-19 14:30:47] ⚠️  Found 3 issues
[2025-11-19 14:30:50] ❌ Found 12 security issues
[2025-11-19 14:30:55] ⚠️  Found 8 policy violations

=================================================================
                    NATIVE INTELLIGENCE
=================================================================
💰 Cost Analysis:
   • Monthly: $1,247.50
   • Potential Savings: $936.25 (75%)

🎯 FinOps Recommendations:
   • Use Reserved Instances (save $498/month)
   • Implement business hours scheduling (save $389/month)
   • Switch to gp3 storage (save $49/month)
```

## Test It

The repository includes intentionally vulnerable test files:

```bash
# Test all scanners
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform test-files/terraform/
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-cloudformation test-files/cloudformation/
docker run --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-kubernetes test-files/kubernetes/
docker run --rm spd109/devops-uat:latest scan-docker nginx:latest
```

**⚠️ WARNING**: Test files contain intentional vulnerabilities. Never use in production.

## Troubleshooting

**Docker not found (Windows)**
```bash
# Add to PATH: C:\Program Files\Docker\Docker\resources\bin
# Restart terminal and test
docker --version
```

**Volume mount issues**
```bash
# Ensure you're in the correct directory
ls terraform/  # Should show your files

# Or use absolute path
docker run --rm -v "/full/path:/work" spd109/devops-uat:latest scan-terraform .
```

**Permission denied (Linux)**
```bash
sudo systemctl start docker
sudo usermod -aG docker $USER  # Then logout/login
```

## License

MIT License
