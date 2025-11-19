"""
Integration tests for Scanner

Tests full scanning workflows with multiple components.
"""

import pytest
from pathlib import Path
from devops_universal_scanner.core.scanner import Scanner


class TestScannerIntegration:
    """Test Scanner integration with real test files"""

    @pytest.fixture
    def test_files_dir(self):
        """Get test files directory"""
        return Path(__file__).parent.parent.parent / "devops_universal_scanner" / "test-files"

    def test_cloudformation_scan_complete_workflow(self, test_files_dir):
        """Test complete CloudFormation scanning workflow"""
        # Setup
        target = test_files_dir / "cloudformation" / "ec2-instance.yaml"

        if not target.exists():
            pytest.skip(f"Test file not found: {target}")

        # Execute
        scanner = Scanner("cloudformation", target, environment="test")
        exit_code = scanner.scan()

        # Assert
        assert isinstance(exit_code, int)
        assert scanner.log_file.exists()

    def test_terraform_scan_complete_workflow(self, test_files_dir):
        """Test complete Terraform scanning workflow"""
        # Setup
        target = test_files_dir / "terraform" / "main.tf"

        if not target.exists():
            pytest.skip(f"Test file not found: {target}")

        # Execute
        scanner = Scanner("terraform", target, environment="test")
        exit_code = scanner.scan()

        # Assert
        assert isinstance(exit_code, int)
        assert scanner.log_file.exists()

    def test_scanner_generates_summary(self, test_files_dir):
        """Test that scanner generates proper summary"""
        # Setup
        target = test_files_dir / "cloudformation" / "ec2-instance.yaml"

        if not target.exists():
            pytest.skip(f"Test file not found: {target}")

        # Execute
        scanner = Scanner("cloudformation", target, environment="test")
        exit_code = scanner.scan()

        # Assert - check log file contains expected sections
        log_content = scanner.log_file.read_text()
        assert "Security Scan Report" in log_content
        assert "Scan Summary" in log_content
        assert "Cost Analysis" in log_content or "cost" in log_content.lower()

    def test_scanner_handles_nonexistent_file(self):
        """Test scanner properly handles nonexistent files"""
        # Setup
        target = Path("/nonexistent/file.yaml")

        # Execute
        scanner = Scanner("cloudformation", target, environment="test")
        exit_code = scanner.scan()

        # Assert
        assert exit_code == 1  # Should fail gracefully


class TestNativeIntelligence:
    """Test native intelligence integration"""

    @pytest.fixture
    def test_files_dir(self):
        """Get test files directory"""
        return Path(__file__).parent.parent.parent / "devops_universal_scanner" / "test-files"

    def test_cost_analysis_runs(self, test_files_dir):
        """Test that cost analysis runs without errors"""
        target = test_files_dir / "cloudformation" / "ec2-instance.yaml"

        if not target.exists():
            pytest.skip(f"Test file not found: {target}")

        scanner = Scanner("cloudformation", target, environment="test")
        scanner.scan()

        # Check log contains cost analysis
        log_content = scanner.log_file.read_text()
        assert "Cost Analysis" in log_content or "COST" in log_content

    def test_security_analysis_runs(self, test_files_dir):
        """Test that security analysis runs without errors"""
        target = test_files_dir / "cloudformation" / "ec2-instance.yaml"

        if not target.exists():
            pytest.skip(f"Test file not found: {target}")

        scanner = Scanner("cloudformation", target, environment="test")
        scanner.scan()

        # Check log contains security analysis
        log_content = scanner.log_file.read_text()
        assert "Security Analysis" in log_content or "SECURITY" in log_content

    def test_ami_cve_scanning_runs(self, test_files_dir):
        """Test that AMI CVE scanning runs without errors"""
        target = test_files_dir / "cloudformation" / "ec2-instance.yaml"

        if not target.exists():
            pytest.skip(f"Test file not found: {target}")

        scanner = Scanner("cloudformation", target, environment="test")
        scanner.scan()

        # Check log contains AMI scanning
        log_content = scanner.log_file.read_text()
        assert "AMI" in log_content or "ami-" in log_content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
