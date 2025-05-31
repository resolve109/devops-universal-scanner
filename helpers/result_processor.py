#!/usr/bin/env python3
"""
Result Processor Helper
Handles post-scan result processing, formatting, and analysis
"""

import os
import json
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import the existing ScanResultFormatter from scan_formatter.py
current_dir = os.path.dirname(__file__)
formatter_path = os.path.join(current_dir, 'scan_formatter.py')

try:
    spec = importlib.util.spec_from_file_location("scan_formatter", formatter_path)
    scan_formatter_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scan_formatter_module)
    ScanResultFormatter = scan_formatter_module.ScanResultFormatter
except Exception as e:
    print(f"Warning: Could not import ScanResultFormatter: {e}")
    # Fallback - create a basic formatter if the module doesn't exist
    class ScanResultFormatter:
        @staticmethod
        def format_checkov_code_blocks(data):
            return data
        @staticmethod
        def add_scan_metadata(data, scan_type, target):
            return data
        @staticmethod
        def generate_summary(data):
            return {"total_issues": 0, "tools_used": []}

class ResultProcessor:
    """Processes and analyzes scan results"""
    
    def __init__(self):
        self.formatter = ScanResultFormatter()        # Expected output files by scanner type (now using .log format)
        self.output_files = {
            'terraform': 'terraform-scan-report.log',
            'cloudformation': 'cloudformation-scan-report.log',
            'bicep': 'azure-bicep-scan-report.log',
            'arm': 'azure-arm-scan-report.log',
            'gcp': 'gcp-scan-report.log',
            'docker': 'docker-scan-report.log'
        }
        
    def process_scan_results(self, scan_type: str, work_dir: str) -> bool:
        """Process results from a completed scan"""
        
        try:
            # Get expected output file
            output_file = self.output_files.get(scan_type)
            if not output_file:
                print(f"⚠️  Warning: Unknown scan type '{scan_type}', skipping result processing")
                return True
                
            output_path = Path(work_dir) / output_file
            
            # Check if output file exists
            if not output_path.exists():
                print(f"⚠️  Warning: Expected output file not found: {output_file}")
                print("Scan may have failed or produced no results")
                return False
                
            print(f"📊 Processing scan log results: {output_file}")
            
            # For log files, we'll analyze the content and generate summary
            with open(output_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # Analyze log content for key information
            analysis = self._analyze_log_content(log_content, scan_type)
            
            # Generate summary report
            self._generate_log_summary_report(analysis, work_dir, scan_type, output_file)
            
            print(f"✅ Log results processed successfully")
            print(f"   Original: {output_file}")
            print(f"   Summary: {scan_type}-summary.txt")
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing scan results: {e}")
            return False
    
    def _analyze_log_content(self, log_content: str, scan_type: str) -> Dict[str, Any]:
        """Analyze log content to extract key information"""
        
        lines = log_content.split('\n')
        analysis = {
            'total_lines': len(lines),
            'success_count': 0,
            'warning_count': 0,
            'error_count': 0,
            'tools_used': [],
            'key_findings': [],
            'scan_sections': []
        }
        
        current_section = None
        
        for line in lines:
            # Count status indicators
            if '✅ SUCCESS:' in line:
                analysis['success_count'] += 1
            elif '⚠️  WARNING:' in line:
                analysis['warning_count'] += 1
            elif '❌ ERROR:' in line:
                analysis['error_count'] += 1
            
            # Track sections
            if '============================================================' in line:
                continue
            elif line.strip().startswith('[') and ']' in line and any(word in line.upper() for word in ['SCAN', 'CHECK', 'VALIDATION', 'ANALYSIS']):
                current_section = line.strip()
                analysis['scan_sections'].append(current_section)
            
            # Detect tools used
            if any(tool in line.lower() for tool in ['checkov', 'tfsec', 'tflint', 'trivy', 'cfn-lint', 'bicep', 'arm-ttk', 'gcloud']):
                for tool in ['checkov', 'tfsec', 'tflint', 'trivy', 'cfn-lint', 'bicep', 'arm-ttk', 'gcloud']:
                    if tool in line.lower() and tool not in analysis['tools_used']:
                        analysis['tools_used'].append(tool)
            
            # Extract key findings (lines with specific patterns)
            if any(keyword in line.lower() for keyword in ['failed', 'passed', 'critical', 'high', 'medium', 'low', 'vulnerability', 'secret']):
                if line.strip() and not line.startswith('[') and not line.startswith('='):
                    analysis['key_findings'].append(line.strip())
        
        return analysis
    
    def _generate_log_summary_report(self, 
                                   analysis: Dict[str, Any], 
                                   work_dir: str, 
                                   scan_type: str,
                                   log_file: str) -> None:
        """Generate a human-readable summary report from log analysis"""
        
        summary_content = []
        summary_content.append("=" * 60)
        summary_content.append(f"DevOps Scanner - {scan_type.title()} Log Summary")
        summary_content.append("=" * 60)
        summary_content.append("")
        
        # Basic information
        summary_content.append("📋 Scan Information:")
        summary_content.append(f"   Scan Type: {scan_type}")
        summary_content.append(f"   Log File: {log_file}")
        summary_content.append(f"   Total Log Lines: {analysis['total_lines']}")
        summary_content.append("")
        
        # Status summary
        summary_content.append("📊 Scan Status Summary:")
        summary_content.append(f"   ✅ Successes: {analysis['success_count']}")
        summary_content.append(f"   ⚠️  Warnings: {analysis['warning_count']}")
        summary_content.append(f"   ❌ Errors: {analysis['error_count']}")
        summary_content.append("")
        
        # Tools used
        if analysis['tools_used']:
            summary_content.append("🔧 Tools Used:")
            for tool in analysis['tools_used']:
                summary_content.append(f"   • {tool}")
            summary_content.append("")
        
        # Scan sections
        if analysis['scan_sections']:
            summary_content.append("📑 Scan Sections:")
            for section in analysis['scan_sections']:
                summary_content.append(f"   • {section}")
            summary_content.append("")
        
        # Key findings (limited to first 20 to avoid clutter)
        if analysis['key_findings']:
            summary_content.append("🔍 Key Findings (first 20):")
            for finding in analysis['key_findings'][:20]:
                if len(finding) > 100:
                    finding = finding[:97] + "..."
                summary_content.append(f"   • {finding}")
            if len(analysis['key_findings']) > 20:
                summary_content.append(f"   ... and {len(analysis['key_findings']) - 20} more findings")
            summary_content.append("")
        
        # Overall assessment
        summary_content.append("📈 Overall Assessment:")
        if analysis['error_count'] > 0:
            summary_content.append("   🔴 CRITICAL: Scan completed with errors")
        elif analysis['warning_count'] > 0:
            summary_content.append("   🟡 WARNING: Scan completed with warnings")
        else:
            summary_content.append("   🟢 SUCCESS: Scan completed successfully")
        
        summary_content.append("")
        summary_content.append("📄 For detailed results, see the full log file:")
        summary_content.append(f"   {log_file}")
        summary_content.append("")
        summary_content.append("=" * 60)
        
        # Write summary file
        summary_path = Path(work_dir) / f"{scan_type}-summary.txt"
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(summary_content))
        except Exception as e:
            print(f"Warning: Could not write summary file: {e}")
            
    def _generate_summary_report(self, 
                               scan_data: Dict[str, Any], 
                               work_dir: str, 
                               scan_type: str) -> None:
        """Generate a human-readable summary report"""
        
        summary = scan_data.get('summary', {})
        metadata = scan_data.get('scan_metadata', {})
        
        summary_content = []
        summary_content.append("=" * 60)
        summary_content.append(f"DevOps Scanner - {scan_type.title()} Results Summary")
        summary_content.append("=" * 60)
        summary_content.append("")
        
        # Metadata
        if metadata:
            summary_content.append("📋 Scan Information:")
            summary_content.append(f"   Scan Type: {metadata.get('scan_type', 'Unknown')}")
            summary_content.append(f"   Target: {metadata.get('target', 'Unknown')}")
            summary_content.append(f"   Timestamp: {metadata.get('timestamp', 'Unknown')}")
            summary_content.append(f"   Scanner Version: {metadata.get('scanner_version', 'Unknown')}")
            summary_content.append("")
            
        # Summary statistics
        summary_content.append("📊 Results Summary:")
        summary_content.append(f"   Total Issues: {summary.get('total_issues', 0)}")
        
        if summary.get('critical_issues', 0) > 0:
            summary_content.append(f"   🔴 Critical: {summary.get('critical_issues', 0)}")
        if summary.get('high_issues', 0) > 0:
            summary_content.append(f"   🟠 High: {summary.get('high_issues', 0)}")
        if summary.get('medium_issues', 0) > 0:
            summary_content.append(f"   🟡 Medium: {summary.get('medium_issues', 0)}")
        if summary.get('low_issues', 0) > 0:
            summary_content.append(f"   🔵 Low: {summary.get('low_issues', 0)}")
            
        tools_used = summary.get('tools_used', [])
        if tools_used:
            summary_content.append(f"   Tools Used: {', '.join(tools_used)}")
            
        summary_content.append("")
        
        # Add specific scanner details
        self._add_scanner_specific_details(scan_data, summary_content, scan_type)
        
        # Recommendations
        summary_content.append("💡 Recommendations:")
        if summary.get('total_issues', 0) == 0:
            summary_content.append("   ✅ No security issues found! Great job!")
        else:
            summary_content.append("   📝 Review the detailed JSON report for specific issues")
            summary_content.append("   🔧 Address critical and high severity issues first")
            summary_content.append("   📚 Refer to scanner documentation for remediation guidance")
            
        summary_content.append("")
        summary_content.append("=" * 60)
        
        # Write summary file
        summary_path = Path(work_dir) / f"{scan_type}-summary.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_content))
            
    def _add_scanner_specific_details(self, 
                                    scan_data: Dict[str, Any], 
                                    summary_content: List[str], 
                                    scan_type: str) -> None:
        """Add scanner-specific details to summary"""
        
        # Checkov details (common for IaC scanners)
        if 'checkov' in scan_data:
            checkov_data = scan_data['checkov']
            if 'results' in checkov_data:
                results = checkov_data['results']
                failed_checks = len(results.get('failed_checks', []))
                passed_checks = len(results.get('passed_checks', []))
                
                summary_content.append("🔍 Checkov Analysis:")
                summary_content.append(f"   Failed Checks: {failed_checks}")
                summary_content.append(f"   Passed Checks: {passed_checks}")
                summary_content.append("")
                
        # TFSec details (for Terraform)
        if 'tfsec' in scan_data and scan_type == 'terraform':
            tfsec_results = scan_data['tfsec'].get('results', [])
            summary_content.append("🔒 TFSec Analysis:")
            summary_content.append(f"   Security Issues: {len(tfsec_results)}")
            summary_content.append("")
            
        # Docker-specific details
        if scan_type == 'docker':
            if 'trivy' in scan_data:
                summary_content.append("🐳 Trivy Analysis:")
                summary_content.append("   Container vulnerability scan completed")
                summary_content.append("")
                
    def get_scan_statistics(self, work_dir: str) -> Dict[str, Any]:
        """Get statistics from all scan results in directory"""
        
        stats = {
            'total_scans': 0,
            'total_issues': 0,
            'scan_files': [],
            'by_type': {}
        }
        
        work_path = Path(work_dir)
        
        # Look for scan result files
        for scan_type, filename in self.output_files.items():
            file_path = work_path / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    summary = data.get('summary', {})
                    issues = summary.get('total_issues', 0)
                    
                    stats['total_scans'] += 1
                    stats['total_issues'] += issues
                    stats['scan_files'].append(filename)
                    stats['by_type'][scan_type] = {
                        'issues': issues,
                        'file': filename,
                        'tools': summary.get('tools_used', [])
                    }
                    
                except Exception:
                    continue
                    
        return stats
