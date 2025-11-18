"""
Logging module for DevOps Scanner
Handles timestamped logging to console and files
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO


class ScanLogger:
    """
    Enhanced logger for scanning operations
    Writes to both console and log file with timestamps
    """

    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialize logger

        Args:
            log_file: Path to log file (optional)
        """
        self.log_file = log_file
        self.file_handle: Optional[TextIO] = None

        if self.log_file:
            self.file_handle = open(self.log_file, 'w', encoding='utf-8')
            self._write_header()

    def _write_header(self):
        """Write log file header"""
        if self.file_handle:
            self.file_handle.write("=" * 65 + "\n")
            self.file_handle.write("     DEVOPS UNIVERSAL SCANNER - SECURITY SCAN REPORT\n")
            self.file_handle.write("=" * 65 + "\n\n")
            self.file_handle.flush()

    def _timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _write(self, message: str, prefix: str = ""):
        """Write to both console and file"""
        timestamped = f"[{self._timestamp()}] {prefix}{message}"

        # Console
        print(timestamped)

        # File
        if self.file_handle:
            self.file_handle.write(timestamped + "\n")
            self.file_handle.flush()

    def message(self, text: str):
        """Log a regular message"""
        self._write(text)

    def success(self, text: str):
        """Log a success message"""
        self._write(text, "✅ SUCCESS: ")

    def warning(self, text: str):
        """Log a warning message"""
        self._write(text, "⚠️  WARNING: ")

    def error(self, text: str):
        """Log an error message"""
        self._write(text, "❌ ERROR: ")

    def section(self, title: str):
        """Log a section header"""
        if self.file_handle:
            self.file_handle.write("\n" + "=" * 60 + "\n")
            self.file_handle.flush()

        print(f"\n{'=' * 60}")
        self._write(title)
        print("=" * 60)

        if self.file_handle:
            self.file_handle.write("=" * 60 + "\n")
            self.file_handle.flush()

    def tool_output(self, output: str):
        """Log raw tool output (no timestamp)"""
        print(output)
        if self.file_handle:
            self.file_handle.write(output + "\n")
            self.file_handle.flush()

    def close(self):
        """Close log file"""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
