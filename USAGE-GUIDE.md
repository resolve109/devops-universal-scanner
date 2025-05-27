# DevOps Universal Scanner - Simple Usage

## ✅ SUCCESS! The container now has simple commands built-in:

### 🔹 For Terraform (Azure):
```bash
# Simple command - just point to the terraform directory
docker run -it --rm -v "%cd%:/work" devops-uat:latest scan-terraform /work/terraform
```

### 🔹 For CloudFormation (AWS):
```bash
# Simple command - just point to the CloudFormation file
docker run -it --rm -v "%cd%:/work" devops-uat:latest scan-cloudformation /work/S3.yaml
```

## What the Scripts Do:

### scan-terraform.sh:
- ✅ Auto-detects all .tf files in the directory
- ✅ Runs TFLint for Terraform linting
- ✅ Runs TFSec for security scanning
- ✅ Runs Checkov for policy compliance
- ✅ Attempts Terraform plan (dry run)

### scan-cloudformation.sh:
- ✅ Validates the CloudFormation file exists
- ✅ Runs CFN-Lint for CloudFormation validation
- ✅ Runs Checkov for security and compliance
- ✅ Attempts AWS CloudFormation validation (if credentials available)

## Test Results:
- ✅ Container builds successfully 
- ✅ Terraform scan detects all 12 .tf files
- ✅ CloudFormation scan processes S3.yaml
- ✅ Both tools run their respective scanners

## Files Added to Container:
- `/usr/local/bin/scan-terraform` (symlink to script)
- `/usr/local/bin/scan-cloudformation` (symlink to script)

The commands are now SHORT and SIMPLE as requested!
