#!/bin/bash
# UAT Setup Script - Environment setup and validation runner
# Usage: uat-setup.sh [options] [command] [target]

set -e

# Default settings
VERBOSE=false
CHECK_TOOLS=false
AWS_PROFILE=""
LOG_DIR="/work/logs"

# Function to show help
show_help() {
    echo "UAT Setup Script - DevOps Universal Scanner"
    echo ""
    echo "Usage: uat-setup.sh [options] [command] [target]"
    echo ""
    echo "Commands:"
    echo "  setup                   Setup environment and validate tools"
    echo "  scan-tf <directory>     Run Terraform scan on directory"
    echo "  scan-cf <file>          Run CloudFormation scan on file"
    echo "  check-aws              Check AWS credentials and connectivity"
    echo "  check-tools            Verify all tools are installed and working"
    echo ""
    echo "Options:"
    echo "  -h, --help             Show this help message"
    echo "  -v, --verbose          Enable verbose output"
    echo "  -p, --profile <name>   AWS profile to use"
    echo "  -l, --log-dir <dir>    Directory for log files (default: /work/logs)"
    echo "  --check-tools          Verify tools before running"
    echo ""
    echo "Examples:"
    echo "  uat-setup.sh setup                    # Basic environment setup"
    echo "  uat-setup.sh scan-tf terraform        # Scan terraform directory"
    echo "  uat-setup.sh scan-cf S3.yaml          # Scan CloudFormation file"
    echo "  uat-setup.sh -p myprofile scan-cf template.yaml"
    echo ""
    exit 0
}

# Function for verbose logging
log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo "[DEBUG] $1"
    fi
}

# Function to log with timestamp
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to setup logging directory
setup_logging() {
    log_verbose "Setting up log directory: $LOG_DIR"
    mkdir -p "$LOG_DIR"
    chmod 777 "$LOG_DIR" 2>/dev/null || true
    
    if [ ! -w "$LOG_DIR" ]; then
        echo "Warning: Cannot write to log directory $LOG_DIR, using /tmp"
        LOG_DIR="/tmp"
    fi
}

# Function to check tool versions
check_tools() {
    log_info "Checking tool versions..."
    
    local tools_ok=true
    
    # Core tools
    if command_exists aws; then
        echo "✅ AWS CLI: $(aws --version 2>&1 | head -n1)"
    else
        echo "❌ AWS CLI not found"
        tools_ok=false
    fi
    
    if command_exists cfn-lint; then
        echo "✅ cfn-lint: $(cfn-lint --version 2>&1)"
    else
        echo "❌ cfn-lint not found"
        tools_ok=false
    fi
    
    if command_exists checkov; then
        echo "✅ checkov: $(checkov --version 2>&1)"
    else
        echo "❌ checkov not found"
        tools_ok=false
    fi
    
    if command_exists terraform; then
        echo "✅ terraform: $(terraform version | head -n1)"
    else
        echo "❌ terraform not found"
        tools_ok=false
    fi
    
    if command_exists tflint; then
        echo "✅ tflint: $(tflint --version 2>&1)"
    else
        echo "❌ tflint not found"
        tools_ok=false
    fi
    
    if command_exists tfsec; then
        echo "✅ tfsec: $(tfsec --version 2>&1)"
    else
        echo "❌ tfsec not found"
        tools_ok=false
    fi
    
    # Optional tools
    if command_exists cdk; then
        echo "✅ AWS CDK: $(cdk --version 2>&1)"
    else
        echo "ℹ️  AWS CDK not available (optional)"
    fi
    
    if [ "$tools_ok" = false ]; then
        echo ""
        echo "❌ Some required tools are missing. Please check the container setup."
        exit 1
    fi
    
    echo ""
    echo "✅ All required tools are available"
}

# Function to check AWS credentials
check_aws() {
    log_info "Checking AWS credentials..."
    
    # Set AWS profile if specified
    if [ -n "$AWS_PROFILE" ]; then
        export AWS_PROFILE="$AWS_PROFILE"
        log_verbose "Using AWS profile: $AWS_PROFILE"
    fi
    
    # Check credentials in order of precedence
    if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
        echo "✅ Using AWS credentials from environment variables"
        if aws sts get-caller-identity >/dev/null 2>&1; then
            echo "✅ AWS credentials are valid"
            aws sts get-caller-identity
        else
            echo "❌ AWS credentials are invalid"
            return 1
        fi
    elif [ -n "$AWS_PROFILE" ]; then
        echo "✅ Using AWS profile: $AWS_PROFILE"
        if aws sts get-caller-identity >/dev/null 2>&1; then
            echo "✅ AWS profile credentials are valid"
            aws sts get-caller-identity
        else
            echo "❌ AWS profile credentials are invalid"
            return 1
        fi
    else
        echo "ℹ️  No AWS credentials configured"
        echo "   - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, or"
        echo "   - Use --profile option, or"
        echo "   - Configure AWS credentials in the container"
        return 1
    fi
}

# Function to run environment setup
run_setup() {
    log_info "Running UAT environment setup..."
    
    # Ensure we're in the work directory
    cd /work
    log_verbose "Working directory: $(pwd)"
    
    # Setup logging
    setup_logging
    
    # Check tools if requested
    if [ "$CHECK_TOOLS" = true ]; then
        check_tools
    fi
    
    # Check AWS (non-fatal)
    echo ""
    if ! check_aws; then
        echo "⚠️  AWS validation will be skipped during scans"
    fi
    
    echo ""
    log_info "✅ UAT setup complete!"
    echo ""
    echo "Available commands:"
    echo "  - scan-terraform <directory>     # Scan Terraform files"
    echo "  - scan-cloudformation <file>     # Scan CloudFormation files"
    echo ""
}

# Function to run Terraform scan with logging
run_terraform_scan() {
    local target="$1"
    if [ -z "$target" ]; then
        echo "Error: No target specified for Terraform scan"
        echo "Usage: uat-setup.sh scan-tf <directory>"
        exit 1
    fi
    
    setup_logging
    local log_file="$LOG_DIR/terraform-scan-$(date +%Y%m%d-%H%M%S).log"
    
    log_info "Running Terraform scan on: $target"
    log_info "Log file: $log_file"
    
    echo "====== TERRAFORM SCAN REPORT: $(date) ======" > "$log_file"
    echo "Target: $target" >> "$log_file"
    echo "" >> "$log_file"
    
    # Run the scan and capture output
    if scan-terraform "$target" 2>&1 | tee -a "$log_file"; then
        log_info "✅ Terraform scan completed successfully"
    else
        log_info "⚠️  Terraform scan completed with warnings/errors"
    fi
    
    log_info "Full results saved to: $log_file"
}

# Function to run CloudFormation scan with logging
run_cloudformation_scan() {
    local target="$1"
    if [ -z "$target" ]; then
        echo "Error: No target specified for CloudFormation scan"
        echo "Usage: uat-setup.sh scan-cf <file>"
        exit 1
    fi
    
    setup_logging
    local log_file="$LOG_DIR/cloudformation-scan-$(date +%Y%m%d-%H%M%S).log"
    
    log_info "Running CloudFormation scan on: $target"
    log_info "Log file: $log_file"
    
    echo "====== CLOUDFORMATION SCAN REPORT: $(date) ======" > "$log_file"
    echo "Target: $target" >> "$log_file"
    echo "" >> "$log_file"
    
    # Set AWS profile if specified
    if [ -n "$AWS_PROFILE" ]; then
        export AWS_PROFILE="$AWS_PROFILE"
        echo "AWS Profile: $AWS_PROFILE" >> "$log_file"
        echo "" >> "$log_file"
    fi
    
    # Run the scan and capture output
    if scan-cloudformation "$target" 2>&1 | tee -a "$log_file"; then
        log_info "✅ CloudFormation scan completed successfully"
    else
        log_info "⚠️  CloudFormation scan completed with warnings/errors"
    fi
    
    log_info "Full results saved to: $log_file"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -p|--profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        -l|--log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        --check-tools)
            CHECK_TOOLS=true
            shift
            ;;
        setup)
            COMMAND="setup"
            shift
            ;;
        scan-tf)
            COMMAND="scan-tf"
            TARGET="$2"
            shift 2
            ;;
        scan-cf)
            COMMAND="scan-cf"
            TARGET="$2"
            shift 2
            ;;
        check-aws)
            COMMAND="check-aws"
            shift
            ;;
        check-tools)
            COMMAND="check-tools"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Execute the requested command
case "${COMMAND:-setup}" in
    setup)
        run_setup
        ;;
    scan-tf)
        run_terraform_scan "$TARGET"
        ;;
    scan-cf)
        run_cloudformation_scan "$TARGET"
        ;;
    check-aws)
        check_aws
        ;;
    check-tools)
        check_tools
        ;;
    *)
        echo "No command specified. Running default setup..."
        run_setup
        ;;
esac
