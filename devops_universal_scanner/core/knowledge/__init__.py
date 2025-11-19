"""
Knowledge Module
Policy knowledge base and custom rules engine

Uses local Checkov documentation as knowledge source
Provides fallback when Checkov isn't available
Enables custom rule creation
"""

from devops_universal_scanner.core.knowledge.policy_loader import PolicyKnowledgeLoader, get_policy_loader
from devops_universal_scanner.core.knowledge.custom_rules import CustomRulesEngine, get_custom_rules_engine, CustomRule

__all__ = [
    "PolicyKnowledgeLoader",
    "get_policy_loader",
    "CustomRulesEngine",
    "get_custom_rules_engine",
    "CustomRule",
]
