"""
Checkov Policy Index
Comprehensive index of all Checkov security policies
Based on: https://github.com/bridgecrewio/checkov/tree/main/docs/5.Policy%20Index
"""

from core.checkov_policies.policy_loader import CheckovPolicyIndex
from core.checkov_policies.policy_categories import PolicyCategory, Severity

__all__ = [
    "CheckovPolicyIndex",
    "PolicyCategory",
    "Severity",
]
