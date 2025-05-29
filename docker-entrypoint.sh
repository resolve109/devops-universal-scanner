#!/bin/bash
# DevOps Universal Scanner - Docker Entrypoint
# Handles auto-detection and provides helpful guidance when volume mounting is missing

set +e  # Don't exit on errors, handle them gracefully

# Function to show help
show_help() {
    echo "================================================================"
    echo "🚀 DevOps Universal Scanner - Docker Container"
    echo "================================================================"
    echo ""
    echo "USAGE:"
    echo "  docker run -it --rm -v \"\$(pwd):/work\" spd109/devops-uat:latest <command> [target]"
    echo ""
    echo "AVAILABLE COMMANDS:"
    echo "  scan-terraform <directory>    - Scan Terraform files"
    echo "  scan-cloudformation <file>    - Scan CloudFormation templates"
    echo "  scan-docker <image>           - Scan Docker images"
    echo "  scan-arm <file>               - Scan Azure ARM templates"
    echo "  scan-bicep <file>             - Scan Azure Bicep files"
    echo "  scan-gcp <file>               - Scan GCP Deployment Manager"
    echo ""
    echo "EXAMPLES:"
    echo "  docker run -it --rm -v \"\$(pwd):/work\" spd109/devops-uat:latest scan-terraform terraform/"
    echo "  docker run -it --rm -v \"\$(pwd):/work\" spd109/devops-uat:latest scan-docker nginx:latest"
    echo ""
    echo "📁 Current working directory contents:"
    ls -la /work 2>/dev/null || echo "   (No files found - volume mount required for file scanning)"
    echo ""
}

# Function to check if volume is mounted
check_volume_mount() {
    if [ ! "$(ls -A /work 2>/dev/null)" ]; then
        return 1  # Empty or doesn't exist
    fi
    return 0  # Has content
}

# Function to provide volume mount guidance
provide_volume_mount_guidance() {
    local scan_type="$1"
    local target="$2"
    
    echo "❌ ERROR: No files found in container working directory"
    echo ""
    echo "🔧 SOLUTION: Add volume mount to access your files"
    echo ""
    echo "💡 Try this command instead:"
    
    # Platform-specific guidance
    if [ -n "$target" ] && [[ "$target" != *":"* ]]; then
        echo ""
        echo "Windows (PowerShell):"
        echo "  docker run -it --rm -v \"\${PWD}:/work\" spd109/devops-uat:latest $scan_type $target"
        echo ""
        echo "Windows (Command Prompt):"
        echo "  docker run -it --rm -v \"%cd%:/work\" spd109/devops-uat:latest $scan_type $target"
        echo ""
        echo "Linux/macOS:"
        echo "  docker run -it --rm -v \"\$(pwd):/work\" spd109/devops-uat:latest $scan_type $target"
    else
        echo ""
        echo "Windows (PowerShell):"
        echo "  docker run -it --rm -v \"\${PWD}:/work\" spd109/devops-uat:latest $scan_type ${target:-'<your-target>'}"
        echo ""
        echo "Windows (Command Prompt):"
        echo "  docker run -it --rm -v \"%cd%:/work\" spd109/devops-uat:latest $scan_type ${target:-'<your-target>'}"
        echo ""
        echo "Linux/macOS:"
        echo "  docker run -it --rm -v \"\$(pwd):/work\" spd109/devops-uat:latest $scan_type ${target:-'<your-target>'}"
    fi
    echo ""
    echo "💡 Remember: Volume mounting (-v flag) is required for file-based scans!"
}

# Main entrypoint logic
main() {
    # If no arguments, show help
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # Parse command
    COMMAND="$1"
    shift
    
    # Handle help requests
    case "$COMMAND" in
        help|-h|--help)
            show_help
            exit 0
            ;;
    esac
    
    # Check if it's a scanner command
    case "$COMMAND" in
        scan-terraform|scan-cloudformation|scan-docker|scan-arm|scan-bicep|scan-gcp)
            TARGET="$1"
            
            # For Docker image scanning, don't require volume mount
            if [ "$COMMAND" = "scan-docker" ]; then
                if [ -z "$TARGET" ]; then
                    echo "❌ ERROR: Docker image name required"
                    echo "Usage: scan-docker <image_name>"
                    echo "Example: scan-docker nginx:latest"
                    exit 1
                fi
                exec /usr/local/bin/tools/scan-docker.sh "$TARGET"
            fi
            
            # For file-based scanning, check if volume is mounted
            if ! check_volume_mount && [ -n "$TARGET" ]; then
                provide_volume_mount_guidance "$COMMAND" "$TARGET"
                exit 1
            fi
            
            # Execute the appropriate scanner
            case "$COMMAND" in
                scan-terraform)
                    exec /usr/local/bin/tools/scan-terraform.sh "$@"
                    ;;
                scan-cloudformation)
                    exec /usr/local/bin/tools/scan-cloudformation.sh "$@"
                    ;;
                scan-arm)
                    exec /usr/local/bin/tools/scan-arm.sh "$@"
                    ;;
                scan-bicep)
                    exec /usr/local/bin/tools/scan-bicep.sh "$@"
                    ;;
                scan-gcp)
                    exec /usr/local/bin/tools/scan-gcp.sh "$@"
                    ;;
            esac
            ;;
        *)
            # Unknown command - check if it's a tool wrapper
            if [ -x "/usr/local/bin/tools/${COMMAND}-wrapper.sh" ]; then
                exec "/usr/local/bin/tools/${COMMAND}-wrapper.sh" "$@"
            elif [ -x "/usr/local/bin/$COMMAND" ]; then
                exec "/usr/local/bin/$COMMAND" "$@"
            elif [ "$COMMAND" = "terraform" ] || [ "$COMMAND" = "tflint" ] || [ "$COMMAND" = "tfsec" ] || [ "$COMMAND" = "checkov" ] || [ "$COMMAND" = "trivy" ] || [ "$COMMAND" = "bicep" ] || [ "$COMMAND" = "cfn-lint" ]; then
                # Direct tool execution for common tools
                echo "🔄 Running $COMMAND directly..."
                exec "/usr/local/bin/$COMMAND" "$@"
            else
                echo "❌ ERROR: Unknown command '$COMMAND'"
                echo ""
                echo "Available scanners:"
                echo "  scan-terraform, scan-cloudformation, scan-docker, scan-arm (or scan-azure-arm),"
                echo "  scan-bicep (or scan-azure-bicep), scan-gcp"
                echo ""
                echo "Available tools:"
                echo "  terraform, tflint, tfsec, checkov, trivy, cfn-lint, bicep"
                echo ""
                show_help
                exit 1
            fi
            ;;
    esac
}

# Execute main function with all arguments
main "$@"
