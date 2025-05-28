#!/bin/bash
# DevOps Scanner - Simple Wrapper Script
# Automatically handles volume mounting for the DevOps Universal Scanner
# Usage: ./devops-scanner scan-[type] [target]

set -e

CONTAINER_IMAGE="spd109/devops-uat:latest"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Auto-detect current working directory
WORK_DIR=$(pwd)

# Show help if no arguments
show_help() {
    echo -e "${BLUE}DevOps Universal Scanner - Simple Wrapper${NC}"
    echo ""
    echo -e "${GREEN}Usage:${NC}"
    echo "  devops-scanner scan-[type] [target]"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  devops-scanner scan-terraform terraform/"
    echo "  devops-scanner scan-cloudformation template.yaml"
    echo "  devops-scanner scan-docker nginx:latest"
    echo ""
    echo -e "${GREEN}Supported scan types:${NC}"
    echo "  scan-terraform, scan-cloudformation, scan-docker"
    echo "  scan-arm, scan-bicep, scan-gcp"
    echo ""
    echo -e "${YELLOW}Note: Working directory is automatically mounted${NC}"
}

# Show help if no arguments or help requested
if [ $# -eq 0 ] || [ "$1" = "help" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Build Docker command with auto-detected volume mount
echo -e "${BLUE}DevOps Scanner - Auto-mounting: ${WORK_DIR}${NC}"

# Execute the Docker command with all passed arguments
docker run -it --rm -v "${WORK_DIR}:/work" ${CONTAINER_IMAGE} "$@"

