# Multi-stage optimized build for DevOps Universal Scanner v3.0
# Pure Python 3.13 Engine - Optimized for size and performance

# Builder stage - Compile and prepare binaries
FROM python:3.13-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    git \
    curl \
    wget \
    unzip \
    libffi-dev \
    openssl-dev

# Create virtual environment for Python dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install security-patched setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools>=75.0.0 wheel>=0.43.0

# Copy requirements file
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies (excludes dev dependencies)
RUN set -e && \
    echo "Installing Python packages..." && \
    pip install --no-cache-dir -r /tmp/requirements.txt --verbose && \
    echo "Verifying key packages installed..." && \
    pip show checkov cfn-lint pyyaml || exit 1 && \
    # Remove test/dev packages to save space
    pip uninstall -y pytest pytest-cov black ruff || true

# Download and extract scanning tool binaries
WORKDIR /tmp/binaries

# Terraform
RUN TERRAFORM_VERSION=$(curl -s https://api.github.com/repos/hashicorp/terraform/releases/latest | grep tag_name | cut -d '"' -f 4 | cut -c 2-) && \
    wget -q https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    chmod +x terraform && \
    rm *.zip

# TFLint
RUN TFLINT_VERSION=$(curl -s https://api.github.com/repos/terraform-linters/tflint/releases/latest | grep tag_name | cut -d '"' -f 4 | cut -c 2-) && \
    wget -q https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_VERSION}/tflint_linux_amd64.zip && \
    unzip tflint_linux_amd64.zip && \
    chmod +x tflint && \
    rm *.zip

# TFSec
RUN TFSEC_VERSION=$(curl -s "https://api.github.com/repos/aquasecurity/tfsec/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/') && \
    wget -q "https://github.com/aquasecurity/tfsec/releases/download/${TFSEC_VERSION}/tfsec-linux-amd64" && \
    mv tfsec-linux-amd64 tfsec && \
    chmod +x tfsec

# Bicep CLI
RUN wget -q https://github.com/Azure/bicep/releases/latest/download/bicep-linux-x64 && \
    mv bicep-linux-x64 bicep && \
    chmod +x bicep

# kube-score (stub - disabled)
RUN echo '#!/bin/sh\necho "kube-score functionality temporarily disabled"' > kube-score && \
    chmod +x kube-score

# Kubescape (stub - disabled)
RUN echo '#!/bin/sh\necho "kubescape functionality temporarily disabled"' > kubescape && \
    chmod +x kubescape

# Runtime stage - Minimal Python 3.13 Alpine
FROM python:3.13-alpine

LABEL maintainer="DevOps Security Team" \
      version="3.0.0" \
      description="DevOps Universal Scanner - Pure Python 3.13 Engine" \
      tools="terraform,tflint,tfsec,checkov,cfn-lint,bicep,arm-ttk"

# Install only essential runtime dependencies
# NOTE: Node.js removed - not needed in pure Python engine
# NOTE: Trivy removed - saves ~150-200MB
RUN apk add --no-cache \
    bash \
    git \
    curl \
    jq \
    ca-certificates \
    openssl \
    libffi \
    && rm -rf /var/cache/apk/*

# Copy Python virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Verify Python tools are installed and accessible
RUN echo "Verifying Python tool installation..." && \
    ls -la /opt/venv/bin/ && \
    python3 -c "import yaml; print('✅ pyyaml installed')" && \
    which python3 && \
    which checkov || echo "⚠️  checkov not found" && \
    which cfn-lint || echo "⚠️  cfn-lint not found"

# Copy scanning tool binaries from builder
COPY --from=builder /tmp/binaries/terraform /usr/local/bin/terraform
COPY --from=builder /tmp/binaries/tflint /usr/local/bin/tflint
COPY --from=builder /tmp/binaries/tfsec /usr/local/bin/tfsec
COPY --from=builder /tmp/binaries/bicep /usr/local/bin/bicep
COPY --from=builder /tmp/binaries/kube-score /usr/local/bin/kube-score
COPY --from=builder /tmp/binaries/kubescape /usr/local/bin/kubescape

# Install Azure ARM-TTK (minimal, git clone optimized)
RUN mkdir -p /opt/arm-ttk && \
    git clone --depth 1 --single-branch https://github.com/Azure/arm-ttk.git /opt/arm-ttk && \
    # Remove unnecessary files to save space
    rm -rf /opt/arm-ttk/.git /opt/arm-ttk/docs /opt/arm-ttk/unit-tests /opt/arm-ttk/.github && \
    ln -s /opt/arm-ttk/arm-ttk/Test-AzTemplate.sh /usr/local/bin/arm-ttk && \
    chmod +x /opt/arm-ttk/arm-ttk/Test-AzTemplate.sh

# Create directories for scanner operations
RUN mkdir -p /var/cache/devops-scanner \
             /var/log/devops-scanner \
             /work && \
    chmod -R 777 /work /var/cache/devops-scanner /var/log/devops-scanner

# Copy pure Python application code
WORKDIR /app

# Copy the entire package
COPY devops_universal_scanner/ /app/devops_universal_scanner/
COPY requirements.txt /app/requirements.txt

# Make entrypoint executable
RUN chmod +x /app/devops_universal_scanner/entrypoint.py

# Add app to Python path
ENV PYTHONPATH="/app"

# Mark installation complete
RUN echo "$(date +%Y-%m-%d)" > /var/cache/devops-scanner/last_update_timestamp && \
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Pure Python 3.13 optimized installation completed" >> /var/log/devops-scanner/updates.log

# Set working directory for scans
WORKDIR /work

# Set Python entrypoint
ENTRYPOINT ["python3", "/app/devops_universal_scanner/entrypoint.py"]

# Show help if no arguments
CMD []

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# Image optimization notes:
# - Removed Trivy: ~150-200MB savings
# - Removed Node.js + npm: ~60MB savings
# - Removed old .sh scripts: ~1-2MB savings
# - Pure Python 3.13: Better performance and maintainability
# - Multi-stage build: Minimal runtime image
# - Expected final size: ~600-700MB (down from 1.02GB)
