FROM ubuntu:22.04

# Set non-interactive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip git unzip jq nano curl wget gnupg2 software-properties-common apt-transport-https ca-certificates lsb-release && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js for various tools
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs

# Install AWS tools - always gets the latest versions
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir --upgrade --ignore-installed blinker \
    cfn-lint \
    checkov \
    aws-cdk-lib \
    boto3 \
    awscli \
    aws-sam-cli \
    detect-secrets

# Install Terraform
RUN TERRAFORM_VERSION=$(curl -s https://api.github.com/repos/hashicorp/terraform/releases/latest | grep tag_name | cut -d '"' -f 4 | cut -c 2-) && \
    wget -q https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /usr/local/bin && \
    rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip

# Install tflint
RUN curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# Install tfsec
RUN TFSEC_VERSION=$(curl -s "https://api.github.com/repos/aquasecurity/tfsec/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/') && \
    echo "Attempting to download tfsec version: ${TFSEC_VERSION}" && \
    wget -q "https://github.com/aquasecurity/tfsec/releases/download/${TFSEC_VERSION}/tfsec-linux-amd64" -O /usr/local/bin/tfsec && \
    chmod +x /usr/local/bin/tfsec

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install Bicep CLI
RUN curl -Lo bicep https://github.com/Azure/bicep/releases/latest/download/bicep-linux-x64 && \
    chmod +x ./bicep && \
    mv ./bicep /usr/local/bin/bicep

# Install ARM-TTK (ARM Template Toolkit)
RUN mkdir -p /opt/arm-ttk && \
    git clone --depth 1 https://github.com/Azure/arm-ttk.git /opt/arm-ttk && \
    ln -s /opt/arm-ttk/arm-ttk.sh /usr/local/bin/arm-ttk

# Install Google Cloud SDK
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && apt-get install -y google-cloud-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Trivy
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin v0.52.0

# Create a directory for scripts and tools
RUN mkdir -p /usr/local/bin/tools

# Copy scripts to the tools directory
COPY docker-tools-help.sh /usr/local/bin/tools/
COPY scan-terraform.sh /usr/local/bin/tools/
COPY scan-cloudformation.sh /usr/local/bin/tools/
COPY scan-docker.sh /usr/local/bin/tools/
COPY uat-setup.sh /usr/local/bin/tools/
COPY CONTAINER-README.md /usr/local/bin/tools/

# Create auto-detection script
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
    py)\n\
        # Check for AWS CDK\n\
        if grep -q "aws_cdk\\|Stack\\|construct" "$file_path"; then\n\
            echo "aws_cdk"\n\
            exit 0\n\
        fi\n\
        ;;\n\
    js|ts)\n\
        # Check for AWS CDK\n\
        if grep -q "aws-cdk\\|Stack\\|construct" "$file_path"; then\n\
            echo "aws_cdk"\n\
            exit 0\n\
        fi\n\
        # Check for Azure Pulumi\n\
        if grep -q "azure-native\\|pulumi" "$file_path"; then\n\
            echo "azure_pulumi"\n\
            exit 0\n\
        fi\n\
        # Check for GCP Pulumi\n\
        if grep -q "gcp\\|pulumi" "$file_path"; then\n\
            echo "gcp_pulumi"\n\
            exit 0\n\
        fi\n\
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
    chmod +x /usr/local/bin/tools/uat-setup.sh && \
    chmod +x /usr/local/bin/tools/auto-detect.sh

# Create symbolic links in /usr/local/bin for easier access
RUN ln -s /usr/local/bin/tools/docker-tools-help.sh /usr/local/bin/docker-tools-help && \
    ln -s /usr/local/bin/tools/scan-terraform.sh /usr/local/bin/scan-terraform && \
    ln -s /usr/local/bin/tools/scan-cloudformation.sh /usr/local/bin/scan-cloudformation && \
    ln -s /usr/local/bin/tools/scan-docker.sh /usr/local/bin/scan-docker && \
    ln -s /usr/local/bin/tools/uat-setup.sh /usr/local/bin/uat-setup && \
    ln -s /usr/local/bin/tools/auto-detect.sh /usr/local/bin/auto-detect

# Create update script with weekly caching
RUN echo '#!/bin/bash\n\
\n\
# Check if force update is requested\n\
FORCE_UPDATE=false\n\
if [ "$1" = "--force" ] || [ "$1" = "-f" ]; then\n\
    FORCE_UPDATE=true\n\
    echo "Force update requested."\n\
fi\n\
\n\
# Check if we need to update (once per week)\n\
UPDATE_CACHE_FILE="/tmp/.tool_update_cache"\n\
WEEK_IN_SECONDS=604800  # 7 days * 24 hours * 60 minutes * 60 seconds\n\
\n\
# Function to check if update is needed\n\
need_update() {\n\
    if [ "$FORCE_UPDATE" = true ]; then\n\
        return 0  # Force update requested\n\
    fi\n\
    \n\
    if [ ! -f "$UPDATE_CACHE_FILE" ]; then\n\
        return 0  # No cache file, need update\n\
    fi\n\
    \n\
    LAST_UPDATE=$(cat "$UPDATE_CACHE_FILE")\n\
    CURRENT_TIME=$(date +%s)\n\
    TIME_DIFF=$((CURRENT_TIME - LAST_UPDATE))\n\
    \n\
    if [ $TIME_DIFF -gt $WEEK_IN_SECONDS ]; then\n\
        return 0  # More than a week, need update\n\
    else\n\
        DAYS_LEFT=$(( (WEEK_IN_SECONDS - TIME_DIFF) / 86400 ))\n\
        echo "Tools were updated recently. Next update in $DAYS_LEFT days. (Use --force to update anyway)"\n\
        return 1  # Less than a week, skip update\n\
    fi\n\
}\n\
\n\
# Check if update is needed\n\
if need_update; then\n\
    echo "Updating tools to latest versions (weekly update)..."\n\
    \n\
    apt-get update > /dev/null 2>&1\n\
    apt-get install -y --only-upgrade google-cloud-cli nodejs > /dev/null 2>&1\n\
    pip3 install --no-cache-dir --upgrade pip checkov cfn-lint aws-cdk-lib boto3 awscli aws-sam-cli detect-secrets\n\
    \n\
    # Update tflint\n\
    curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash\n\
    \n\
    # Update terraform\n\
    TERRAFORM_VERSION=$(curl -s https://api.github.com/repos/hashicorp/terraform/releases/latest | grep tag_name | cut -d "\"" -f 4 | cut -c 2-)\n\
    CURRENT_VERSION=$(terraform version -json | grep "terraform_version" | cut -d "\"" -f 4)\n\
    \n\
    if [ "$TERRAFORM_VERSION" != "$CURRENT_VERSION" ]; then\n\
        echo "Updating Terraform from $CURRENT_VERSION to $TERRAFORM_VERSION"\n\
        wget -q https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip\n\
        unzip -o terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /usr/local/bin\n\
        rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip\n\
    fi\n\
    \n\
    # Update tfsec\n\
    TFSEC_VERSION=$(curl -s "https://api.github.com/repos/aquasecurity/tfsec/releases/latest" | grep '"tag_name":' | sed -E '\''s/.*"([^"]+)".*/\\1/'\'')\n\
    CURRENT_TFSEC_VERSION=$(tfsec --version || echo "v0.0.0")\n\
    if [ "$TFSEC_VERSION" != "$CURRENT_TFSEC_VERSION" ]; then\n\
        echo "Updating tfsec from $CURRENT_TFSEC_VERSION to $TFSEC_VERSION"\n\
        wget -q "https://github.com/aquasecurity/tfsec/releases/download/${TFSEC_VERSION}/tfsec-linux-amd64" -O /usr/local/bin/tfsec\n\
        chmod +x /usr/local/bin/tfsec\n\
    fi\n\
    \n\
    # Update Azure CLI\n\
    az upgrade --yes > /dev/null 2>&1 || true\n\
    \n\
    # Update Trivy\n\
    TRIVY_VERSION=$(curl -s "https://api.github.com/repos/aquasecurity/trivy/releases/latest" | grep '"tag_name":' | sed -E '\''s/.*"([^"]+)".*/\\1/'\'')\n\
    CURRENT_TRIVY_VERSION=$(trivy --version | head -n1 | awk '\''{print $2}'\'' || echo "v0.0.0")\n\
    if [ "$TRIVY_VERSION" != "$CURRENT_TRIVY_VERSION" ]; then\n\
        echo "Updating Trivy from $CURRENT_TRIVY_VERSION to $TRIVY_VERSION"\n\
        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin "$TRIVY_VERSION"\n\
    fi\n\
    \n\
    # Update ARM-TTK\n\
    cd /opt/arm-ttk && git pull\n\
    \n\
    # Update Bicep\n\
    curl -Lo bicep https://github.com/Azure/bicep/releases/latest/download/bicep-linux-x64\n\
    chmod +x ./bicep\n\
    mv ./bicep /usr/local/bin/bicep\n\
    \n\
    # Mark update as completed\n\
    echo $(date +%s) > "$UPDATE_CACHE_FILE"\n\
    echo "All tools updated to latest versions."\n\
else\n\
    echo "Skipping tool updates (already updated this week)."\n\
fi\n\
' > /usr/local/bin/tools/update-tools.sh && \
    chmod +x /usr/local/bin/tools/update-tools.sh && \
    ln -s /usr/local/bin/tools/update-tools.sh /usr/local/bin/update-tools

# Create cache status script
RUN echo '#!/bin/bash\n\
UPDATE_CACHE_FILE="/tmp/.tool_update_cache"\n\
WEEK_IN_SECONDS=604800\n\
\n\
if [ ! -f "$UPDATE_CACHE_FILE" ]; then\n\
    echo "No update cache found. Tools have never been updated."\n\
    echo "Run: update-tools"\n\
    exit 0\n\
fi\n\
\n\
LAST_UPDATE=$(cat "$UPDATE_CACHE_FILE")\n\
CURRENT_TIME=$(date +%s)\n\
TIME_DIFF=$((CURRENT_TIME - LAST_UPDATE))\n\
DAYS_SINCE=$((TIME_DIFF / 86400))\n\
DAYS_LEFT=$(( (WEEK_IN_SECONDS - TIME_DIFF) / 86400 ))\n\
\n\
LAST_UPDATE_DATE=$(date -d "@$LAST_UPDATE" "+%Y-%m-%d %H:%M:%S")\n\
\n\
echo "=== Tool Update Cache Status ==="\n\
echo "Last update: $LAST_UPDATE_DATE ($DAYS_SINCE days ago)"\n\
\n\
if [ $TIME_DIFF -gt $WEEK_IN_SECONDS ]; then\n\
    echo "Status: UPDATE NEEDED (overdue by $((DAYS_SINCE - 7)) days)"\n\
    echo "Next scheduled run will update tools."\n\
else\n\
    echo "Status: Up to date"\n\
    echo "Next update: in $DAYS_LEFT days"\n\
fi\n\
\n\
echo ""\n\
echo "Commands:"\n\
echo "  update-tools        # Update if needed (weekly check)"\n\
echo "  update-tools --force # Force update now"\n\
echo "  update-status       # Show this status"\n\
' > /usr/local/bin/tools/update-status.sh && \
    chmod +x /usr/local/bin/tools/update-status.sh && \
    ln -s /usr/local/bin/tools/update-status.sh /usr/local/bin/update-status

# Create intelligent validator script
RUN echo '#!/bin/bash\n\
\n\
# Intelligent validator script\n\
file_path="$1"\n\
output_file="${2:-validation-report.txt}"\n\
\n\
# Update tools\n\
update-tools\n\
\n\
# Detect file type\n\
file_type=$(auto-detect "$file_path")\n\
\n\
echo "===== VALIDATION REPORT: $(date) =====" > "$output_file"\n\
echo "File: $file_path" >> "$output_file"\n\
echo "Detected type: $file_type" >> "$output_file"\n\
echo "" >> "$output_file"\n\
\n\
# Run checkov on all file types (it supports multiple IaC frameworks)\n\
echo "===== CHECKOV SECURITY SCAN =====" | tee -a "$output_file"\n\
if [ -d "$file_path" ]; then\n\
    checkov -d "$file_path" --quiet | tee -a "$output_file"\n\
else\n\
    checkov -f "$file_path" --quiet | tee -a "$output_file"\n\
fi\n\
echo "" >> "$output_file"\n\
\n\
# Run specific tools based on detected type\n\
case "$file_type" in\n\
    aws_cloudformation)\n\
        echo "===== AWS CLOUDFORMATION VALIDATION =====" | tee -a "$output_file"\n\
        if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then\n\
            aws cloudformation validate-template --template-body file://"$file_path" | tee -a "$output_file"\n\
        else\n\
            echo "AWS credentials not available. Skipping AWS API validation." | tee -a "$output_file"\n\
        fi\n\
        echo "" >> "$output_file"\n\
        \n\
        echo "===== CFN-LINT VALIDATION =====" | tee -a "$output_file"\n\
        cfn-lint "$file_path" | tee -a "$output_file"\n\
        ;;\n\
    terraform_dir)\n\
        echo "===== TERRAFORM VALIDATION =====" | tee -a "$output_file"\n\
        cd "$file_path" && terraform init -backend=false | tee -a "$output_file"\n\
        cd "$file_path" && terraform validate | tee -a "$output_file"\n\
        echo "" >> "$output_file"\n\
        \n\
        echo "===== TFLINT VALIDATION =====" | tee -a "$output_file"\n\
        cd "$file_path" && tflint | tee -a "$output_file"\n\
        echo "" >> "$output_file"\n\
        \n\
        echo "===== TFSEC SECURITY SCAN =====" | tee -a "$output_file"\n\
        tfsec "$file_path" --no-color | tee -a "$output_file"\n\
        ;;\n\
    terraform_file)\n\
        dir_path="$(dirname "$file_path")"\n\
        echo "===== TERRAFORM VALIDATION =====" | tee -a "$output_file"\n\
        cd "$dir_path" && terraform init -backend=false | tee -a "$output_file"\n\
        cd "$dir_path" && terraform validate | tee -a "$output_file"\n\
        echo "" >> "$output_file"\n\
        \n\
        echo "===== TFLINT VALIDATION =====" | tee -a "$output_file"\n\
        cd "$dir_path" && tflint | tee -a "$output_file"\n\
        echo "" >> "$output_file"\n\
        \n\
        echo "===== TFSEC SECURITY SCAN =====" | tee -a "$output_file"\n\
        tfsec "$dir_path" --no-color | tee -a "$output_file"\n\
        ;;\n\
    azure_arm)\n\
        echo "===== AZURE ARM VALIDATION =====" | tee -a "$output_file"\n\
        if [ -n "$AZURE_SUBSCRIPTION_ID" ]; then\n\
            az deployment group validate --template-file "$file_path" --resource-group DummyResourceGroup | tee -a "$output_file"\n\
        else\n\
            echo "Azure credentials not available. Skipping Azure API validation." | tee -a "$output_file"\n\
        fi\n\
        echo "" >> "$output_file"\n\
        \n\
        echo "===== ARM-TTK VALIDATION =====" | tee -a "$output_file"\n\
        arm-ttk "$file_path" | tee -a "$output_file"\n\
        ;;\n\
    azure_bicep)\n\
        echo "===== AZURE BICEP VALIDATION =====" | tee -a "$output_file"\n\
        bicep build "$file_path" | tee -a "$output_file"\n\
        ;;\n\
    gcp_deployment_manager)\n\
        echo "===== GCP DEPLOYMENT MANAGER VALIDATION =====" | tee -a "$output_file"\n\
        if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then\n\
            gcloud deployment-manager deployments validate --config="$file_path" --project=dummy-project | tee -a "$output_file"\n\
        else\n\
            echo "GCP credentials not available. Skipping GCP API validation." | tee -a "$output_file"\n\
        fi\n\
        ;;\n\
    aws_cdk)\n\
        echo "===== AWS CDK VALIDATION =====" | tee -a "$output_file"\n\
        dir_path="$(dirname "$file_path")"\n\
        cd "$dir_path" && cdk synth | tee -a "$output_file"\n\
        ;;\n\
    unknown|unknown_dir)\n\
        echo "Unknown file type. Running basic validations only." | tee -a "$output_file"\n\
        ;;\n\
esac\n\
\n\
# Run detect-secrets on all files\n\
echo "===== SECRETS DETECTION =====" | tee -a "$output_file"\n\
if [ -d "$file_path" ]; then\n\
    detect-secrets scan "$file_path" | tee -a "$output_file"\n\
else\n\
    detect-secrets scan "$file_path" | tee -a "$output_file"\n\
fi\n\
echo "" >> "$output_file"\n\
\n\
# Run Trivy security scan\n\
echo "===== TRIVY SECURITY SCAN =====" | tee -a "$output_file"\n\
if [ -d "$file_path" ]; then\n\
    trivy config "$file_path" --format table | tee -a "$output_file"\n\
else\n\
    trivy config "$file_path" --format table | tee -a "$output_file"\n\
fi\n\
echo "" >> "$output_file"\n\
\n\
echo "===== VALIDATION COMPLETE =====" | tee -a "$output_file"\n\
echo "Full report available in: $output_file"\n\
' > /usr/local/bin/tools/smart-validate.sh && \
chmod +x /usr/local/bin/tools/smart-validate.sh && \
ln -s /usr/local/bin/tools/smart-validate.sh /usr/local/bin/smart-validate

# Create wrapper scripts for direct tool execution
RUN echo '#!/bin/bash\ncheckov "$@"' > /usr/local/bin/tools/checkov-wrapper.sh && \
    echo '#!/bin/bash\ncfn-lint "$@"' > /usr/local/bin/tools/cfn-lint-wrapper.sh && \
    echo '#!/bin/bash\naws "$@"' > /usr/local/bin/tools/aws-wrapper.sh && \
    echo '#!/bin/bash\ncdk "$@"' > /usr/local/bin/tools/cdk-wrapper.sh && \
    echo '#!/bin/bash\nsam "$@"' > /usr/local/bin/tools/sam-wrapper.sh && \
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
    chmod +x /usr/local/bin/tools/aws-wrapper.sh && \
    chmod +x /usr/local/bin/tools/cdk-wrapper.sh && \
    chmod +x /usr/local/bin/tools/sam-wrapper.sh && \
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
    ln -s /usr/local/bin/tools/aws-wrapper.sh /usr/local/bin/aws-tool && \
    ln -s /usr/local/bin/tools/cdk-wrapper.sh /usr/local/bin/cdk-tool && \
    ln -s /usr/local/bin/tools/sam-wrapper.sh /usr/local/bin/sam-tool && \
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

# Set default entrypoint to use bash shell
ENTRYPOINT ["/bin/bash"]

# Set CMD to run the helper script if no arguments provided
CMD ["/usr/local/bin/docker-tools-help"]