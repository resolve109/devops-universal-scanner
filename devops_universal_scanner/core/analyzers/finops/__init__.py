"""
FinOps Intelligence Module
Provides cost awareness, optimization recommendations, and idle resource detection
"""

from devops_universal_scanner.core.analyzers.finops.cost_analyzer import CostAnalyzer
from devops_universal_scanner.core.analyzers.finops.idle_detector import IdleResourceDetector
from devops_universal_scanner.core.analyzers.finops.optimization import OptimizationRecommender

__all__ = [
    "CostAnalyzer",
    "IdleResourceDetector",
    "OptimizationRecommender",
]
