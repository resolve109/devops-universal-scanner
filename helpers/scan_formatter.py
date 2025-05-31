#!/usr/bin/env python3
"""
DevOps Scanner Helper Utilities
Provides formatting, parsing, and utility functions for scan results
"""

import json
import sys
import os
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime

class ScanResultFormatter:
    """Handles formatting and cleaning of scan results"""
    
    @staticmethod
    def format_checkov_code_blocks(checkov_data: Dict) -> Dict:
        """
        Formats Checkov code blocks from array format to readable strings
        Input: [line_num, code_content] arrays
        Output: Clean, readable code strings
        """
        if not isinstance(checkov_data, dict):
            return checkov_data
            
        # Process failed_checks
        if 'results' in checkov_data and 'failed_checks' in checkov_data['results']:
            for check in checkov_data['results']['failed_checks']:
                if 'code_block' in check and isinstance(check['code_block'], list):
                    # Convert array format to readable string
                    code_lines = []
                    for line_data in check['code_block']:
                        if isinstance(line_data, list) and len(line_data) >= 2:
                            line_num, code_content = line_data[0], line_data[1]
                            # Clean up newlines and format nicely
                            clean_code = code_content.rstrip('\n')
                            code_lines.append(f"{line_num:3d} | {clean_code}")
                    
                    check['code_block'] = '\n'.join(code_lines) if code_lines else ""
                    check['code_block_formatted'] = True
        
        # Process passed_checks if they exist
        if 'results' in checkov_data and 'passed_checks' in checkov_data['results']:
            for check in checkov_data['results']['passed_checks']:
                if 'code_block' in check and isinstance(check['code_block'], list):
                    code_lines = []
                    for line_data in check['code_block']:
                        if isinstance(line_data, list) and len(line_data) >= 2:
                            line_num, code_content = line_data[0], line_data[1]
                            clean_code = code_content.rstrip('\n')
                            code_lines.append(f"{line_num:3d} | {clean_code}")
                    
                    check['code_block'] = '\n'.join(code_lines) if code_lines else ""
                    check['code_block_formatted'] = True
        
        return checkov_data
    
    @staticmethod
    def add_scan_metadata(data: Dict, scan_type: str, target: str) -> Dict:
        """Add metadata to scan results"""
        metadata = {
            'scan_metadata': {
                'scan_type': scan_type,
                'target': target,
                'timestamp': datetime.now().isoformat(),
                'scanner_version': '2.0.0',
                'formatted': True
            }
        }
        
        # Insert metadata at the beginning
        result = {**metadata, **data}
        return result
    
    @staticmethod
    def generate_summary(data: Dict) -> Dict:
        """Generate a summary of scan results"""
        summary = {
            'total_issues': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0,
            'tools_used': []
        }
        
        # Count Checkov issues
        if 'checkov' in data and 'results' in data['checkov']:
            checkov_results = data['checkov']['results']
            if 'failed_checks' in checkov_results:
                summary['total_issues'] += len(checkov_results['failed_checks'])
                summary['tools_used'].append('Checkov')
        
        # Count TFSec issues
        if 'tfsec' in data and 'results' in data['tfsec']:
            tfsec_results = data['tfsec']['results']
            summary['total_issues'] += len(tfsec_results)
            summary['tools_used'].append('TFSec')
            
            # Count by severity
            for result in tfsec_results:
                severity = result.get('severity', '').upper()
                if severity == 'CRITICAL':
                    summary['critical_issues'] += 1
                elif severity == 'HIGH':
                    summary['high_issues'] += 1
                elif severity == 'MEDIUM':
                    summary['medium_issues'] += 1
                elif severity == 'LOW':
                    summary['low_issues'] += 1
        
        # Count CFN-Lint issues
        if 'cfn_lint' in data:
            cfn_issues = data['cfn_lint']
            if isinstance(cfn_issues, list):
                summary['total_issues'] += len(cfn_issues)
                summary['tools_used'].append('CFN-Lint')
        
        return summary

class ReportProcessor:
    """Processes and consolidates scan reports"""
    
    def __init__(self, input_file: str, output_file: str, scan_type: str, target: str):
        self.input_file = input_file
        self.output_file = output_file
        self.scan_type = scan_type
        self.target = target
        self.formatter = ScanResultFormatter()
    
    def process(self) -> bool:
        """Process the input file and generate formatted output"""
        try:
            # Read input file
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Format Checkov results
            if 'checkov' in data:
                data['checkov'] = self.formatter.format_checkov_code_blocks(data['checkov'])
            
            # Add metadata
            data = self.formatter.add_scan_metadata(data, self.scan_type, self.target)
            
            # Generate summary
            data['summary'] = self.formatter.generate_summary(data)
            
            # Write formatted output
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Formatted report saved: {self.output_file}")
            print(f"  Total issues found: {data['summary']['total_issues']}")
            print(f"  Tools used: {', '.join(data['summary']['tools_used'])}")
            
            return True
            
        except Exception as e:
            print(f"Error processing report: {e}", file=sys.stderr)
            return False

def main():
    parser = argparse.ArgumentParser(description='DevOps Scanner Helper Utilities')
    parser.add_argument('command', choices=['format-report', 'format-checkov'], 
                       help='Command to execute')
    parser.add_argument('--input', '-i', required=True, help='Input file path')
    parser.add_argument('--output', '-o', required=True, help='Output file path')
    parser.add_argument('--scan-type', help='Type of scan (terraform, cloudformation, etc.)')
    parser.add_argument('--target', help='Scan target (file or directory)')
    
    args = parser.parse_args()
    
    if args.command == 'format-report':
        if not args.scan_type or not args.target:
            print("Error: --scan-type and --target required for format-report", file=sys.stderr)
            sys.exit(1)
        
        processor = ReportProcessor(args.input, args.output, args.scan_type, args.target)
        if processor.process():
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif args.command == 'format-checkov':
        try:
            with open(args.input, 'r') as f:
                data = json.load(f)
            
            formatter = ScanResultFormatter()
            formatted_data = formatter.format_checkov_code_blocks(data)
            
            with open(args.output, 'w') as f:
                json.dump(formatted_data, f, indent=2)
            
            print(f"✓ Checkov results formatted: {args.output}")
            
        except Exception as e:
            print(f"Error formatting Checkov results: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()
