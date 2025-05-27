# DevOps Universal Scanner

A Docker image for validating infrastructure-as-code files with support for AWS CloudFormation and Terraform.

## Overview

This repository contains the source code for building a Docker image that includes validation tools for AWS CloudFormation templates and Terraform configurations. The image provides simple, easy-to-use commands for scanning and validating your infrastructure code.

## Features

- **Simple Commands**: Easy-to-use scan commands for Terraform and CloudFormation
- **Current Support**: Validates infrastructure templates for:
  - AWS (CloudFormation)
  - Cross-platform (Terraform)

- **Comprehensive Validation**: Includes various validation tools:
  - Syntax and structural validation
  - Security scanning with checkov and tfsec  
  - Linting and best practices with cfn-lint and tflint
  - Secret detection
  
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

- AWS CloudFormation template validation (tested with S3.yaml)
- Terraform configuration validation (tested with 12 .tf files)
- Simple scan commands: `scan-terraform` and `scan-cloudformation`

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

### Even Simpler with Wrapper Scripts

Create these simple wrapper scripts:

**scan-tf.bat** (Windows):

```batch
@echo off
if "%1"=="" (
    echo Usage: scan-tf.bat terraform
    exit /b 1
)
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-terraform %1
```

**scan-cf.bat** (Windows):

```batch
@echo off
if "%1"=="" (
    echo Usage: scan-cf.bat S3.yaml
    exit /b 1
)
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-cloudformation %1
```

Then simply run:

```cmd
scan-tf.bat terraform
scan-cf.bat S3.yaml
```

### Advanced Usage

Use the scanning commands with various options:

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
```

#### Windows (Command Prompt)

```cmd
REM Scan CloudFormation template
docker run --rm -v "%CD%":/work spd109/devops-uat:latest scan-cloudformation your-template.yaml

REM Validate a Terraform directory
docker run --rm -v "%CD%":/work spd109/devops-uat:latest scan-terraform terraform\
```

### Legacy Commands (Still Available)

For backwards compatibility, these legacy commands are still available:

```bash
# Legacy CloudFormation scanning
docker run --rm -v "%cd%":/work spd109/devops-uat:latest entrypoint template.yaml report.txt

# Legacy Terraform scanning  
docker run --rm -v "%cd%":/work spd109/devops-uat:latest run-linter terraform report.txt
```
