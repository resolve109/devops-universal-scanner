# DevOps Universal Scanner

A Docker image for validating infrastructure-as-code files with support for AWS CloudFormation and Terraform.

## Overview

This repository contains the source code for building a Docker image that includes validation tools for AWS CloudFormation templates and Terraform configurations. The image provides simple, easy-to-use commands for scanning and validating your infrastructure code.

## Features

- **Simple Commands**: Easy-to-use scan commands for Terraform, CloudFormation, and Docker images
- **Current Support**: Validates infrastructure templates and container images for:
  - AWS (CloudFormation)
  - Cross-platform (Terraform)
  - Docker container images

- **Comprehensive Validation**: Includes various validation tools:
  - Syntax and structural validation
  - Security scanning with checkov and tfsec  
  - Linting and best practices with cfn-lint and tflint
  - Container vulnerability scanning with Trivy
  - Secret detection
  
- **JSON Report Output**: All scanners generate structured JSON reports:
  - `terraform-scan-report.json` (TFLint, TFSec, Checkov results)
  - `cloudformation-scan-report.json` (CFN-Lint, Checkov, AWS validation)
  - `trivy-report.json` (Container vulnerabilities, secrets, misconfigurations)
  
- **Auto-Updating**: Tools automatically update to latest versions on container start  
- **Cross-platform**: Works on:
  - Windows
  - macOS  
  - Linux
  - CI/CD servers

- **Flexible usage**: Can be used:
  - As part of a CI/CD pipeline
  - For local development
  - With or without AWS cloud provider credentials

## Current Status

**✅ Tested & Working:**

- AWS CloudFormation template validation with JSON output (tested with S3.yaml)
- Terraform configuration validation with JSON output (tested with multiple .tf files)
- Docker container image scanning with JSON output (tested with Trivy)
- Simple scan commands: `scan-terraform`, `scan-cloudformation`, and `scan-docker`
- All scanners now generate structured JSON reports for integration with CI/CD pipelines

**⚠️ Available but Untested:**

- Azure ARM templates, Bicep (tools installed but not tested)
- GCP Deployment Manager (tools installed but not tested)  
- Auto-detection and smart-validate features
- Various wrapper commands for individual tools

**Recommended Usage:** Use the tested scan commands for reliable validation.

## Quick Start

### Using the pre-built Docker image from Docker Hub

```bash
docker pull spd109/devops-uat:latest
```

## Simple Usage

### For Terraform

```bash
# Simple command - just point to the terraform directory
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-terraform terraform
```

### For CloudFormation (AWS)

```bash
# Simple command - just point to the CloudFormation file
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-cloudformation S3.yaml
```

### For Docker Images

```bash
# Simple command - just specify the image name and tag
docker run -it --rm spd109/devops-uat:latest scan-docker nginx:latest

# Scan a custom application image
docker run -it --rm spd109/devops-uat:latest scan-docker myapp:1.0.0
```

### Advanced Usage

Use the tested scanning commands with various options:

#### Linux/macOS

```bash
# Scan CloudFormation template
docker run --rm -v $(pwd):/work spd109/devops-uat:latest scan-cloudformation your-template.yaml

# Validate a Terraform directory
docker run --rm -v $(pwd):/work spd109/devops-uat:latest scan-terraform ./terraform/

# With AWS credentials
docker run --rm -v $(pwd):/work \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  spd109/devops-uat:latest scan-cloudformation template.yaml

# Scan Docker container images
docker run --rm spd109/devops-uat:latest scan-docker nginx:latest
docker run --rm spd109/devops-uat:latest scan-docker ubuntu:22.04
```

#### Windows (Command Prompt)

```cmd
REM Scan CloudFormation template
docker run --rm -v "%CD%":/work spd109/devops-uat:latest scan-cloudformation your-template.yaml

REM Validate a Terraform directory
docker run --rm -v "%CD%":/work spd109/devops-uat:latest scan-terraform terraform\

REM Scan Docker container images  
docker run --rm spd109/devops-uat:latest scan-docker nginx:latest
docker run --rm spd109/devops-uat:latest scan-docker spd109/devops-uat:latest
```

### Legacy Commands (Still Available)

For backwards compatibility, these legacy commands are still available:

```bash
# Environment setup and validation
docker run --rm -v "%cd%":/work spd109/devops-uat:latest uat-setup setup

# Auto-detect file type (experimental)
docker run --rm -v "%cd%":/work spd109/devops-uat:latest auto-detect template.yaml
```
