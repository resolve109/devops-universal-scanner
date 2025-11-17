"""
FinOps Intelligence Module
Provides cost awareness, optimization recommendations, and idle resource detection
"""

from analyzers.finops.cost_analyzer import CostAnalyzer
from analyzers.finops.idle_detector import IdleResourceDetector
from analyzers.finops.optimization import OptimizationRecommender

__all__ = [
    "CostAnalyzer",
    "IdleResourceDetector",
    "OptimizationRecommender",
]
