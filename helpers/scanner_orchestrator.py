#!/usr/bin/env python3
"""
Scanner Orchestrator Helper
Coordinates different types of scans and manages scanner execution
"""

import os
import sys
from typing import Dict, Optional, Any

# Import local modules
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from docker_manager import DockerManager
from path_detector import PathDetector

class ScannerOrchestrator:
    """Orchestrates scanner execution with specialized handlers"""
    
    def __init__(self, docker_manager: DockerManager):
        self.docker_manager = docker_manager
        self.path_detector = PathDetector()
        
        # Scanner command mapping
        self.scanner_commands = {
            'terraform': 'scan-terraform',
            'cloudformation': 'scan-cloudformation',
            'bicep': 'scan-azure-bicep',
            'arm': 'scan-azure-arm',
            'gcp': 'scan-gcp',
            'docker': 'scan-docker'
        }
        
    def execute_scan(self, 
                    command: str, 
                    target: Optional[str], 
                    work_info: Dict[str, str]) -> bool:
        """Execute a scan with the appropriate scanner"""
        
        try:
            # Check Docker availability
            if not self.docker_manager.check_docker_availability():
                print("❌ Error: Docker is not available or not running")
                print("Please ensure Docker is installed and running")
                return False
                
            # Pull latest image (non-blocking)
            self.docker_manager.pull_container_image()
            
            # Get scanner command
            scanner_cmd = self.scanner_commands.get(command)
            if not scanner_cmd:
                print(f"❌ Error: No scanner available for command '{command}'")
                return False
                
            # Prepare target for container
            container_target = self._prepare_container_target(target, work_info)
            
            # Build and execute Docker command
            docker_cmd = self.docker_manager.build_docker_command(
                scanner_command=scanner_cmd,
                target=container_target,
                work_info=work_info
            )
            
            # Execute the scan
            result = self.docker_manager.execute_docker_command(docker_cmd)
            
            if result['success']:
                print("✅ Scanner execution completed successfully")
                return True
            else:
                print("❌ Scanner execution failed")
                print(f"Return code: {result['returncode']}")
                if result['stderr']:
                    print(f"Error output: {result['stderr']}")
                return False
                
        except Exception as e:
            print(f"❌ Error during scan execution: {e}")
            return False
            
    def _prepare_container_target(self, 
                                target: Optional[str], 
                                work_info: Dict[str, str]) -> Optional[str]:
        """Prepare target path for use inside container"""
        
        if not target:
            return None
            
        # Validate target path
        target_info = self.path_detector.validate_target_path(
            target, work_info['host_path']
        )
        
        if not target_info['valid']:
            print(f"⚠️  Warning: Target path may be invalid: {target_info['error']}")
            
        # Convert to container-relative path
        container_target = self.path_detector.get_relative_container_path(
            target_info['path'], work_info['host_path']
        )
        
        return container_target
        
    def get_available_scanners(self) -> Dict[str, str]:
        """Get list of available scanners"""
        return self.scanner_commands.copy()
        
    def validate_scanner_command(self, command: str) -> bool:
        """Validate if scanner command is available"""
        return command in self.scanner_commands
        
    def get_scanner_info(self, command: str) -> Dict[str, Any]:
        """Get information about a specific scanner"""
        
        scanner_info = {
            'terraform': {
                'description': 'Terraform configuration scanner',
                'tools': ['Checkov', 'TFSec', 'TFLint'],
                'file_types': ['.tf', '.tfvars'],
                'supports_directory': True
            },
            'cloudformation': {
                'description': 'AWS CloudFormation template scanner',
                'tools': ['Checkov', 'CFN-Lint'],
                'file_types': ['.yaml', '.yml', '.json'],
                'supports_directory': False
            },
            'bicep': {
                'description': 'Azure Bicep template scanner',
                'tools': ['Checkov'],
                'file_types': ['.bicep'],
                'supports_directory': False
            },
            'arm': {
                'description': 'Azure ARM template scanner',
                'tools': ['Checkov'],
                'file_types': ['.json'],
                'supports_directory': False
            },
            'gcp': {
                'description': 'GCP Deployment Manager scanner',
                'tools': ['Checkov'],
                'file_types': ['.yaml', '.yml', '.jinja'],
                'supports_directory': False
            },
            'docker': {
                'description': 'Docker image security scanner',
                'tools': ['Trivy', 'Dockle'],
                'file_types': [],
                'supports_directory': False
            }
        }
        
        return scanner_info.get(command, {
            'description': 'Unknown scanner',
            'tools': [],
            'file_types': [],
            'supports_directory': False
        })
