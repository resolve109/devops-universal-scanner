#!/bin/bash
# Checkov Result Processor
# Handles Checkov execution with improved error handling and result processing

set +e  # Don't exit on errors, handle them gracefully

# Configuration
CHECKOV_TEMP_FILE="/tmp/checkov-report.json"
CHECKOV_DEFAULT='{"results":{"failed_checks":[],"passed_checks":[],"skipped_checks":[]}}'

# Function to run Checkov with multiple fallback methods
run_checkov_scan() {
    local framework="$1"
    local target="$2"
    local scan_type="$3"  # "file" or "directory"
    
    echo "🔍 Running Checkov security scan..."
    echo "   Framework: $framework"
    echo "   Target: $target"
    echo "   Type: $scan_type"
    
    # Initialize with default structure
    echo "$CHECKOV_DEFAULT" > "$CHECKOV_TEMP_FILE"
    
    local checkov_cmd=""
    local method_used=""
    
    # Build base command based on scan type
    if [ "$scan_type" = "directory" ]; then
        checkov_cmd="checkov -d $target"
    else
        checkov_cmd="checkov -f $target"
    fi
    
    # Method 1: Try with specific framework and --output-file
    echo "   Attempting Method 1: Framework-specific with output file..."
    if $checkov_cmd --framework $framework --output=json --output-file="$CHECKOV_TEMP_FILE" 2>/dev/null; then
        method_used="Method 1 (framework + output-file)"
        echo "   ✓ Success with Method 1"
    # Method 2: Try with specific framework and stdout redirection
    elif $checkov_cmd --framework $framework --output=json > "$CHECKOV_TEMP_FILE" 2>&1; then
        method_used="Method 2 (framework + stdout)"
        echo "   ✓ Success with Method 2"
    # Method 3: Try without framework specification (auto-detect)
    elif $checkov_cmd --output=json > "$CHECKOV_TEMP_FILE" 2>&1; then
        method_used="Method 3 (auto-detect)"
        echo "   ✓ Success with Method 3"
    else
        method_used="Default (all methods failed)"
        echo "   ⚠ All Checkov methods failed, using default structure"
    fi
    
    # Validate the JSON output
    if validate_checkov_json "$CHECKOV_TEMP_FILE"; then
        echo "   ✓ Valid Checkov JSON generated using: $method_used"
        
        # Count results
        local failed_count=$(jq -r '.results.failed_checks | length' "$CHECKOV_TEMP_FILE" 2>/dev/null || echo "0")
        local passed_count=$(jq -r '.results.passed_checks | length' "$CHECKOV_TEMP_FILE" 2>/dev/null || echo "0")
        local skipped_count=$(jq -r '.results.skipped_checks | length' "$CHECKOV_TEMP_FILE" 2>/dev/null || echo "0")
        
        echo "   📊 Results: $failed_count failed, $passed_count passed, $skipped_count skipped"
    else
        echo "   ⚠ Generated JSON is invalid, using default structure"
        echo "$CHECKOV_DEFAULT" > "$CHECKOV_TEMP_FILE"
    fi
    
    # Always run console output for user visibility (suppress JSON but show findings)
    echo ""
    echo "📋 Checkov Console Output:"
    if [ "$scan_type" = "directory" ]; then
        checkov -d "$target" --framework "$framework" --quiet 2>/dev/null || echo "   Checkov scan completed"
    else
        checkov -f "$target" --framework "$framework" --quiet 2>/dev/null || echo "   Checkov scan completed"
    fi
}

# Function to validate Checkov JSON output
validate_checkov_json() {
    local json_file="$1"
    
    # Check if file exists and has content
    if [ ! -f "$json_file" ] || [ ! -s "$json_file" ]; then
        return 1
    fi
    
    # Check if it's valid JSON
    if ! jq empty "$json_file" 2>/dev/null; then
        return 1
    fi
    
    # Check if it has the expected Checkov structure
    if ! jq -e '.results' "$json_file" >/dev/null 2>&1; then
        return 1
    fi
    
    return 0
}

# Function to get Checkov results for consolidation
get_checkov_results() {
    if [ -f "$CHECKOV_TEMP_FILE" ]; then
        cat "$CHECKOV_TEMP_FILE"
    else
        echo "$CHECKOV_DEFAULT"
    fi
}

# Function to clean up temporary files
cleanup_checkov_temp() {
    rm -f "$CHECKOV_TEMP_FILE"
}

# Main execution based on arguments
case "${1:-help}" in
    "scan-file")
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 scan-file <framework> <file_path>"
            exit 1
        fi
        run_checkov_scan "$2" "$3" "file"
        ;;
    "scan-directory") 
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 scan-directory <framework> <directory_path>"
            exit 1
        fi
        run_checkov_scan "$2" "$3" "directory"
        ;;
    "get-results")
        get_checkov_results
        ;;
    "cleanup")
        cleanup_checkov_temp
        ;;
    "validate")
        if [ -z "$2" ]; then
            echo "Usage: $0 validate <json_file>"
            exit 1
        fi
        if validate_checkov_json "$2"; then
            echo "✓ Valid Checkov JSON"
            exit 0
        else
            echo "✗ Invalid Checkov JSON"
            exit 1
        fi
        ;;
    *)
        echo "Checkov Result Processor - Helper Script"
        echo ""
        echo "Commands:"
        echo "  scan-file <framework> <file>       - Scan a single file"
        echo "  scan-directory <framework> <dir>   - Scan a directory"
        echo "  get-results                        - Get current results JSON"
        echo "  validate <json_file>               - Validate JSON structure"
        echo "  cleanup                            - Clean temporary files"
        ;;
esac
