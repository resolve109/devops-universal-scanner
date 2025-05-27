# DevOps Universal Scanner - Container Documentation

## Available Commands

### Simple Scanning Commands

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
auto-detect template.yaml              # Auto-detect file type
```

### Built-in Tools

- **Terraform**: terraform, tflint, tfsec, checkov
- **CloudFormation**: cfn-lint, checkov, aws-cli
- **Azure**: azure-cli, bicep, arm-ttk
- **Security**: checkov, tfsec, trivy, detect-secrets
- **General**: git, jq, curl, wget

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
