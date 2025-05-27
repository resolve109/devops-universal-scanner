#!/bin/bash
set -e

# Function to show help message
show_help() {
    echo "Usage: ./run-linter.sh [options] [file]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -b, --build         Force rebuild of the Docker image"
    echo "  -u, --update        Update the Docker image to the latest version"
    echo "  -q, --quiet         Less verbose output"
    echo "  -p, --profile       AWS profile to use (default: 'default')"
    echo "  -d, --default       Use the default AWS profile (shorthand for -p default)"
    echo "  -s, --sso           Attempt to refresh SSO credentials before running"
    echo "  -v, --verbose       Verbose output for debugging"
    echo "  -l, --local-only    Only run local validations (skip Docker)"
    echo ""
    echo "If no file is provided, you will be prompted to enter one."
    exit 0
}

# Default settings
FORCE_REBUILD=false
UPDATE_IMAGE=false
QUIET_MODE=false
AWS_PROFILE="default"
REFRESH_SSO=false
VERBOSE_MODE=false
LOCAL_ONLY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -b|--build)
            FORCE_REBUILD=true
            shift
            ;;
        -u|--update)
            UPDATE_IMAGE=true
            shift
            ;;
        -q|--quiet)
            QUIET_MODE=true
            shift
            ;;
        -p|--profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        -d|--default)
            AWS_PROFILE="default"
            shift
            ;;
        -s|--sso)
            REFRESH_SSO=true
            shift
            ;;
        -v|--verbose)
            VERBOSE_MODE=true
            shift
            ;;
        -l|--local-only)
            LOCAL_ONLY=true
            shift
            ;;
        *)
            # Assume it's the file path
            YAML_FILE="$1"
            shift
            ;;
    esac
done

# Function to log verbose messages
log_verbose() {
    if [ "$VERBOSE_MODE" = true ]; then
        echo "[DEBUG] $1"
    fi
}

# If file is not provided as argument, prompt for it
if [ -z "$YAML_FILE" ]; then
    read -p "Enter the YAML file path to analyze: " YAML_FILE
fi

# Make sure YAML_FILE exists
if [ ! -f "$YAML_FILE" ]; then
    echo "Error: File '$YAML_FILE' not found."
    exit 1
fi

# Check AWS credentials and refresh SSO if needed
if [ "$REFRESH_SSO" = true ]; then
    echo "Checking AWS credentials..."
    
    # Check if credentials are valid
    if ! aws --profile "$AWS_PROFILE" sts get-caller-identity &>/dev/null; then
        echo "AWS credentials not valid. Attempting to refresh SSO session..."
        aws sso login --profile "$AWS_PROFILE"
        
        # Verify we now have valid credentials
        if ! aws --profile "$AWS_PROFILE" sts get-caller-identity &>/dev/null; then
            echo "Warning: Unable to obtain valid AWS credentials. CloudFormation validation may fail."
        else
            echo "AWS SSO login successful."
        fi
    else
        echo "AWS credentials are valid."
    fi
fi

# Convert any relative path to absolute path
YAML_FILE=$(realpath "$YAML_FILE")
YAML_FILENAME=$(basename "$YAML_FILE")
ORIGINAL_DIR=$(dirname "$YAML_FILE")
CURRENT_DIR=$(pwd)

# Create timestamp for log file
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
LOG_FILENAME="validations-${YAML_FILENAME%.*}-${TIMESTAMP}.txt"
ORIGINAL_LOG_FILE="${ORIGINAL_DIR}/${LOG_FILENAME}"
CURRENT_LOG_FILE="${CURRENT_DIR}/${LOG_FILENAME}"

# Create a temp directory for processing
TEMP_DIR=$(mktemp -d)
TEMP_YAML_FILE="${TEMP_DIR}/${YAML_FILENAME}"
TEMP_LOG_FILE="${TEMP_DIR}/${LOG_FILENAME}"

# Start the log file
echo "====== VALIDATION REPORT: $(date) ======" > "$TEMP_LOG_FILE"
echo "YAML File: $YAML_FILENAME" >> "$TEMP_LOG_FILE"
echo "Tool Versions:" >> "$TEMP_LOG_FILE"
echo "- AWS CLI: $(aws --version 2>&1)" >> "$TEMP_LOG_FILE"

# Copy the YAML file to temp directory
cp "$YAML_FILE" "$TEMP_YAML_FILE"

[ "$QUIET_MODE" = false ] && echo "Using temporary directory: $TEMP_DIR"
[ "$QUIET_MODE" = false ] && echo "Using AWS profile: $AWS_PROFILE"

# ---------- LOCAL AWS CLOUDFORMATION VALIDATION ----------
echo "====== AWS CloudFormation Validation (Local) ======" | tee -a "$TEMP_LOG_FILE"
echo "" >> "$TEMP_LOG_FILE"

# Run AWS CloudFormation validate-template (locally, not in Docker)
if aws --profile "$AWS_PROFILE" cloudformation validate-template --template-body "file://$YAML_FILE" > "${TEMP_DIR}/cf_validation.json" 2> "${TEMP_DIR}/cf_error.txt"; then
    echo "✅ AWS CloudFormation validation passed." | tee -a "$TEMP_LOG_FILE"
    if [ "$VERBOSE_MODE" = true ]; then
        echo "Validation Response:" | tee -a "$TEMP_LOG_FILE"
        cat "${TEMP_DIR}/cf_validation.json" | tee -a "$TEMP_LOG_FILE"
    fi
else
    echo "❌ AWS CloudFormation validation failed." | tee -a "$TEMP_LOG_FILE"
    cat "${TEMP_DIR}/cf_error.txt" | tee -a "$TEMP_LOG_FILE"
fi

echo "" | tee -a "$TEMP_LOG_FILE"
echo "" >> "$TEMP_LOG_FILE"

# Skip Docker portion if local-only flag is set
if [ "$LOCAL_ONLY" = true ]; then
    echo "Skipping Docker-based validations due to --local-only flag."
else
    # ---------- DOCKER-BASED VALIDATIONS ----------
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo "Error: Docker is not running. Please start Docker and try again."
        exit 1
    fi

    # Set image name
    IMAGE_NAME="cloudformation-linter:latest"

    # If update flag is set, remove the image to force pull
    if [ "$UPDATE_IMAGE" = true ]; then
        echo "Forcing update of Docker image..."
        docker rmi "$IMAGE_NAME" >/dev/null 2>&1 || true
        FORCE_REBUILD=true
    fi

    # Check if the image exists, build if it doesn't or if forced
    if [ "$FORCE_REBUILD" = true ] || ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
        echo "Building Docker image. This will use the latest versions of all tools..."
        # Copy the current directory to a temp directory to build the image
        TEMP_BUILD_DIR=$(mktemp -d)
        
        # Check if Dockerfile and entrypoint.sh exist in current directory
        if [ -f "Dockerfile" ] && [ -f "entrypoint.sh" ]; then
            cp Dockerfile entrypoint.sh "$TEMP_BUILD_DIR"
        else
            echo "Error: Dockerfile and/or entrypoint.sh not found in current directory."
            echo "Make sure both files are in the same directory as run-linter.sh."
            rm -rf "$TEMP_BUILD_DIR"
            rm -rf "$TEMP_DIR"
            exit 1
        fi
        
        # Build image from the temp directory with progress output
        echo "Building Docker image - this may take a few minutes..."
        docker build --progress=plain -t "$IMAGE_NAME" "$TEMP_BUILD_DIR"
        
        # Clean up temp directory
        rm -rf "$TEMP_BUILD_DIR"
    fi

    # Create a small entrypoint-naws.sh file that skips AWS validation
    cat > "${TEMP_DIR}/entrypoint-naws.sh" << 'EOF'
#!/bin/bash
set -e

YAML_FILE="$1"
LOG_FILE="$2"

# Skip AWS checking and validation

# Run cfn-lint
echo "====== cfn-lint CI/CD Pipeline ======" | tee -a "$LOG_FILE"
cfn-lint --non-zero-exit-code error --non-zero-exit-code warning "$YAML_FILE" 2>&1 | tee -a "$LOG_FILE"
LINT_EXIT=$?
echo "" | tee -a "$LOG_FILE"

# Run cfn-lint with additional checks
echo "====== cfn-lint Extended Checks ======" | tee -a "$LOG_FILE"
cfn-lint -i W --non-zero-exit-code error "$YAML_FILE" 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Run checkov
echo "====== Checkov ======" | tee -a "$LOG_FILE"
checkov -f "$YAML_FILE" 2>&1 | tee -a "$LOG_FILE"
CHECKOV_EXIT=$?
echo "" | tee -a "$LOG_FILE"

exit $(($LINT_EXIT || $CHECKOV_EXIT))
EOF

    # Make the script executable
    chmod +x "${TEMP_DIR}/entrypoint-naws.sh"

    # Run the Docker container with the custom script
    echo "Starting Docker container for linting and security checks..."
    set +e  # Don't exit on error
    docker run --rm -i \
      -v "${TEMP_DIR}:/work" \
      --entrypoint "/work/entrypoint-naws.sh" \
      "$IMAGE_NAME" "$YAML_FILENAME" "$LOG_FILENAME"
    DOCKER_EXIT=$?
    set -e  # Resume exit on error

    # Check if Docker ran successfully
    if [ $DOCKER_EXIT -ne 0 ]; then
        echo "Warning: Docker container exited with code $DOCKER_EXIT"
    fi
fi

# Make sure the target directories exist and are writable
echo "Attempting to copy results to original directory: $ORIGINAL_DIR"
if [ ! -w "$ORIGINAL_DIR" ]; then
    echo "Warning: Cannot write to original directory: $ORIGINAL_DIR"
    echo "Will only save log file to current directory: $CURRENT_DIR"
else
    # Copy using multiple methods to ensure success
    echo "Copying validation results to original directory..."
    cat "${TEMP_LOG_FILE}" > "$ORIGINAL_LOG_FILE" 2>/dev/null || cp "${TEMP_LOG_FILE}" "$ORIGINAL_LOG_FILE" 2>/dev/null || true
    
    # Verify the file was created in original directory
    if [ -f "$ORIGINAL_LOG_FILE" ] && [ -s "$ORIGINAL_LOG_FILE" ]; then
        echo "✅ Log file successfully saved to: $ORIGINAL_LOG_FILE"
    else
        echo "❌ Failed to save log file to: $ORIGINAL_LOG_FILE"
    fi
fi

# Ensure log file is copied to current directory
echo "Copying validation results to current directory: $CURRENT_DIR"
cat "${TEMP_LOG_FILE}" > "$CURRENT_LOG_FILE" 2>/dev/null || cp "${TEMP_LOG_FILE}" "$CURRENT_LOG_FILE" 2>/dev/null || true

# Verify the file was created in current directory
if [ -f "$CURRENT_LOG_FILE" ] && [ -s "$CURRENT_LOG_FILE" ]; then
    echo "✅ Log file successfully saved to: $CURRENT_LOG_FILE"
else 
    echo "❌ Failed to save log file to: $CURRENT_LOG_FILE"
    
    # One last desperate attempt
    echo "Attempting emergency save method..."
    FALLBACK_LOG="${CURRENT_DIR}/emergency-linter-log-$(date +%s).txt"
    echo "====== EMERGENCY VALIDATION REPORT: $(date) ======" > "$FALLBACK_LOG"
    echo "Original target file: $CURRENT_LOG_FILE" >> "$FALLBACK_LOG"
    echo "" >> "$FALLBACK_LOG"
    cat "${TEMP_LOG_FILE}" >> "$FALLBACK_LOG" 2>/dev/null || true
    
    if [ -f "$FALLBACK_LOG" ] && [ -s "$FALLBACK_LOG" ]; then
        echo "✅ Emergency log file saved to: $FALLBACK_LOG"
    fi
fi

# Clean up the temp directory
rm -rf "$TEMP_DIR"

echo ""
echo "Process completed."