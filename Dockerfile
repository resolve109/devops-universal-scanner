# Multi-stage build for smaller final image
FROM alpine:3.21.3 AS builder

# Install build dependencies in builder stage
RUN apk add --no-cache \
    python3-dev \
    py3-pip \
    gcc \
    musl-dev \
    linux-headers \
    git \
    curl \
    wget \
    unzip

# Create virtual environment to isolate dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install only essential Python packages with optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools>=75.0.0 && \
    pip install --no-cache-dir \
    cfn-lint==0.87.* \
    checkov==3.2.* \
    sympy \
    argcomplete \
    google-cloud-core==2.4.* \
    google-cloud-storage==2.10.* \
    google-api-python-client==2.108.* \
    azure-cli-core==2.55.* \
    asteval==0.9.31

# Download and extract binaries
WORKDIR /tmp

# Get Terraform
RUN TERRAFORM_VERSION=$(curl -s https://api.github.com/repos/hashicorp/terraform/releases/latest | grep tag_name | cut -d '"' -f 4 | cut -c 2-) && \
    wget -q https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    chmod +x terraform

# Get TFLint
RUN TFLINT_VERSION=$(curl -s https://api.github.com/repos/terraform-linters/tflint/releases/latest | grep tag_name | cut -d '"' -f 4 | cut -c 2-) && \
    wget -q https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_VERSION}/tflint_linux_amd64.zip && \
    unzip tflint_linux_amd64.zip && \
    chmod +x tflint

# Get TFSec  
RUN TFSEC_VERSION=$(curl -s "https://api.github.com/repos/aquasecurity/tfsec/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/') && \
    wget -q "https://github.com/aquasecurity/tfsec/releases/download/${TFSEC_VERSION}/tfsec-linux-amd64" && \
    mv tfsec-linux-amd64 tfsec && \
    chmod +x tfsec

# Get Bicep CLI
RUN wget -q https://github.com/Azure/bicep/releases/latest/download/bicep-linux-x64 && \
    mv bicep-linux-x64 bicep && \
    chmod +x bicep

# Get Trivy
RUN TRIVY_VERSION=$(curl -s https://api.github.com/repos/aquasecurity/trivy/releases/latest | grep tag_name | cut -d '"' -f 4 | cut -c 2-) && \
    wget -q https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz && \
    tar -xzf trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz && \
    chmod +x trivy

# Get kube-score (disabled for now)
RUN echo "Kube-score disabled temporarily" && \
    echo "#!/bin/bash\necho \"kube-score functionality temporarily disabled\"" > /tmp/kube-score && \
    chmod +x /tmp/kube-score

# Get Kubescape (disabled for now)
RUN echo "Kubescape disabled temporarily" && \
    echo "#!/bin/bash\necho \"kubescape functionality temporarily disabled\"" > /tmp/kubescape && \
    chmod +x /tmp/kubescape

# Final lightweight stage
FROM alpine:3.21.3

# Install only runtime dependencies (much smaller)
RUN apk add --no-cache \
    python3 \
    bash \
    curl \
    git \
    jq \
    nodejs \
    npm \
    ca-certificates \
    openssl

# Copy Python virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy compiled binaries from builder
COPY --from=builder /tmp/terraform /usr/local/bin/terraform
COPY --from=builder /tmp/tflint /usr/local/bin/tflint
COPY --from=builder /tmp/tfsec /usr/local/bin/tfsec
COPY --from=builder /tmp/bicep /usr/local/bin/bicep
COPY --from=builder /tmp/trivy /usr/local/bin/trivy
COPY --from=builder /tmp/kube-score /usr/local/bin/kube-score
COPY --from=builder /tmp/kubescape /usr/local/bin/kubescape

# Create directories for caching and update tracking
RUN mkdir -p /var/cache/devops-scanner /var/log/devops-scanner

# Copy scripts and helpers
COPY daily-update-manager.sh /usr/local/bin/daily-update-manager.sh
RUN chmod +x /usr/local/bin/daily-update-manager.sh

# Install minimal npm packages globally
RUN npm install -g --production \
    ip@latest \
    cross-spawn@latest \
    semver@latest \
    tar@latest

# Create minimal ARM-TTK (just the essential scripts)
RUN mkdir -p /opt/arm-ttk && \
    git clone --depth 1 --single-branch https://github.com/Azure/arm-ttk.git /opt/arm-ttk && \
    # Remove unnecessary files to save space
    rm -rf /opt/arm-ttk/.git /opt/arm-ttk/docs /opt/arm-ttk/unit-tests && \
    ln -s /opt/arm-ttk/arm-ttk/arm-ttk.sh /usr/local/bin/arm-ttk

# Create directory for scripts and tools
RUN mkdir -p /usr/local/bin/tools

# Copy scripts to the tools directory
COPY docker-tools-help.sh /usr/local/bin/tools/
COPY scanners/scan-terraform.sh /usr/local/bin/tools/
COPY scanners/scan-cloudformation.sh /usr/local/bin/tools/
COPY scanners/scan-docker.sh /usr/local/bin/tools/
COPY scanners/scan-arm.sh /usr/local/bin/tools/
COPY scanners/scan-bicep.sh /usr/local/bin/tools/
COPY scanners/scan-gcp.sh /usr/local/bin/tools/
COPY scanners/scan-kubernetes.sh /usr/local/bin/tools/
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
    chmod +x /usr/local/bin/tools/scan-kubernetes.sh && \
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
    ln -s /usr/local/bin/tools/scan-kubernetes.sh /usr/local/bin/scan-kubernetes && \
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
    echo '#!/bin/bash\ntrivy "$@"' > /usr/local/bin/tools/trivy-wrapper.sh && \
    echo '#!/bin/bash\nkube-score "$@"' > /usr/local/bin/tools/kube-score-wrapper.sh && \
    echo '#!/bin/bash\nkubescape "$@"' > /usr/local/bin/tools/kubescape-wrapper.sh && \
    chmod +x /usr/local/bin/tools/checkov-wrapper.sh && \
    chmod +x /usr/local/bin/tools/cfn-lint-wrapper.sh && \
    chmod +x /usr/local/bin/tools/terraform-wrapper.sh && \
    chmod +x /usr/local/bin/tools/tflint-wrapper.sh && \
    chmod +x /usr/local/bin/tools/tfsec-wrapper.sh && \
    chmod +x /usr/local/bin/tools/az-wrapper.sh && \
    chmod +x /usr/local/bin/tools/bicep-wrapper.sh && \
    chmod +x /usr/local/bin/tools/arm-ttk-wrapper.sh && \
    chmod +x /usr/local/bin/tools/trivy-wrapper.sh && \
    chmod +x /usr/local/bin/tools/kube-score-wrapper.sh && \
    chmod +x /usr/local/bin/tools/kubescape-wrapper.sh && \
    ln -s /usr/local/bin/tools/checkov-wrapper.sh /usr/local/bin/checkov-tool && \
    ln -s /usr/local/bin/tools/cfn-lint-wrapper.sh /usr/local/bin/cfn-lint-tool && \
    ln -s /usr/local/bin/tools/terraform-wrapper.sh /usr/local/bin/terraform-tool && \
    ln -s /usr/local/bin/tools/tflint-wrapper.sh /usr/local/bin/tflint-tool && \
    ln -s /usr/local/bin/tools/tfsec-wrapper.sh /usr/local/bin/tfsec-tool && \
    ln -s /usr/local/bin/tools/az-wrapper.sh /usr/local/bin/az-tool && \
    ln -s /usr/local/bin/tools/bicep-wrapper.sh /usr/local/bin/bicep-tool && \
    ln -s /usr/local/bin/tools/arm-ttk-wrapper.sh /usr/local/bin/arm-ttk-tool && \
    ln -s /usr/local/bin/tools/trivy-wrapper.sh /usr/local/bin/trivy-tool && \
    ln -s /usr/local/bin/tools/kube-score-wrapper.sh /usr/local/bin/kube-score-tool && \
    ln -s /usr/local/bin/tools/kubescape-wrapper.sh /usr/local/bin/kubescape-tool

# Set up a working directory
WORKDIR /work

# Make sure the work directory is writable
RUN chmod -R 777 /work

# Make the entrypoint executable
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Mark initial installation as complete to prevent unnecessary first-run updates
RUN echo "$(date +%Y-%m-%d)" > /var/cache/devops-scanner/last_update_timestamp && \
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Optimized installation completed with latest security patches" >> /var/log/devops-scanner/updates.log

# Set default entrypoint to our custom script
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Set CMD to show help if no arguments provided
CMD []