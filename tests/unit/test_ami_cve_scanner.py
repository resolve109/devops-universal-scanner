"""
Unit tests for AMI CVE Scanner

Tests AMI vulnerability detection and alternative recommendations.
"""

import pytest
from devops_universal_scanner.core.cve.ami_cve_scanner import AMICVEScanner, AMICVE


class TestAMICVEScanner:
    """Test AMI CVE Scanner functionality"""

    @pytest.fixture
    def scanner(self):
        """Create AMI CVE Scanner instance"""
        return AMICVEScanner(region="us-east-1")

    def test_check_known_vulnerable_ami(self, scanner):
        """Test detection of known vulnerable AMI"""
        result = scanner.check_ami("ami-0abcdef1234567890")

        assert result.has_cve is True
        assert "CVE-2024-12345" in result.cve_ids
        assert result.severity == "HIGH"
        assert len(result.suggested_alternatives) > 0

    def test_check_clean_ami(self, scanner):
        """Test detection of clean AMI"""
        result = scanner.check_ami("ami-0123456789abcdef0")

        assert result.has_cve is False
        assert result.is_outdated is False
        assert result.severity == "INFO"

    def test_check_placeholder_ami(self, scanner):
        """Test detection of placeholder AMI"""
        result = scanner.check_ami("ami-0000000000000000")

        assert result.severity == "LOW"
        assert "placeholder" in result.recommendation.lower()

    def test_extract_amis_from_cloudformation(self, scanner):
        """Test extracting AMI IDs from CloudFormation template"""
        template_content = """
        Resources:
          Instance1:
            Type: AWS::EC2::Instance
            Properties:
              ImageId: ami-0abcdef1234567890
          Instance2:
            Type: AWS::EC2::Instance
            Properties:
              ImageId: ami-0123456789abcdef0
        """

        amis = scanner.extract_amis_from_template(template_content, "cloudformation")

        assert len(amis) == 2
        assert "ami-0abcdef1234567890" in amis
        assert "ami-0123456789abcdef0" in amis

    def test_extract_amis_from_terraform(self, scanner):
        """Test extracting AMI IDs from Terraform template"""
        template_content = """
        resource "aws_instance" "example" {
          ami           = "ami-0abcdef1234567890"
          instance_type = "t3.micro"
        }
        """

        amis = scanner.extract_amis_from_template(template_content, "terraform")

        assert len(amis) == 1
        assert "ami-0abcdef1234567890" in amis

    def test_scan_template_with_vulnerable_ami(self, scanner):
        """Test scanning template containing vulnerable AMI"""
        template_content = """
        ImageId: ami-0abcdef1234567890
        """

        results = scanner.scan_template(template_content, "cloudformation")

        assert len(results) == 1
        assert results[0].has_cve is True
        assert results[0].ami_id == "ami-0abcdef1234567890"

    def test_generate_report(self, scanner):
        """Test generating AMI CVE report"""
        template_content = """
        ImageId: ami-0abcdef1234567890
        """

        scanner.scan_template(template_content, "cloudformation")
        report = scanner.generate_report()

        assert "AMI SECURITY SCAN" in report
        assert "ami-0abcdef1234567890" in report
        assert "CVE-2024-12345" in report
        assert "SUGGESTED ALTERNATIVES" in report

    def test_suggested_alternatives_provided(self, scanner):
        """Test that suggested alternatives are provided for vulnerable AMIs"""
        result = scanner.check_ami("ami-0abcdef1234567890")

        assert len(result.suggested_alternatives) > 0
        alt = result.suggested_alternatives[0]
        assert hasattr(alt, 'ami_id')
        assert hasattr(alt, 'distribution')
        assert hasattr(alt, 'region')
        assert alt.ami_id.startswith('ami-')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
