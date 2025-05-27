# DevOps Universal Scanner - Container Documentation

## Available Commands

### Primary Scanning Commands (Tested & Recommended)

#### Terraform Scanning
```bash
scan-terraform terraform        # Scan terraform directory
scan-terraform terraform/file.tf   # Scan specific terraform file
```

#### CloudFormation Scanning
```bash
scan-cloudformation template.yaml  # Scan CloudFormation template
scan-cloudformation S3.yaml       # Scan specific CloudFormation file
```

### Legacy Commands (Still Available)

```bash
entrypoint template.yaml report.txt    # Legacy CloudFormation scanning
run-linter terraform report.txt        # Legacy Terraform scanning
```

### Advanced Commands (Experimental)

```bash
auto-detect template.yaml              # Auto-detect file type
smart-validate template.yaml           # Smart validation with auto-detection
```

### Built-in Tools

**Tested & Supported:**
- **Terraform**: terraform, tflint, tfsec, checkov
- **CloudFormation**: cfn-lint, checkov, aws-cli
- **Security**: checkov, tfsec, detect-secrets
- **General**: git, jq, curl, wget

**Additional Tools (Installed but untested):**

- **Azure**: azure-cli, bicep, arm-ttk  
- **GCP**: google-cloud-cli
- **Security**: trivy

### Volume Mounting

The container expects your code to be mounted at `/work`:

```bash
docker run -it --rm -v "$(pwd):/work" spd109/devops-uat:latest scan-terraform terraform
```

### Examples

```bash
# Scan Terraform directory
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-terraform terraform

# Scan CloudFormation template
docker run -it --rm -v "%cd%:/work" spd109/devops-uat:latest scan-cloudformation S3.yaml
```
