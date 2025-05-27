# DevOps Universal Scanner

A versatile multi-cloud infrastructure-as-code validation Docker image with smart detection for AWS, Azure, and GCP resources.

## Overview

This repository contains the source code for building a Docker image that includes various tools for validating infrastructure-as-code files across multiple cloud providers (AWS, Azure, GCP) and formats (CloudFormation, ARM, Terraform, etc.). The image features smart detection capabilities to automatically identify file types and run appropriate validation tools.

## Features

- **Smart Auto-Detection**: Automatically detects file type and cloud provider to run appropriate tools
- **Multi-Cloud Support**: Validates infrastructure templates for:
  - AWS (CloudFormation, CDK, SAM)
  - Azure (ARM Templates, Bicep)
  - GCP (Deployment Manager)
  - Cross-platform (Terraform, Pulumi)

- **Comprehensive Validation**: Includes various validation tools:
  - Syntax and structural validation
  - Security scanning with checkov, tfsec, and Snyk
  - Linting and best practices with cfn-lint, tflint, arm-ttk
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
  - With or without cloud provider credentials

## Quick Start

### Using the pre-built Docker image from Docker Hub

```bash
docker pull spd109/devops-universal-scanner:latest
```

## Simple Usage

### For Terraform (Azure)

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

### Advanced Usage with Auto-Detection

The container will automatically detect the file type and run appropriate validation tools.

#### Linux/macOS

```bash
# Auto-detect and validate any IaC file
docker run --rm -v $(pwd):/work spd109/devops-universal-scanner:latest smart-validate your-template.yaml

# Validate a Terraform directory
docker run --rm -v $(pwd):/work spd109/devops-universal-scanner:latest smart-validate ./terraform/

# With cloud credentials
docker run --rm -v $(pwd):/work \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -e AZURE_SUBSCRIPTION_ID=$AZURE_SUBSCRIPTION_ID \
  spd109/devops-universal-scanner:latest smart-validate template.yaml
```

#### Windows (Command Prompt)

```cmd
REM Auto-detect and validate any IaC file
docker run --rm -v "%CD%":/work spd109/devops-universal-scanner:latest smart-validate your-template.yaml

REM Validate a Terraform directory
docker run --rm -v "%CD%":/work spd109/devops-universal-scanner:latest smart-validate terraform\
```
