#!/usr/bin/env python3
"""
DevOps Universal Scanner - Cross-platform Auto-mounting Wrapper
Automatically handles volume mounting - no manual setup required!
Usage: python devops-scanner.py scan-[type] [target]
"""

import sys
import os
import subprocess
from pathlib import Path

CONTAINER_IMAGE = "spd109/devops-uat:latest"

def show_help():
    """Display help information"""
    print("\n🚀 DevOps Universal Scanner - Auto-mounting Wrapper")
    print("\nUsage: python devops-scanner.py scan-[type] [target]")
    print("\nCommands:")
    print("  scan-terraform [dir]         - Scan Terraform configuration")
    print("  scan-cloudformation [file]   - Scan CloudFormation template")
    print("  scan-arm [file]             - Scan Azure ARM template")
    print("  scan-bicep [file]           - Scan Azure Bicep template")
    print("  scan-gcp [file]             - Scan GCP template")
    print("  scan-docker [image:tag]     - Scan Docker image")
    print("\nExamples:")
    print("  python devops-scanner.py scan-terraform terraform/")
    print("  python devops-scanner.py scan-cloudformation template.yaml")
    print("  python devops-scanner.py scan-docker nginx:latest")
    print("\n✨ Features:")
    print("  • Automatic working directory detection")
    print("  • No manual volume mounts required!")
    print("  • Cross-platform support")

def get_current_directory():
    """Get current working directory formatted for Docker"""
    cwd = Path.cwd().resolve()
    
    # Convert Windows path format if needed
    if os.name == 'nt':  # Windows
        cwd_str = str(cwd).replace('\\', '/')
        # Convert C: to /c/ format for Docker
        if len(cwd_str) >= 2 and cwd_str[1] == ':':
            drive = cwd_str[0].lower()
            cwd_str = f"/{drive}{cwd_str[2:]}"
        return cwd_str
    else:
        return str(cwd)

def main():
    """Main entry point"""
    # Show help if no arguments or help requested
    if len(sys.argv) == 1 or sys.argv[1] in ['help', '-h', '--help']:
        show_help()
        return 0
    
    # Get current working directory
    work_dir = get_current_directory()
    
    # Build Docker command
    docker_cmd = [
        'docker', 'run', '-it', '--rm',
        '-v', f"{work_dir}:/work",
        CONTAINER_IMAGE
    ] + sys.argv[1:]  # Add all passed arguments
    
    # Display what we're doing
    print(f"\n🚀 DevOps Scanner - Auto-mounting wrapper")
    print(f"📁 Mounting: {work_dir} -> /work")
    print(f"🐳 Executing: {' '.join(docker_cmd)}")
    print("")
    
    # Execute Docker command
    try:
        result = subprocess.run(docker_cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️  Scan interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error executing Docker command: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
