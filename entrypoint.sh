#!/bin/bash
set -e

YAML_FILE="$1"
LOG_FILE="$2"
PROFILE="${3:-default}"  # Use default profile if not specified

# Input validation
if [ -z "$YAML_FILE" ] || [ -z "$LOG_FILE" ]; then
    echo "Error: Missing required parameters."
    echo "Usage: <command> <yaml_file> <log_file> [aws_profile]"
    exit 1
fi

echo "Analyzing: $YAML_FILE"
echo "Log file: $LOG_FILE"
echo "AWS Profile: $PROFILE"
echo ""

# Display environment for debugging
echo "AWS Environment Variables:"
echo "AWS_PROFILE=${AWS_PROFILE:-not set}"
echo "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:+<REDACTED>}"
echo "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:+<REDACTED>}"
echo "AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN:+<REDACTED>}"

# Check if yaml file exists
if [ ! -f "/work/$YAML_FILE" ]; then
    echo "Error: YAML file not found in /work directory: $YAML_FILE"
    exit 1
fi

# Make sure we're in the correct directory
cd /work

# Check if we have write permission for the log file
touch "$LOG_FILE" 2>/dev/null || {
    echo "Error: Cannot write to log file: $LOG_FILE"
    echo "Checking directory permissions..."
    ls -la /work
    echo "Attempting to fix permissions..."
    chmod -R 777 /work
    touch "$LOG_FILE" || {
        echo "Fatal error: Still cannot write to log file."
        exit 1
    }
}

# Create or clear log file - ensure we write to the correct location
echo "====== VALIDATION REPORT: $(date) ======" > "$LOG_FILE"
echo "YAML File: $YAML_FILE" >> "$LOG_FILE"
echo "Tool Versions:" >> "$LOG_FILE"
echo "- AWS CLI: $(aws --version 2>&1)" >> "$LOG_FILE"
echo "- cfn-lint: $(cfn-lint --version 2>&1)" >> "$LOG_FILE"
echo "- checkov: $(checkov --version 2>&1)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Function to run a command and log its output
run_command() {
    local title="$1"
    local command="$2"
    local fail_on_error="${3:-true}"
    
    echo "====== $title ======" 
    echo "====== $title ======" >> "$LOG_FILE"
    
    # Run the command and capture exit code
    eval "$command" 2>&1 | tee -a "$LOG_FILE"
    local exit_code=${PIPESTATUS[0]}
    
    echo "" >> "$LOG_FILE"
    echo ""
    
    if [ "$fail_on_error" = true ]; then
        return $exit_code
    else
        return 0
    fi
}

# Initialize exit status
OVERALL_EXIT=0

# Prioritize environment variables over profile for credentials
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Using AWS credentials from environment variables."
    # Run CloudFormation validate-template without profile
    run_command "AWS CloudFormation Validation (Environment Variables)" "aws cloudformation validate-template --template-body file://$YAML_FILE" false || echo "CloudFormation validation failed, continuing with other checks."
elif [ -n "$AWS_PROFILE" ]; then
    echo "Using AWS_PROFILE environment variable: $AWS_PROFILE"
    # Try using environment variable
    if aws sts get-caller-identity &>/dev/null; then
        echo "AWS profile credentials are valid."
        run_command "AWS CloudFormation Validation (AWS_PROFILE)" "aws cloudformation validate-template --template-body file://$YAML_FILE" false || echo "CloudFormation validation failed, continuing with other checks."
    else
        echo "AWS_PROFILE environment variable set but credentials are not valid."
        echo "Skipping CloudFormation API validation." >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
    fi
elif [ -n "$PROFILE" ]; then
    echo "Using AWS profile: $PROFILE"
    # Try using profile
    if aws --profile "$PROFILE" sts get-caller-identity &>/dev/null; then
        echo "AWS credentials found for profile '$PROFILE'."
        run_command "AWS CloudFormation Validation (Profile)" "aws --profile $PROFILE cloudformation validate-template --template-body file://$YAML_FILE" false || echo "CloudFormation validation failed, continuing with other checks."
    else
        echo "AWS profile credentials are not valid."
        echo "Skipping CloudFormation API validation." >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
    fi
else
    # Try without any profile (for instance roles)
    echo "No AWS profile or environment variables provided, trying instance role..."
    if aws sts get-caller-identity &>/dev/null; then
        echo "AWS credentials found via instance role or environment variables."
        run_command "AWS CloudFormation Validation (Instance Role)" "aws cloudformation validate-template --template-body file://$YAML_FILE" false || echo "CloudFormation validation failed, continuing with other checks."
    else
        echo "No AWS credentials found via any method."
        echo "Skipping CloudFormation API validation." >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
    fi
fi

# Continue with other validations even if AWS credentials are not available
echo "Continuing with local validation tools..."

# Run cfn-lint with CI/CD pipeline settings
run_command "cfn-lint CI/CD Pipeline" "cfn-lint --non-zero-exit-code error --non-zero-exit-code warning $YAML_FILE" true || OVERALL_EXIT=1

# Run cfn-lint with additional checks that might be just informational
run_command "cfn-lint Extended Checks" "cfn-lint -i W --non-zero-exit-code error $YAML_FILE" false

# Run checkov with full output
run_command "Checkov" "checkov -f $YAML_FILE" true || OVERALL_EXIT=1

# Run additional checks
# AWS CDK Toolkit validation (if present)
if command -v cdk &> /dev/null; then
    # Check if credentials are available
    CREDENTIALS_AVAILABLE=false
    
    if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
        CREDENTIALS_AVAILABLE=true
    elif [ -n "$AWS_PROFILE" ] && aws sts get-caller-identity &>/dev/null; then
        CREDENTIALS_AVAILABLE=true
    elif [ -n "$PROFILE" ] && aws --profile "$PROFILE" sts get-caller-identity &>/dev/null; then
        CREDENTIALS_AVAILABLE=true
    elif aws sts get-caller-identity &>/dev/null; then
        CREDENTIALS_AVAILABLE=true
    fi
    
    if [ "$CREDENTIALS_AVAILABLE" = true ] && grep -q "AWS::CDK::Metadata" "$YAML_FILE"; then
        if [ -n "$AWS_PROFILE" ]; then
            run_command "AWS CDK Validation" "AWS_PROFILE=$AWS_PROFILE cdk synth" false
        elif [ -n "$PROFILE" ]; then
            run_command "AWS CDK Validation" "AWS_PROFILE=$PROFILE cdk synth" false
        else
            run_command "AWS CDK Validation" "cdk synth" false
        fi
    fi
fi

echo "====== END OF REPORT ======" >> "$LOG_FILE"

# Make sure log file is properly written to disk
sync

# Verify log file exists and has content
if [ -f "$LOG_FILE" ] && [ -s "$LOG_FILE" ]; then
    echo "Full validation results saved to: $LOG_FILE"
    # Print file stats
    echo "Log file details:"
    ls -la "$LOG_FILE"
    # Print first few lines as verification
    echo "First 5 lines of log file:"
    head -n 5 "$LOG_FILE"
else
    echo "ERROR: Could not save log file to: $LOG_FILE or file is empty"
    # Try to debug the issue
    echo "Current directory contents:"
    ls -la
    echo "Attempting emergency log file copy..."
    # Create a fallback log file in a different location
    EMERGENCY_LOG="/tmp/emergency-log-$(date +%s).txt"
    echo "====== EMERGENCY LOG ======" > "$EMERGENCY_LOG"
    echo "Original log file path: $LOG_FILE" >> "$EMERGENCY_LOG"
    echo "Validation completed with exit code: $OVERALL_EXIT" >> "$EMERGENCY_LOG"
    echo "Emergency log created at: $EMERGENCY_LOG"
    exit 1
fi

exit $OVERALL_EXIT