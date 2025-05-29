FROM alpine:3.21.3

# Install essential build and runtime dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl \
    bash \
    git \
    unzip \
    wget \
    ca-certificates \
    gnupg \
    nodejs \
    npm \
    jq \
    openssl \
    file

# Create directories for caching and update tracking
RUN mkdir -p /var/cache/devops-scanner /var/log/devops-scanner

# Copy the daily update manager script first
COPY daily-update-manager.sh /usr/local/bin/daily-update-manager.sh
RUN chmod +x /usr/local/bin/daily-update-manager.sh

# Update setuptools first to fix CVE-2025-47273 (requires setuptools >= 70.4.0)
# Install essential Python tools with security-focused versions
RUN pip3 install --no-cache-dir --break-system-packages --upgrade pip setuptools>=75.0.0 && \
    pip3 install --no-cache-dir --break-system-packages --upgrade \
    cfn-lint \
    checkov \
    asteval \
    google-cloud-core \
    google-cloud-storage \
    google-api-python-client

# Install/update npm packages globally - always use latest versions for security
RUN npm install -g \
    ip@latest \
    cross-spawn@latest \
    semver@latest \
    tar@latest

# Install Terraform (use latest to get newer Go stdlib)
RUN TERRAFORM_VERSION=$(curl -s https://api.github.com/repos/hashicorp/terraform/releases/latest | grep tag_name | cut -d '"' -f 4 | cut -c 2-) && \
    wget -q https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /usr/local/bin && \
    rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip

# Install tflint (latest version to get newer Go stdlib)
RUN curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# Install tfsec (latest version, though deprecated in favor of Trivy)
RUN TFSEC_VERSION=$(curl -s "https://api.github.com/repos/aquasecurity/tfsec/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/') && \
    wget -q "https://github.com/aquasecurity/tfsec/releases/download/${TFSEC_VERSION}/tfsec-linux-amd64" -O /usr/local/bin/tfsec && \
    chmod +x /usr/local/bin/tfsec

# Install minimal Azure CLI and build tools
RUN apk add --no-cache \
    gcc \
    python3-dev \
    musl-dev \
    linux-headers \
    && pip3 install --no-cache-dir --break-system-packages azure-cli-core \
    && apk del gcc python3-dev musl-dev linux-headers

# Install Bicep CLI (always latest release)
RUN curl -Lo bicep https://github.com/Azure/bicep/releases/latest/download/bicep-linux-x64 && \
    chmod +x ./bicep && \
    mv ./bicep /usr/local/bin/bicep

# Install ARM-TTK (ARM Template Toolkit) - latest from main branch
RUN mkdir -p /opt/arm-ttk && \
    git clone --depth 1 https://github.com/Azure/arm-ttk.git /opt/arm-ttk && \
    ln -s /opt/arm-ttk/arm-ttk.sh /usr/local/bin/arm-ttk

# Install minimal Google Cloud libraries for GCP Deployment Manager - latest versions
RUN pip3 install --no-cache-dir --break-system-packages --upgrade \
    google-cloud-core \
    google-cloud-storage \
    google-api-python-client && \
    mkdir -p /usr/local/bin/gcloud && \
    ln -s /usr/bin/python3 /usr/local/bin/python

# Install Trivy (latest version with newer Go stdlib to fix CVEs)
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin latest

# Create a directory for scripts and tools
RUN mkdir -p /usr/local/bin/tools

# Copy scripts to the tools directory
COPY docker-tools-help.sh /usr/local/bin/tools/
COPY scanners/scan-terraform.sh /usr/local/bin/tools/
COPY scanners/scan-cloudformation.sh /usr/local/bin/tools/
COPY scanners/scan-docker.sh /usr/local/bin/tools/
COPY scanners/scan-arm.sh /usr/local/bin/tools/
COPY scanners/scan-bicep.sh /usr/local/bin/tools/
COPY scanners/scan-gcp.sh /usr/local/bin/tools/
COPY uat-setup.sh /usr/local/bin/tools/

# Copy the Docker entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# Copy helper modules
COPY helpers/ /usr/local/bin/helpers/

# Create auto-detection script (simplified)
RUN echo '#!/bin/bash\n\
\n\
# Script to auto-detect file type and cloud provider\n\
file_path="$1"\n\
dir_path="$(dirname "$file_path")"\n\
\n\
# Check if path is a directory\n\
if [ -d "$file_path" ]; then\n\
    # Check for terraform files\n\
    if ls "$file_path"/*.tf 1> /dev/null 2>&1; then\n\
        echo "terraform_dir"\n\
        exit 0\n\
    fi\n\
    echo "unknown_dir"\n\
    exit 1\n\
fi\n\
\n\
# Get file extension\n\
extension="${file_path##*.}"\n\
\n\
# Check for terraform files in the same directory\n\
if ls "$dir_path"/*.tf 1> /dev/null 2>&1; then\n\
    echo "terraform_file"\n\
    exit 0\n\
fi\n\
\n\
# Check based on extension\n\
case "$extension" in\n\
    yaml|yml)\n\
        # Check for AWS CloudFormation\n\
        if grep -q "AWSTemplateFormatVersion\\|Resources:" "$file_path"; then\n\
            echo "aws_cloudformation"\n\
            exit 0\n\
        fi\n\
        # Check for GCP deployment manager\n\
        if grep -q "resources:" "$file_path" && grep -q "type: .*gcp\\|google" "$file_path"; then\n\
            echo "gcp_deployment_manager"\n\
            exit 0\n\
        fi\n\
        ;;\n\
    json)\n\
        # Check for AWS CloudFormation\n\
        if grep -q "AWSTemplateFormatVersion\\|Resources" "$file_path"; then\n\
            echo "aws_cloudformation"\n\
            exit 0\n\
        fi\n\
        # Check for Azure ARM template\n\
        if grep -q "\\$schema.*deploymentTemplate.json\\|resources" "$file_path"; then\n\
            echo "azure_arm"\n\
            exit 0\n\
        fi\n\
        ;;\n\
    bicep)\n\
        echo "azure_bicep"\n\
        exit 0\n\
        ;;\n\
    tf)\n\
        echo "terraform_file"\n\
        exit 0\n\
        ;;\n\
esac\n\
\n\
echo "unknown"\n\
exit 1\n\
' > /usr/local/bin/tools/auto-detect.sh

# Make scripts executable
RUN chmod +x /usr/local/bin/tools/docker-tools-help.sh && \
    chmod +x /usr/local/bin/tools/scan-terraform.sh && \
    chmod +x /usr/local/bin/tools/scan-cloudformation.sh && \
    chmod +x /usr/local/bin/tools/scan-docker.sh && \
    chmod +x /usr/local/bin/tools/scan-arm.sh && \
    chmod +x /usr/local/bin/tools/scan-bicep.sh && \
    chmod +x /usr/local/bin/tools/scan-gcp.sh && \
    chmod +x /usr/local/bin/tools/uat-setup.sh && \
    chmod +x /usr/local/bin/tools/auto-detect.sh

# Create symbolic links in /usr/local/bin for easier access
RUN ln -s /usr/local/bin/tools/docker-tools-help.sh /usr/local/bin/docker-tools-help && \
    ln -s /usr/local/bin/tools/scan-terraform.sh /usr/local/bin/scan-terraform && \
    ln -s /usr/local/bin/tools/scan-cloudformation.sh /usr/local/bin/scan-cloudformation && \
    ln -s /usr/local/bin/tools/scan-docker.sh /usr/local/bin/scan-docker && \
    ln -s /usr/local/bin/tools/scan-arm.sh /usr/local/bin/scan-azure-arm && \
    ln -s /usr/local/bin/tools/scan-bicep.sh /usr/local/bin/scan-azure-bicep && \
    ln -s /usr/local/bin/tools/scan-gcp.sh /usr/local/bin/scan-gcp && \
    ln -s /usr/local/bin/tools/uat-setup.sh /usr/local/bin/uat-setup && \
    ln -s /usr/local/bin/tools/auto-detect.sh /usr/local/bin/auto-detect

# Create essential wrapper scripts for direct tool execution
RUN echo '#!/bin/bash\ncheckov "$@"' > /usr/local/bin/tools/checkov-wrapper.sh && \
    echo '#!/bin/bash\ncfn-lint "$@"' > /usr/local/bin/tools/cfn-lint-wrapper.sh && \
    echo '#!/bin/bash\nterraform "$@"' > /usr/local/bin/tools/terraform-wrapper.sh && \
    echo '#!/bin/bash\ntflint "$@"' > /usr/local/bin/tools/tflint-wrapper.sh && \
    echo '#!/bin/bash\ntfsec "$@"' > /usr/local/bin/tools/tfsec-wrapper.sh && \
    echo '#!/bin/bash\naz "$@"' > /usr/local/bin/tools/az-wrapper.sh && \
    echo '#!/bin/bash\nbicep "$@"' > /usr/local/bin/tools/bicep-wrapper.sh && \
    echo '#!/bin/bash\narm-ttk "$@"' > /usr/local/bin/tools/arm-ttk-wrapper.sh && \
    echo '#!/bin/bash\ngcloud "$@"' > /usr/local/bin/tools/gcloud-wrapper.sh && \
    echo '#!/bin/bash\ntrivy "$@"' > /usr/local/bin/tools/trivy-wrapper.sh && \
    chmod +x /usr/local/bin/tools/checkov-wrapper.sh && \
    chmod +x /usr/local/bin/tools/cfn-lint-wrapper.sh && \
    chmod +x /usr/local/bin/tools/terraform-wrapper.sh && \
    chmod +x /usr/local/bin/tools/tflint-wrapper.sh && \
    chmod +x /usr/local/bin/tools/tfsec-wrapper.sh && \
    chmod +x /usr/local/bin/tools/az-wrapper.sh && \
    chmod +x /usr/local/bin/tools/bicep-wrapper.sh && \
    chmod +x /usr/local/bin/tools/arm-ttk-wrapper.sh && \
    chmod +x /usr/local/bin/tools/gcloud-wrapper.sh && \
    chmod +x /usr/local/bin/tools/trivy-wrapper.sh && \
    ln -s /usr/local/bin/tools/checkov-wrapper.sh /usr/local/bin/checkov-tool && \
    ln -s /usr/local/bin/tools/cfn-lint-wrapper.sh /usr/local/bin/cfn-lint-tool && \
    ln -s /usr/local/bin/tools/terraform-wrapper.sh /usr/local/bin/terraform-tool && \
    ln -s /usr/local/bin/tools/tflint-wrapper.sh /usr/local/bin/tflint-tool && \
    ln -s /usr/local/bin/tools/tfsec-wrapper.sh /usr/local/bin/tfsec-tool && \
    ln -s /usr/local/bin/tools/az-wrapper.sh /usr/local/bin/az-tool && \
    ln -s /usr/local/bin/tools/bicep-wrapper.sh /usr/local/bin/bicep-tool && \
    ln -s /usr/local/bin/tools/arm-ttk-wrapper.sh /usr/local/bin/arm-ttk-tool && \
    ln -s /usr/local/bin/tools/gcloud-wrapper.sh /usr/local/bin/gcloud-tool && \
    ln -s /usr/local/bin/tools/trivy-wrapper.sh /usr/local/bin/trivy-tool

# Set up a working directory
WORKDIR /work

# Make sure the work directory is writable
RUN chmod -R 777 /work

# Make the entrypoint executable
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Mark initial installation as complete to prevent unnecessary first-run updates
RUN echo "$(date +%Y-%m-%d)" > /var/cache/devops-scanner/last_update_timestamp && \
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Initial installation completed with latest security patches" >> /var/log/devops-scanner/updates.log

# Set default entrypoint to our custom script
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Set CMD to show help if no arguments provided
CMD []