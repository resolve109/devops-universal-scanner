"""
DevOps Universal Scanner - Native Intelligence Layer
====================================================

A comprehensive scanning orchestration platform that wraps industry-standard
tools (Checkov, CFN-Lint, TFLint, TFSec, Trivy) and adds intelligent analysis:

- FinOps: Cost warnings, idle resource detection, optimization suggestions
- AI/ML: GPU cost analysis, training time estimates, inference optimization
- Security: Enhanced security insights beyond base tool capabilities
- Recommendations: Actionable fixes with context and priorities

This is not just another scanner - it's a DevOps Swiss Army knife with
native intelligence that makes your infrastructure better.
"""

__version__ = "2.0.0"
__author__ = "DevOps Security Team"

# Main modules available for import
from analyzers.core.aggregator import ResultAggregator
from analyzers.reporting.report_generator import EnhancedReportGenerator
from analyzers.finops.cost_analyzer import CostAnalyzer
from analyzers.finops.optimization import OptimizationRecommender

__all__ = [
    "ResultAggregator",
    "EnhancedReportGenerator",
    "CostAnalyzer",
    "OptimizationRecommender",
]
