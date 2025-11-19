#!/usr/bin/env python3
"""
Path Detector Helper
Automatically detects and formats paths for Docker volume mounting
"""

import os
import platform
from pathlib import Path
from typing import Dict, Optional

class PathDetector:
    """Handles automatic path detection and Docker volume formatting"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.is_windows = self.platform == 'windows'
        
    def get_working_directory_info(self) -> Dict[str, str]:
        """Get comprehensive working directory information for Docker mounting"""
        
        # Get current working directory
        cwd = os.getcwd()
        
        # Convert to Path object for easier manipulation
        cwd_path = Path(cwd).resolve()
        
        # Prepare Docker volume mount format
        docker_volume = self._format_for_docker_volume(cwd_path)
        
        return {
            'host_path': str(cwd_path),
            'container_path': '/work',
            'docker_volume': docker_volume,
            'platform': self.platform,
            'is_windows': self.is_windows
        }
        
    def _format_for_docker_volume(self, path: Path) -> str:
        """Format path for Docker volume mounting"""
        
        if self.is_windows:
            # Convert Windows path to Docker format
            # C:\Users\... -> /c/Users/...
            path_str = str(path).replace('\\', '/')
            
            # Handle drive letter
            if len(path_str) >= 2 and path_str[1] == ':':
                drive = path_str[0].lower()
                path_str = f"/{drive}{path_str[2:]}"
                
            return path_str
        else:
            # Unix-like systems
            return str(path)
            
    def validate_target_path(self, target: str, base_path: Optional[str] = None) -> Dict[str, any]:
        """Validate and resolve target path"""
        
        if base_path is None:
            base_path = os.getcwd()
            
        # Convert to absolute path if relative
        if not os.path.isabs(target):
            target_path = Path(base_path) / target
        else:
            target_path = Path(target)
            
        # Resolve to absolute path
        try:
            resolved_path = target_path.resolve()
            exists = resolved_path.exists()
            is_file = resolved_path.is_file() if exists else None
            is_dir = resolved_path.is_dir() if exists else None
            
            return {
                'path': str(resolved_path),
                'relative_to_cwd': os.path.relpath(str(resolved_path)),
                'exists': exists,
                'is_file': is_file,
                'is_dir': is_dir,
                'valid': True,
                'error': None
            }
            
        except Exception as e:
            return {
                'path': target,
                'relative_to_cwd': target,
                'exists': False,
                'is_file': None,
                'is_dir': None,
                'valid': False,
                'error': str(e)
            }
            
    def get_relative_container_path(self, target_path: str, base_path: str) -> str:
        """Get the path relative to the container working directory"""
        try:
            # Make target_path relative to base_path
            rel_path = os.path.relpath(target_path, base_path)
            
            # Normalize path separators for container (Unix-style)
            container_path = rel_path.replace('\\', '/')
            
            # Remove leading ./ if present
            if container_path.startswith('./'):
                container_path = container_path[2:]
                
            return container_path
            
        except Exception:
            # Fallback to just the filename/dirname
            return os.path.basename(target_path)
            
    def detect_scan_type(self, target_path: str) -> str:
        """Detect the type of scan based on target path"""
        
        if not os.path.exists(target_path):
            return "unknown"
            
        if os.path.isfile(target_path):
            # Check file extension
            ext = Path(target_path).suffix.lower()
            
            if ext in ['.tf', '.tfvars']:
                return 'terraform'
            elif ext in ['.yaml', '.yml', '.json']:
                # Could be CloudFormation, ARM, or other
                return 'template'
            elif ext == '.bicep':
                return 'bicep'
            else:
                return 'file'
                
        elif os.path.isdir(target_path):
            # Check directory contents
            dir_path = Path(target_path)
            
            # Look for Terraform files
            if any(dir_path.glob('*.tf')) or any(dir_path.glob('*.tfvars')):
                return 'terraform'
            
            # Look for other IaC files
            if any(dir_path.glob('*.yaml')) or any(dir_path.glob('*.yml')):
                return 'template'
                
            return 'directory'
            
        return "unknown"
