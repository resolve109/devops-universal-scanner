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
            self.file_handle.write("=" * 80 + "\n")
            self.file_handle.write(f"Security Scan Report - {self._timestamp()}\n")
            self.file_handle.write("=" * 80 + "\n\n")
            self.file_handle.flush()

    def _timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _write(self, message: str, prefix: str = "", timestamp: bool = False):
        """Write to both console and file"""
        if timestamp:
            formatted = f"[{self._timestamp()}] {prefix}{message}"
        else:
            formatted = f"{prefix}{message}"

        # Console
        print(formatted)

        # File
        if self.file_handle:
            # Always include timestamp in file for audit trail
            if timestamp:
                self.file_handle.write(formatted + "\n")
            else:
                self.file_handle.write(f"[{self._timestamp()}] {formatted}\n")
            self.file_handle.flush()

    def message(self, text: str, timestamp: bool = False):
        """Log a regular message"""
        self._write(text, "", timestamp=timestamp)

    def success(self, text: str):
        """Log a success message"""
        self._write(text, "[PASS] ")

    def warning(self, text: str):
        """Log a warning message"""
        self._write(text, "[WARN] ")

    def error(self, text: str):
        """Log an error message"""
        self._write(text, "[FAIL] ")

    def info(self, text: str):
        """Log an info message"""
        self._write(text, "[INFO] ")

    def section(self, title: str, style: str = "double"):
        """
        Log a section header

        Args:
            title: Section title
            style: 'double' (=) or 'single' (-)
        """
        divider = "=" * 80 if style == "double" else "-" * 80

        if self.file_handle:
            self.file_handle.write(f"\n{divider}\n")
            self.file_handle.write(f"[{self._timestamp()}] {title}\n")
            self.file_handle.write(f"{divider}\n")
            self.file_handle.flush()

        print(f"\n{divider}")
        print(title)
        print(divider)

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
