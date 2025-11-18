"""
Custom Rules Engine
Creates custom security rules based on policy knowledge base
Extends Checkov with additional checks
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
import re


@dataclass
class CustomRule:
    """Custom security rule"""
    id: str
    name: str
    description: str
    severity: str
    resource_pattern: str  # Regex pattern for resource types
    check_function: callable
    framework: str


class CustomRulesEngine:
    """
    Custom rules engine for enhanced security scanning
    Based on policy knowledge base
    """

    def __init__(self):
        self.rules: Dict[str, CustomRule] = {}
        self._register_default_rules()

    def _register_default_rules(self):
        """Register default custom rules"""

        # FinOps rule: Detect oversized instances
        self.register_rule(CustomRule(
            id="CKV_CUSTOM_FINOPS_001",
            name="Detect oversized instances for development",
            description="Development environments shouldn't use production-grade instances",
            severity="MEDIUM",
            resource_pattern=r"aws_instance|azurerm_virtual_machine",
            check_function=self._check_oversized_dev_instance,
            framework="terraform"
        ))

        # FinOps rule: Detect 24/7 non-production resources
        self.register_rule(CustomRule(
            id="CKV_CUSTOM_FINOPS_002",
            name="Detect 24/7 non-production resources",
            description="Non-production resources should use business hours scheduling",
            severity="LOW",
            resource_pattern=r"aws_instance|aws_db_instance",
            check_function=self._check_24_7_non_prod,
            framework="terraform"
        ))

        # Security rule: Detect hardcoded pricing
        self.register_rule(CustomRule(
            id="CKV_CUSTOM_SEC_001",
            name="Detect potential cost abuse patterns",
            description="Resources configured for maximum scale without limits",
            severity="HIGH",
            resource_pattern=r"aws_autoscaling_group",
            check_function=self._check_autoscaling_limits,
            framework="terraform"
        ))

        # AI/ML rule: GPU instances without optimization
        self.register_rule(CustomRule(
            id="CKV_CUSTOM_AIML_001",
            name="GPU instances without spot instance configuration",
            description="AI/ML GPU instances should consider spot instances for training",
            severity="MEDIUM",
            resource_pattern=r"aws_instance.*p[34].*|.*g[45].*",
            check_function=self._check_gpu_optimization,
            framework="terraform"
        ))

    def register_rule(self, rule: CustomRule):
        """
        Register a custom rule

        Args:
            rule: CustomRule object
        """
        self.rules[rule.id] = rule

    def _check_oversized_dev_instance(self, resource: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Check if development environment uses oversized instances"""
        env = context.get('environment', 'development').lower()
        if env in ['development', 'dev', 'staging', 'test']:
            instance_type = resource.get('instance_type', '')
            # Check for large instance types
            if any(size in instance_type.lower() for size in ['xlarge', '2xlarge', '4xlarge', '8xlarge']):
                return f"Development environment using oversized instance: {instance_type}"
        return None

    def _check_24_7_non_prod(self, resource: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Check if non-production resources run 24/7"""
        env = context.get('environment', 'development').lower()
        if env in ['development', 'dev', 'staging', 'test']:
            # Check for auto-stop/start scheduling
            tags = resource.get('tags', {})
            if not any(key in tags for key in ['AutoStop', 'Schedule', 'BusinessHours']):
                return "Non-production resource without business hours scheduling"
        return None

    def _check_autoscaling_limits(self, resource: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Check autoscaling group limits"""
        max_size = resource.get('max_size', 0)
        if isinstance(max_size, int) and max_size > 100:
            return f"Autoscaling group with very high max_size: {max_size}. Consider setting limits."
        return None

    def _check_gpu_optimization(self, resource: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Check GPU instance optimization"""
        instance_type = resource.get('instance_type', '').lower()
        if any(gpu in instance_type for gpu in ['p3', 'p4', 'g4', 'g5']):
            # Check if spot instance strategy is configured
            if 'spot' not in str(resource).lower():
                return f"GPU instance {instance_type} without spot instance configuration (70-90% savings)"
        return None

    def run_rules(self, resources: List[Dict[str, Any]], framework: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run all custom rules against resources

        Args:
            resources: List of resources to check
            framework: Framework name (terraform, cloudformation, etc.)
            context: Context information (environment, etc.)

        Returns:
            List of findings
        """
        findings = []

        for resource in resources:
            resource_type = resource.get('type', '')

            for rule in self.rules.values():
                # Check if rule applies to this framework
                if rule.framework != framework:
                    continue

                # Check if rule applies to this resource type
                if re.search(rule.resource_pattern, resource_type, re.IGNORECASE):
                    try:
                        result = rule.check_function(resource, context)
                        if result:
                            findings.append({
                                'rule_id': rule.id,
                                'rule_name': rule.name,
                                'description': rule.description,
                                'severity': rule.severity,
                                'resource': resource.get('name', 'unknown'),
                                'resource_type': resource_type,
                                'message': result,
                                'framework': framework
                            })
                    except Exception as e:
                        print(f"Warning: Custom rule {rule.id} failed: {e}")

        return findings

    def get_rule(self, rule_id: str) -> Optional[CustomRule]:
        """Get a rule by ID"""
        return self.rules.get(rule_id)

    def get_rules_for_framework(self, framework: str) -> List[CustomRule]:
        """Get all rules for a framework"""
        return [rule for rule in self.rules.values() if rule.framework == framework]

    def get_stats(self) -> Dict[str, int]:
        """Get custom rules statistics"""
        return {
            "total_rules": len(self.rules),
            "rules_by_framework": self._count_by_framework(),
            "rules_by_severity": self._count_by_severity()
        }

    def _count_by_framework(self) -> Dict[str, int]:
        """Count rules by framework"""
        counts = {}
        for rule in self.rules.values():
            counts[rule.framework] = counts.get(rule.framework, 0) + 1
        return counts

    def _count_by_severity(self) -> Dict[str, int]:
        """Count rules by severity"""
        counts = {}
        for rule in self.rules.values():
            counts[rule.severity] = counts.get(rule.severity, 0) + 1
        return counts


# Global instance
_custom_rules_engine = None

def get_custom_rules_engine() -> CustomRulesEngine:
    """
    Get or create global custom rules engine instance

    Returns:
        CustomRulesEngine instance
    """
    global _custom_rules_engine
    if _custom_rules_engine is None:
        _custom_rules_engine = CustomRulesEngine()
    return _custom_rules_engine
