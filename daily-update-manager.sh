#!/bin/bash

# Daily Update Manager for DevOps Scanner
# Implements intelligent caching to update packages only once per day
# Author: DevOps Scanner Security Team

set -e

CACHE_DIR="/var/cache/devops-scanner"
LOG_DIR="/var/log/devops-scanner"
UPDATE_LOG="$LOG_DIR/updates.log"
TIMESTAMP_FILE="$CACHE_DIR/last_update_timestamp"

# Ensure directories exist
mkdir -p "$CACHE_DIR" "$LOG_DIR"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$UPDATE_LOG"
}

# Function to check if we need to update (once per day)
should_update() {
    local today=$(date +%Y-%m-%d)
    
    if [[ -f "$TIMESTAMP_FILE" ]]; then
        local last_update=$(cat "$TIMESTAMP_FILE" 2>/dev/null || echo "")
        if [[ "$last_update" == "$today" ]]; then
            # Send to stderr to avoid interfering with command output
            echo "INFO: Packages already updated today ($today). Skipping update check." >&2
            return 1  # Don't update
        fi
    fi
    
    echo "INFO: Starting daily package updates for $today" >&2
    return 0  # Update needed
}

# Function to mark update as completed
mark_update_complete() {
    local today=$(date +%Y-%m-%d)
    echo "$today" > "$TIMESTAMP_FILE"
    log_message "INFO: Daily update completed successfully for $today"
}

# Function to update Python packages safely
update_python_packages() {
    log_message "INFO: Updating Python packages for security..."
    
    # Update pip and setuptools first (CVE-2025-47273)
    if pip3 install --no-cache-dir --break-system-packages --upgrade pip setuptools>=75.0.0; then
        log_message "SUCCESS: Updated pip and setuptools (CVE-2025-47273 fixed)"
    else
        log_message "WARNING: Failed to update pip/setuptools"
        return 1
    fi
    
    # Update security-critical Python packages
    local packages=("cfn-lint" "checkov" "asteval" "google-cloud-core" "google-cloud-storage" "google-api-python-client")
    for package in "${packages[@]}"; do
        if pip3 install --no-cache-dir --break-system-packages --upgrade "$package"; then
            log_message "SUCCESS: Updated $package"
        else
            log_message "WARNING: Failed to update $package"
        fi
    done
}

# Function to update npm packages safely
update_npm_packages() {
    log_message "INFO: Updating npm packages for security..."
    
    # Update security-critical npm packages (CVE fixes)
    local packages=("ip@latest" "cross-spawn@latest" "semver@latest" "tar@latest")
    for package in "${packages[@]}"; do
        if npm install -g "$package"; then
            log_message "SUCCESS: Updated $package"
        else
            log_message "WARNING: Failed to update $package"
        fi
    done
}

# Function to update Go-based tools
update_go_tools() {
    log_message "INFO: Checking for updates to Go-based tools..."
    
    # Check Terraform version
    local current_tf_version=$(terraform version -json 2>/dev/null | jq -r '.terraform_version' 2>/dev/null || echo "unknown")
    local latest_tf_version=$(curl -s https://api.github.com/repos/hashicorp/terraform/releases/latest | grep tag_name | cut -d '"' -f 4 | cut -c 2- 2>/dev/null || echo "unknown")
    
    if [[ "$current_tf_version" != "$latest_tf_version" && "$latest_tf_version" != "unknown" ]]; then
        log_message "INFO: Updating Terraform from $current_tf_version to $latest_tf_version"
        if wget -q "https://releases.hashicorp.com/terraform/${latest_tf_version}/terraform_${latest_tf_version}_linux_amd64.zip" -O "/tmp/terraform.zip" && \
           unzip -q "/tmp/terraform.zip" -d "/tmp/" && \
           mv "/tmp/terraform" "/usr/local/bin/terraform" && \
           rm "/tmp/terraform.zip"; then
            log_message "SUCCESS: Updated Terraform to $latest_tf_version"
        else
            log_message "WARNING: Failed to update Terraform"
        fi
    else
        log_message "INFO: Terraform is up to date ($current_tf_version)"
    fi
    
    # Update tflint
    if curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash; then
        log_message "SUCCESS: Updated tflint"
    else
        log_message "WARNING: Failed to update tflint"
    fi
    
    # Update Trivy (critical for container security)
    if curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin latest; then
        log_message "SUCCESS: Updated Trivy"
    else
        log_message "WARNING: Failed to update Trivy"
    fi
}

# Main update function
perform_daily_updates() {
    local mode="${1:-auto}"
    
    if ! should_update; then
        # Quick exit for auto mode when already updated
        if [[ "$mode" == "auto" ]]; then
            # Already logged to stderr in should_update(), just exit quietly
            exit 0
        fi
        # For manual/force modes, continue anyway
        echo "INFO: Proceeding with update check despite recent update..." >&2
    fi
    
    log_message "INFO: Starting comprehensive security updates..."
    local update_success=true
    
    # Update Python packages
    if ! update_python_packages; then
        update_success=false
    fi
    
    # Update npm packages
    if ! update_npm_packages; then
        update_success=false
    fi
    
    # Update Go tools
    if ! update_go_tools; then
        update_success=false
    fi
    
    if [[ "$update_success" == "true" ]]; then
        mark_update_complete
        log_message "INFO: All daily updates completed successfully"
    else
        log_message "WARNING: Some updates failed. Check logs for details."
        exit 1
    fi
}

# Force update function (ignores timestamp)
force_update() {
    log_message "INFO: Force update requested - bypassing daily check"
    rm -f "$TIMESTAMP_FILE"
    perform_daily_updates
}

# Show update status
show_status() {
    echo "=== DevOps Scanner Update Status ==="
    if [[ -f "$TIMESTAMP_FILE" ]]; then
        local last_update=$(cat "$TIMESTAMP_FILE" 2>/dev/null || echo "unknown")
        echo "Last update: $last_update"
        local today=$(date +%Y-%m-%d)
        if [[ "$last_update" == "$today" ]]; then
            echo "Status: ✅ Up to date (updated today)"
        else
            echo "Status: ⚠️  Update available"
        fi
    else
        echo "Status: ❌ Never updated"
    fi
    
    echo ""
    echo "=== Tool Versions ==="
    # Use timeout to prevent hanging on version checks
    echo "Terraform: $(timeout 3 terraform version 2>/dev/null | head -n1 | grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+' || echo 'Unable to determine')"
    echo "Trivy: $(timeout 3 trivy version 2>/dev/null | grep Version | head -n1 | awk '{print $2}' || echo 'Unable to determine')"
    echo "Checkov: $(timeout 3 checkov --version 2>/dev/null || echo 'Unable to determine')"
    echo "cfn-lint: $(timeout 3 cfn-lint --version 2>/dev/null || echo 'Unable to determine')"
    echo "tflint: $(timeout 3 tflint --version 2>/dev/null | head -n1 | awk '{print $3}' || echo 'Unable to determine')"
    echo "Bicep: $(timeout 3 bicep --version 2>/dev/null || echo 'Unable to determine')"
    
    echo ""
    echo "Log file: $UPDATE_LOG"
    if [[ -f "$UPDATE_LOG" ]]; then
        echo "Recent updates:"
        tail -n 5 "$UPDATE_LOG" 2>/dev/null || echo "  No recent log entries"
    fi
}

# Parse command line arguments
case "${1:-auto}" in
    "auto")
        perform_daily_updates "auto"
        ;;
    "force")
        force_update
        ;;
    "status")
        show_status
        exit 0
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [auto|force|status|help]"
        echo ""
        echo "Commands:"
        echo "  auto    - Update packages only if not updated today (default)"
        echo "  force   - Force update regardless of timestamp"
        echo "  status  - Show current update status and tool versions"
        echo "  help    - Show this help message"
        echo ""
        echo "Security Features:"
        echo "  • Daily update caching prevents redundant downloads"
        echo "  • Addresses CVEs in setuptools, npm packages, and Go tools"
        echo "  • Comprehensive logging in $UPDATE_LOG"
        exit 0
        ;;
    *)
        echo "❌ Unknown command: $1" >&2
        echo "Use '$0 help' for usage information" >&2
        exit 1
        ;;
esac
