#!/usr/bin/env python3
"""
Docker Manager Helper
Handles Docker command construction and execution with auto-detection
"""

import os
import subprocess
import platform
from typing import Dict, List, Optional, Any

class DockerManager:
    """Manages Docker operations with automatic configuration"""
    
    def __init__(self, container_image: str):
        self.container_image = container_image
        self.platform = platform.system().lower()
        
    def build_docker_command(self, 
                           scanner_command: str, 
                           target: Optional[str],
                           work_info: Dict[str, str],
                           additional_args: List[str] = None) -> List[str]:
        """Build Docker command with automatic volume mounting"""
        
        cmd = [
            'docker', 'run', '--rm',
            '-v', f"{work_info['docker_volume']}:/work",
            self.container_image,
            scanner_command
        ]
        
        if target:
            cmd.append(target)
            
        if additional_args:
            cmd.extend(additional_args)
            
        return cmd
        
    def execute_docker_command(self, 
                             docker_cmd: List[str], 
                             show_output: bool = True) -> Dict[str, Any]:
        """Execute Docker command and return results"""
        
        try:
            if show_output:
                print(f"🐳 Executing: {' '.join(docker_cmd)}")
                print("")
            
            # Execute command
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(docker_cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out after 10 minutes',
                'command': ' '.join(docker_cmd)
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f'Exception occurred: {str(e)}',
                'command': ' '.join(docker_cmd)
            }
            
    def check_docker_availability(self) -> bool:
        """Check if Docker is available and running"""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
            
    def pull_container_image(self) -> bool:
        """Pull the latest container image"""
        try:
            print(f"🐳 Pulling container image: {self.container_image}")
            result = subprocess.run(
                ['docker', 'pull', self.container_image],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for pulling
            )
            
            if result.returncode == 0:
                print("✅ Container image updated successfully")
                return True
            else:
                print(f"⚠️  Warning: Failed to pull image: {result.stderr}")
                print("Using existing local image...")
                return True  # Continue with existing image
                
        except Exception as e:
            print(f"⚠️  Warning: Could not pull image: {e}")
            print("Using existing local image...")
            return True  # Continue with existing image
            
    def get_container_logs(self, container_id: str) -> str:
        """Get logs from a running container"""
        try:
            result = subprocess.run(
                ['docker', 'logs', container_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout + result.stderr
        except:
            return "Could not retrieve container logs"
