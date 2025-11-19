"""
GPU Cost Analyzer
Analyzes GPU instance costs and provides AI/ML specific recommendations

Operations:
- analyze_gpu_costs: Calculate GPU instance costs
- recommend_gpu_optimization: Suggest GPU cost optimizations
- estimate_training_costs: Estimate ML training costs
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from devops_universal_scanner.core.data.cost_estimates import is_gpu_instance, AWS_COST_ESTIMATES
from devops_universal_scanner.core.analyzers.finops.cost_analyzer import CostBreakdown


@dataclass
class GPURecommendation:
    """GPU-specific recommendation"""
    resource_name: str
    instance_type: str
    monthly_cost: float
    gpu_type: str
    use_case: str
    recommendation: str
    cost_optimization: List[str]


class GPUCostAnalyzer:
    """
    Analyzes GPU instance costs for AI/ML workloads

    Operations:
    1. identify_gpu_instances - Find all GPU instances
    2. analyze_gpu_costs - Calculate GPU-specific costs
    3. recommend_optimizations - Suggest cost optimizations
    """

    def __init__(self):
        self.gpu_resources: List[CostBreakdown] = []
        self.recommendations: List[GPURecommendation] = []

    def analyze(self, cost_breakdowns: List[CostBreakdown]) -> List[GPURecommendation]:
        """Analyze GPU resources"""
        self.gpu_resources = [cb for cb in cost_breakdowns if cb.is_gpu]

        recommendations = []

        for gpu_resource in self.gpu_resources:
            rec = self._analyze_gpu_instance(gpu_resource)
            if rec:
                recommendations.append(rec)

        self.recommendations = recommendations
        return recommendations

    def _analyze_gpu_instance(self, breakdown: CostBreakdown) -> Optional[GPURecommendation]:
        """Analyze a single GPU instance"""
        if not breakdown.instance_type:
            return None

        instance_type = breakdown.instance_type

        # Determine GPU type and use case
        gpu_info = self._get_gpu_info(instance_type)

        recommendations_list = [
            "[COST] GPU instances are expensive - ensure they're actually needed",
            f"[COST] GPU cost: ${breakdown.hourly_cost:.2f}/hour - minimize idle time",
        ]

        # Add specific recommendations based on instance type
        if "p3" in instance_type.lower() or "p4" in instance_type.lower():
            recommendations_list.extend([
                "[SPOT] Consider Spot Instances for training (up to 70% savings)",
                "[MONITORING] Use CloudWatch to monitor GPU utilization",
                "[GPU] Ensure you're using all GPUs (check nvidia-smi)",
            ])
        elif "g4" in instance_type.lower():
            recommendations_list.extend([
                "[INFO] G4 instances are optimized for inference, not training",
                "Consider G5 for better price/performance for ML inference",
            ])

        recommendation = GPURecommendation(
            resource_name=breakdown.resource_name,
            instance_type=instance_type,
            monthly_cost=breakdown.monthly_cost,
            gpu_type=gpu_info["type"],
            use_case=gpu_info["use_case"],
            recommendation=f"[GPU] GPU Instance: {gpu_info['description']}",
            cost_optimization=recommendations_list
        )

        return recommendation

    def _get_gpu_info(self, instance_type: str) -> Dict[str, str]:
        """Get GPU instance information"""
        instance_lower = instance_type.lower()

        if "p4d" in instance_lower:
            return {
                "type": "NVIDIA A100",
                "use_case": "Large-scale ML training, HPC",
                "description": "8x A100 GPUs (40GB each) - Premium training instance"
            }
        elif "p3" in instance_lower:
            return {
                "type": "NVIDIA V100",
                "use_case": "ML training, deep learning",
                "description": "V100 GPUs - Great for training deep learning models"
            }
        elif "g5" in instance_lower:
            return {
                "type": "NVIDIA A10G",
                "use_case": "ML inference, graphics",
                "description": "A10G GPUs - Optimized for inference and graphics"
            }
        elif "g4dn" in instance_lower:
            return {
                "type": "NVIDIA T4",
                "use_case": "ML inference, video transcoding",
                "description": "T4 GPUs - Cost-effective for inference workloads"
            }
        else:
            return {
                "type": "GPU",
                "use_case": "General GPU workload",
                "description": "GPU-enabled instance"
            }

    def generate_gpu_report(self) -> str:
        """Generate GPU analysis report"""
        if not self.recommendations:
            return ""

        lines = []
        lines.append("")
        lines.append("=" * 80)
        lines.append("[AI/ML] GPU COST ANALYSIS")
        lines.append("=" * 80)
        lines.append("")

        total_gpu_cost = sum(rec.monthly_cost for rec in self.recommendations)

        lines.append(f"[INFO] GPU INSTANCES DETECTED: {len(self.recommendations)}")
        lines.append("[COST] TOTAL GPU COST:")
        lines.append(f"   Monthly:  ${total_gpu_cost:,.2f}")
        lines.append(f"   Daily:    ${total_gpu_cost / 30:,.2f}")
        lines.append(f"   Hourly:   ${total_gpu_cost / 730:,.2f}")
        lines.append("")

        for i, rec in enumerate(self.recommendations, 1):
            lines.append(f"{i}. [GPU] {rec.resource_name}")
            lines.append(f"   Instance: {rec.instance_type}")
            lines.append(f"   GPU Type: {rec.gpu_type}")
            lines.append(f"   Use Case: {rec.use_case}")
            lines.append(f"   Monthly Cost: ${rec.monthly_cost:,.2f}")
            lines.append(f"   Daily Cost: ${rec.monthly_cost / 30:,.2f}")
            lines.append(f"   Hourly Cost: ${rec.monthly_cost / 730:,.2f}")
            lines.append("")
            lines.append("   [RECOMMENDATIONS]")
            for opt in rec.cost_optimization:
                lines.append(f"   {opt}")
            lines.append("")
            lines.append("-" * 80)
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def get_total_gpu_cost(self) -> float:
        """Get total monthly GPU cost"""
        return sum(rec.monthly_cost for rec in self.recommendations)
