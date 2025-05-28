# DevOps Universal Scanner - Test Files

This directory contains comprehensive test files for Infrastructure-as-Code (IaC) security scanning. Each file contains **intentional security vulnerabilities** for testing and validating the DevOps Universal Scanner's capabilities.

## 🚨 **WARNING: INTENTIONAL VULNERABILITIES**

**These files contain intentional security misconfigurations and should NEVER be used in production environments!** They are designed specifically for testing security scanning tools.

## Directory Structure

```
test-files/
├── cloudformation/          # AWS CloudFormation templates
├── terraform/              # Terraform configurations
├── azure-arm/              # Azure Resource Manager templates
├── azure-bicep/            # Azure Bicep templates
├── gcp-deployment-manager/ # Google Cloud Deployment Manager templates
└── README.md               # This documentation
```

## Test File Categories

### 🔧 CloudFormation Templates (`cloudformation/`)

#### `ec2-instance.yaml`
- **EC2 instances with security vulnerabilities**
- Issues: Unencrypted storage, overly permissive security groups, hardcoded credentials

#### `rds-database.json`
- **RDS database with security misconfigurations**
- Issues: Public access, weak passwords, no encryption, disabled monitoring

#### `s3-iam-vulnerable.json`
- **S3 and IAM security vulnerabilities**
- Issues: Public bucket access, overly permissive IAM policies, hardcoded credentials

#### `networking-vulnerable.yaml`
- **VPC and networking security issues**
- Issues: Overly permissive security groups, public subnets, wide-open network ACLs

### 🏗️ Terraform Configurations (`terraform/`)

#### `main.tf`
- **Multi-cloud infrastructure with security vulnerabilities**
- Issues: Hardcoded credentials, unencrypted resources, overly permissive access

#### `variables.tf`
- **Variable definitions with security issues**
- Issues: Sensitive data in defaults, no input validation, unprotected secrets

#### `outputs.tf`
- **Output definitions exposing sensitive information**
- Issues: Outputting credentials, connection strings, and sensitive infrastructure details

#### `providers.tf`
- **Provider configurations with security issues**
- Issues: Hardcoded credentials, no backend configuration, weak security settings

### ☁️ Azure ARM Templates (`azure-arm/`)

#### `vm-with-storage.json`
- **Virtual machine and storage with security vulnerabilities**
- Issues: Unencrypted storage, weak authentication, public access

#### `keyvault-sql-vulnerable.json`
- **Key Vault and SQL Database with security issues**
- Issues: Weak access policies, disabled features, public network access

### 🔷 Azure Bicep Templates (`azure-bicep/`)

#### `storage-account.bicep`
- **Storage account with security vulnerabilities**
- Issues: Public access, no encryption, weak TLS settings, sensitive metadata

#### `web-app.bicep`
- **Web application with security misconfigurations**
- Issues: HTTPS not enforced, hardcoded secrets, weak TLS, detailed error logging

### 🌐 GCP Deployment Manager (`gcp-deployment-manager/`)

#### `vulnerable-infrastructure.yaml`
- **GCP resources with security vulnerabilities**
- Issues: Overly permissive firewall rules, public storage, weak VM security

#### `vm-template.jinja`
- **Jinja2 template for VM instances with security issues**
- Issues: Default service accounts, no shielded VM, overly broad scopes

## Common Security Issues Tested

### 🔐 **Authentication & Authorization**
- Hardcoded credentials and API keys
- Weak passwords in default values
- Overly permissive IAM policies
- Default service accounts with broad permissions
- Missing multi-factor authentication

### 🌐 **Network Security**
- Security groups allowing 0.0.0.0/0 access
- Public subnets with auto-assign public IPs
- Missing VPC flow logs
- Overly permissive firewall rules
- No network segmentation

### 💾 **Data Protection**
- Unencrypted storage (at rest and in transit)
- Public read/write access to storage
- No backup encryption
- Disabled versioning
- No data lifecycle management

### 📊 **Monitoring & Logging**
- Disabled audit logging
- No security monitoring
- Missing vulnerability assessments
- No performance monitoring
- Disabled compliance checking

### 🔧 **Configuration Security**
- Sensitive information in tags
- Debug modes enabled in production
- Default configurations used
- No input validation
- Insecure communication protocols

### 📤 **Information Disclosure**
- Outputting sensitive data without protection
- Storing secrets in plain text
- Exposing connection strings
- Detailed error messages
- Sensitive information in comments

## Using These Test Files

### With DevOps Universal Scanner

```bash
# Scan Terraform files
docker run --rm -v ${PWD}/test-files:/work spd109/devops-uat:latest scan-terraform /work/terraform

# Scan CloudFormation files
docker run --rm -v ${PWD}/test-files:/work spd109/devops-uat:latest scan-cloudformation /work/cloudformation

# Results will include JSON reports with identified vulnerabilities
```

### Expected Security Findings

Each test file should trigger multiple security findings:

- **High Severity**: Hardcoded credentials, public access, disabled encryption
- **Medium Severity**: Weak configurations, missing monitoring, overly permissive access
- **Low Severity**: Missing tags, suboptimal configurations, informational issues

### Validation Checklist

When testing with security scanners, verify detection of:

- [ ] Hardcoded passwords and API keys
- [ ] Public storage bucket access
- [ ] Overly permissive security groups (0.0.0.0/0)
- [ ] Unencrypted storage and databases
- [ ] Disabled security monitoring
- [ ] Weak TLS/SSL configurations
- [ ] Missing backup and disaster recovery
- [ ] Sensitive data in outputs and tags
- [ ] Default service accounts with broad permissions
- [ ] Public IP assignment without justification

## Security Tools Integration

These test files are designed to work with popular security scanning tools:

### Cloud-Specific Tools
- **AWS**: AWS Config, Security Hub, GuardDuty, Inspector
- **Azure**: Security Center, Policy, Advisor
- **GCP**: Security Command Center, Cloud Asset Inventory

### Multi-Cloud Tools
- **Checkov**: Policy-as-code framework
- **TFSec**: Terraform security scanner
- **CFN-Lint**: CloudFormation linter
- **Trivy**: Container and IaC scanner
- **Bridgecrew**: Cloud security platform

## Contributing

When adding new test files:

1. Include a variety of security issues (high, medium, low severity)
2. Document the intentional vulnerabilities in comments
3. Follow the naming convention: `[service]-[type]-vulnerable.[ext]`
4. Update this README with descriptions of new test cases
5. Ensure files trigger findings in multiple security tools

## Disclaimer

⚠️ **SECURITY WARNING**: These files contain intentional security vulnerabilities and misconfigurations. They are for testing purposes only and should never be deployed to production environments. Use them responsibly and only in isolated testing environments.

## License

These test files are provided under the same license as the DevOps Universal Scanner project for educational and testing purposes only.
