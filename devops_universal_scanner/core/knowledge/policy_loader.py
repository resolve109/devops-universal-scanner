"""
Policy Knowledge Loader
Parses Checkov policy documentation from markdown files
Provides local knowledge base when Checkov isn't available
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


@dataclass
class PolicyInfo:
    """Information about a security policy"""
    id: str
    name: str
    description: str
    severity: str
    category: str
    resource_types: List[str]
    guideline: str
    framework: str  # terraform, cloudformation, kubernetes, etc.


class PolicyKnowledgeLoader:
    """
    Loads and indexes Checkov policy documentation
    Provides fallback knowledge when Checkov isn't available
    """

    def __init__(self, docs_path: Optional[Path] = None):
        """
        Initialize policy knowledge loader

        Args:
            docs_path: Path to docs folder (default: project_root/docs)
        """
        if docs_path is None:
            # Default to project docs folder
            docs_path = Path(__file__).parent.parent.parent / "docs"

        self.docs_path = Path(docs_path)
        self.policy_index_path = self.docs_path / "5.Policy Index"
        self.custom_policies_path = self.docs_path / "3.Custom Policies"

        # Policy database
        self.policies: Dict[str, PolicyInfo] = {}
        self.policies_by_framework: Dict[str, List[PolicyInfo]] = {}
        self.policies_by_category: Dict[str, List[PolicyInfo]] = {}

        # Load policies if docs exist
        if self.policy_index_path.exists():
            self._load_all_policies()

    def _load_all_policies(self):
        """Load all policy documentation from markdown files"""
        policy_files = list(self.policy_index_path.glob("*.md"))

        for policy_file in policy_files:
            framework = policy_file.stem  # e.g., "terraform", "cloudformation"
            if framework == "all":
                continue  # Skip the all.md file

            policies = self._parse_policy_file(policy_file, framework)
            for policy in policies:
                self.policies[policy.id] = policy

                # Index by framework
                if framework not in self.policies_by_framework:
                    self.policies_by_framework[framework] = []
                self.policies_by_framework[framework].append(policy)

                # Index by category
                if policy.category not in self.policies_by_category:
                    self.policies_by_category[policy.category] = []
                self.policies_by_category[policy.category].append(policy)

    def _parse_policy_file(self, file_path: Path, framework: str) -> List[PolicyInfo]:
        """
        Parse a policy markdown file and extract policy information

        Args:
            file_path: Path to markdown file
            framework: Framework name (terraform, cloudformation, etc.)

        Returns:
            List of PolicyInfo objects
        """
        policies = []

        try:
            content = file_path.read_text(encoding='utf-8')

            # Parse markdown tables
            # Example format:
            # | Policy ID | Name | Severity | Category |
            # | CKV_AWS_1 | Ensure IAM ... | HIGH | IAM |

            # Find all table rows (simplified parser)
            table_pattern = r'\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|'
            matches = re.findall(table_pattern, content)

            for match in matches:
                if len(match) < 4:
                    continue

                # Skip header rows
                if 'Policy' in match[0] or '---' in match[0]:
                    continue

                policy_id = match[0].strip()
                name = match[1].strip()
                severity = match[2].strip() if len(match) > 2 else "MEDIUM"
                category = match[3].strip() if len(match) > 3 else "General"

                # Only process if we have a valid policy ID
                if policy_id and policy_id.startswith('CKV_'):
                    policy = PolicyInfo(
                        id=policy_id,
                        name=name,
                        description=name,
                        severity=severity.upper(),
                        category=category,
                        resource_types=[],  # Would need deeper parsing
                        guideline="",  # Would need deeper parsing
                        framework=framework
                    )
                    policies.append(policy)

        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")

        return policies

    def get_policy(self, policy_id: str) -> Optional[PolicyInfo]:
        """
        Get policy information by ID

        Args:
            policy_id: Policy ID (e.g., "CKV_AWS_1")

        Returns:
            PolicyInfo if found, None otherwise
        """
        return self.policies.get(policy_id)

    def get_policies_for_framework(self, framework: str) -> List[PolicyInfo]:
        """
        Get all policies for a specific framework

        Args:
            framework: Framework name (terraform, cloudformation, etc.)

        Returns:
            List of PolicyInfo objects
        """
        return self.policies_by_framework.get(framework, [])

    def get_policies_for_category(self, category: str) -> List[PolicyInfo]:
        """
        Get all policies for a specific category

        Args:
            category: Category name (IAM, Networking, Encryption, etc.)

        Returns:
            List of PolicyInfo objects
        """
        return self.policies_by_category.get(category, [])

    def search_policies(self, query: str) -> List[PolicyInfo]:
        """
        Search policies by name or description

        Args:
            query: Search query

        Returns:
            List of matching PolicyInfo objects
        """
        query_lower = query.lower()
        results = []

        for policy in self.policies.values():
            if (query_lower in policy.name.lower() or
                query_lower in policy.description.lower() or
                query_lower in policy.category.lower()):
                results.append(policy)

        return results

    def get_frameworks(self) -> List[str]:
        """
        Get list of all available frameworks

        Returns:
            List of framework names
        """
        return list(self.policies_by_framework.keys())

    def get_categories(self) -> List[str]:
        """
        Get list of all policy categories

        Returns:
            List of category names
        """
        return list(self.policies_by_category.keys())

    def get_stats(self) -> Dict[str, int]:
        """
        Get policy database statistics

        Returns:
            Dictionary with statistics
        """
        return {
            "total_policies": len(self.policies),
            "total_frameworks": len(self.policies_by_framework),
            "total_categories": len(self.policies_by_category),
            "policies_by_framework": {
                framework: len(policies)
                for framework, policies in self.policies_by_framework.items()
            }
        }

    def is_available(self) -> bool:
        """
        Check if policy knowledge base is available

        Returns:
            True if docs are loaded, False otherwise
        """
        return len(self.policies) > 0

    def enrich_finding(self, finding_id: str) -> Optional[Dict[str, str]]:
        """
        Enrich a finding with policy knowledge

        Args:
            finding_id: Policy/finding ID

        Returns:
            Dictionary with enriched information or None
        """
        policy = self.get_policy(finding_id)
        if policy:
            return {
                "policy_name": policy.name,
                "description": policy.description,
                "severity": policy.severity,
                "category": policy.category,
                "framework": policy.framework,
                "guideline": policy.guideline
            }
        return None


# Global instance
_policy_loader = None

def get_policy_loader() -> PolicyKnowledgeLoader:
    """
    Get or create global policy loader instance

    Returns:
        PolicyKnowledgeLoader instance
    """
    global _policy_loader
    if _policy_loader is None:
        _policy_loader = PolicyKnowledgeLoader()
    return _policy_loader
