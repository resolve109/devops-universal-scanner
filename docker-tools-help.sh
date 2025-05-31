#!/bin/bash
# Helper script to display usage information for the container tools

cat << EOF
DevOps Universal Scanner - Multi-Cloud Infrastructure Validation

====== SMART VALIDATION ======
Auto-detects file type and runs appropriate validation tools:

  smart-validate <file_or_directory> [output_file]
  
  Examples:
  - smart-validate template.yaml                   # Auto-detects and validates any IaC file
  - smart-validate terraform/                      # Validates a Terraform directory
  - smart-validate arm-template.json report.txt    # Validates an ARM template and saves to report.txt

====== MANUAL VALIDATION TOOLS ======

AWS Tools:
  - checkov-tool -f <file>                # Multi-cloud security scanner
  - cfn-lint-tool <file>                  # CloudFormation linter
  - aws-tool cloudformation validate-template --template-body file://<file>
  - cdk-tool synth                        # AWS CDK synthesis
  - sam-tool validate --template <file>   # AWS SAM validation

Azure Tools:
  - az-tool deployment group validate --template-file <file>  # Azure deployment validation
  - bicep-tool build <file>               # Bicep validation
  - arm-ttk-tool <file>                   # ARM Template Toolkit validation

GCP Tools:
  - gcloud-tool deployment-manager deployments validate --config=<file>

Terraform Tools:
  - terraform-tool validate                # Terraform validation
  - tflint-tool                           # Terraform linter
  - tfsec-tool <directory>                # Terraform security scanner

Security Tools:
  - snyk-tool iac test <file>             # Snyk security scanner
  - detect-secrets scan <file>            # Secrets detection
  - kube-score-tool <file>               # Kubernetes best-practice analysis
  - kubescape-tool scan <path>           # Kubernetes security scanning

Utility Commands:
  - update-tools                          # Updates all tools to latest versions
  - auto-detect <file>                    # Detects file type and cloud provider

====== LEGACY TOOLS ======
  - uat-setup setup                                 # Environment setup and validation
  - uat-setup scan-tf <directory>                   # Terraform scan with logging
  - uat-setup scan-cf <file>                        # CloudFormation scan with logging
  - auto-detect <file>                              # Auto-detect file type

For more detailed help on each tool:
  - Run any tool with --help flag (e.g., checkov-tool --help)
  - Run uat-setup --help for full setup options

To use these tools with your files, mount a volume to /work:
docker run -v /path/to/your/files:/work devops-universal-scanner:latest smart-validate mytemplate.yaml
EOF
