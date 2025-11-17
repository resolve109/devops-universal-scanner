"""
FinOps Optimization Recommender
Provides actionable cost-saving recommendations

Operations:
- analyze_business_hours: Recommend business hours scheduling
- analyze_reserved_vs_ondemand: Compare reserved vs pay-as-you-go
- analyze_rightsizing: Recommend appropriate instance sizes
- analyze_spot_opportunities: Identify spot instance opportunities
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from analyzers.finops.cost_analyzer import CostBreakdown


@dataclass
class OptimizationRecommendation:
    """A cost optimization recommendation"""
    category: str  # 'business_hours', 'reserved', 'rightsizing', 'spot', etc.
    severity: str  # 'high', 'medium', 'low'
    resource_name: str
    resource_type: str
    current_monthly_cost: float
    potential_monthly_savings: float
    savings_percentage: float
    recommendation: str
    implementation_steps: List[str]


class OptimizationRecommender:
    """
    Analyzes resources and provides FinOps optimization recommendations

    Operations:
    1. recommend_business_hours - Schedule resources for business hours only
    2. recommend_reserved_instances - Compare reserved vs on-demand pricing
    3. recommend_rightsizing - Suggest appropriate instance sizes
    4. recommend_spot_instances - Identify spot instance opportunities
    5. recommend_storage_optimization - Optimize storage costs
    """

    def __init__(self):
        self.recommendations: List[OptimizationRecommendation] = []

    def analyze_all(self, cost_breakdowns: List[CostBreakdown], environment: str = "development") -> List[OptimizationRecommendation]:
        """
        Analyze all resources and generate recommendations

        Args:
            cost_breakdowns: List of resource cost breakdowns
            environment: Environment type (development, staging, production)

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        for breakdown in cost_breakdowns:
            # Business hours analysis
            if environment in ["development", "staging", "testing", "demo"]:
                biz_hours_rec = self._analyze_business_hours(breakdown, environment)
                if biz_hours_rec:
                    recommendations.append(biz_hours_rec)

            # Reserved instance analysis (for production or long-running resources)
            if environment == "production" or breakdown.monthly_cost > 100:
                reserved_rec = self._analyze_reserved_instances(breakdown)
                if reserved_rec:
                    recommendations.append(reserved_rec)

            # Spot instance analysis
            spot_rec = self._analyze_spot_opportunities(breakdown, environment)
            if spot_rec:
                recommendations.append(spot_rec)

            # Storage optimization
            if "storage" in breakdown.resource_type.lower() or "ebs" in breakdown.resource_type.lower():
                storage_rec = self._analyze_storage_optimization(breakdown)
                if storage_rec:
                    recommendations.append(storage_rec)

        self.recommendations = recommendations
        return recommendations

    def _analyze_business_hours(self, breakdown: CostBreakdown, environment: str) -> Optional[OptimizationRecommendation]:
        """
        Analyze if resource should run only during business hours

        Business hours assumption: Mon-Fri, 9am-6pm (45 hours/week)
        vs 24/7 (168 hours/week) = 73% savings
        """
        # Only recommend for compute resources
        compute_types = ["aws_instance", "aws_db_instance", "aws_eks_cluster",
                        "aws_sagemaker_notebook_instance", "azurerm_virtual_machine"]

        if breakdown.resource_type not in compute_types:
            return None

        # Don't recommend for production
        if environment == "production":
            return None

        # Calculate savings from business hours only (45 hours/week vs 168 hours/week)
        business_hours_weekly = 45  # Mon-Fri, 9am-6pm
        total_hours_weekly = 168

        usage_ratio = business_hours_weekly / total_hours_weekly  # ~0.27
        savings_ratio = 1 - usage_ratio  # ~0.73 = 73% savings

        potential_savings = breakdown.monthly_cost * savings_ratio

        # Only recommend if savings are meaningful (> $10/month)
        if potential_savings < 10:
            return None

        recommendation = OptimizationRecommendation(
            category="business_hours",
            severity="high" if potential_savings > 100 else "medium",
            resource_name=breakdown.resource_name,
            resource_type=breakdown.resource_type,
            current_monthly_cost=breakdown.monthly_cost,
            potential_monthly_savings=potential_savings,
            savings_percentage=savings_ratio * 100,
            recommendation=f"⏰ Schedule '{breakdown.resource_name}' for business hours only ({environment} environment)",
            implementation_steps=[
                f"1. Create EventBridge (CloudWatch Events) rules to:",
                f"   - START: Monday-Friday at 8:00 AM (before work hours)",
                f"   - STOP: Monday-Friday at 7:00 PM (after work hours)",
                f"2. Use AWS Instance Scheduler or similar automation",
                f"3. Estimated running time: ~45 hours/week instead of 168 hours/week",
                f"4. Monthly savings: ${potential_savings:.2f} ({savings_ratio*100:.0f}% reduction)",
                f"5. Annual savings: ${potential_savings * 12:.2f}",
            ]
        )

        return recommendation

    def _analyze_reserved_instances(self, breakdown: CostBreakdown) -> Optional[OptimizationRecommendation]:
        """
        Analyze if reserved instances would be more cost-effective

        Reserved Instance savings: ~40-60% for 1-year, ~60-75% for 3-year
        """
        # Only for compute resources
        compute_types = ["aws_instance", "aws_db_instance", "aws_elasticache_cluster"]

        if breakdown.resource_type not in compute_types:
            return None

        # Only recommend for resources with significant monthly cost
        if breakdown.monthly_cost < 50:
            return None

        # Assume 1-year Reserved Instance with ~50% savings
        reserved_savings_ratio = 0.50
        potential_savings = breakdown.monthly_cost * reserved_savings_ratio

        recommendation = OptimizationRecommendation(
            category="reserved_instances",
            severity="high" if potential_savings > 200 else "medium",
            resource_name=breakdown.resource_name,
            resource_type=breakdown.resource_type,
            current_monthly_cost=breakdown.monthly_cost,
            potential_monthly_savings=potential_savings,
            savings_percentage=reserved_savings_ratio * 100,
            recommendation=f"💰 Switch to Reserved Instances for '{breakdown.resource_name}' (production workload)",
            implementation_steps=[
                f"Current Cost (On-Demand): ${breakdown.monthly_cost:.2f}/month",
                f"",
                f"Reserved Instance Options:",
                f"1. 1-Year, No Upfront: ~${breakdown.monthly_cost * 0.60:.2f}/month (40% savings)",
                f"2. 1-Year, Partial Upfront: ~${breakdown.monthly_cost * 0.50:.2f}/month (50% savings)",
                f"3. 3-Year, All Upfront: ~${breakdown.monthly_cost * 0.35:.2f}/month (65% savings)",
                f"",
                f"Recommended: 1-Year Partial Upfront Reserved Instance",
                f"   Monthly cost: ${breakdown.monthly_cost * 0.50:.2f}",
                f"   Monthly savings: ${potential_savings:.2f}",
                f"   Annual savings: ${potential_savings * 12:.2f}",
                f"",
                f"Implementation:",
                f"1. Review AWS Cost Explorer for utilization patterns",
                f"2. Purchase Reserved Instance via AWS Console or CLI",
                f"3. RI automatically applies to matching instances",
            ]
        )

        return recommendation

    def _analyze_spot_opportunities(self, breakdown: CostBreakdown, environment: str) -> Optional[OptimizationRecommendation]:
        """
        Analyze if spot instances are appropriate

        Spot instance savings: ~70-90% vs on-demand
        """
        # Only for EC2 instances
        if breakdown.resource_type != "aws_instance":
            return None

        # Not for production
        if environment == "production":
            return None

        # Not for GPU instances (spot availability can be limited)
        if breakdown.is_gpu:
            return None

        # Spot instances typically 70-90% cheaper
        spot_savings_ratio = 0.75  # 75% savings
        potential_savings = breakdown.monthly_cost * spot_savings_ratio

        # Only recommend if savings > $20/month
        if potential_savings < 20:
            return None

        recommendation = OptimizationRecommendation(
            category="spot_instances",
            severity="medium",
            resource_name=breakdown.resource_name,
            resource_type=breakdown.resource_type,
            current_monthly_cost=breakdown.monthly_cost,
            potential_monthly_savings=potential_savings,
            savings_percentage=spot_savings_ratio * 100,
            recommendation=f"🎯 Use Spot Instances for '{breakdown.resource_name}' ({environment} environment)",
            implementation_steps=[
                f"Current Cost (On-Demand): ${breakdown.monthly_cost:.2f}/month",
                f"Spot Instance Cost: ~${breakdown.monthly_cost * 0.25:.2f}/month (75% savings)",
                f"",
                f"⚠️  Spot Instance Considerations:",
                f"- Can be interrupted with 2-minute warning",
                f"- Best for fault-tolerant, flexible workloads",
                f"- Ideal for: development, testing, batch processing, CI/CD",
                f"",
                f"Implementation:",
                f"1. Use EC2 Spot Fleet or Auto Scaling with mixed instances",
                f"2. Configure spot instance request with max price",
                f"3. Implement interruption handling (save state on 2-min warning)",
                f"4. Consider Spot + On-Demand mix for reliability",
                f"",
                f"Monthly savings: ${potential_savings:.2f}",
                f"Annual savings: ${potential_savings * 12:.2f}",
            ]
        )

        return recommendation

    def _analyze_storage_optimization(self, breakdown: CostBreakdown) -> Optional[OptimizationRecommendation]:
        """Analyze storage optimization opportunities"""

        if "ebs" in breakdown.resource_type.lower():
            # Recommend gp3 over gp2 (20% savings)
            savings_ratio = 0.20
            potential_savings = breakdown.monthly_cost * savings_ratio

            if potential_savings < 5:
                return None

            recommendation = OptimizationRecommendation(
                category="storage_optimization",
                severity="low",
                resource_name=breakdown.resource_name,
                resource_type=breakdown.resource_type,
                current_monthly_cost=breakdown.monthly_cost,
                potential_monthly_savings=potential_savings,
                savings_percentage=savings_ratio * 100,
                recommendation=f"💾 Optimize EBS volume type for '{breakdown.resource_name}'",
                implementation_steps=[
                    f"Consider switching from gp2 to gp3:",
                    f"- gp3 is 20% cheaper than gp2",
                    f"- gp3 provides better baseline performance",
                    f"- Can provision IOPS and throughput independently",
                    f"",
                    f"Potential monthly savings: ${potential_savings:.2f}",
                ]
            )

            return recommendation

        return None

    def generate_optimization_report(self) -> str:
        """Generate a formatted optimization report"""
        if not self.recommendations:
            return "\n💡 No optimization recommendations at this time.\n"

        lines = []
        lines.append("")
        lines.append("=" * 80)
        lines.append("💡 FINOPS OPTIMIZATION RECOMMENDATIONS")
        lines.append("=" * 80)
        lines.append("")

        # Calculate total potential savings
        total_savings = sum(rec.potential_monthly_savings for rec in self.recommendations)

        lines.append(f"📊 TOTAL POTENTIAL SAVINGS:")
        lines.append(f"   Monthly:  ${total_savings:,.2f}")
        lines.append(f"   Annual:   ${total_savings * 12:,.2f}")
        lines.append("")

        # Group by category
        categories = {}
        for rec in self.recommendations:
            if rec.category not in categories:
                categories[rec.category] = []
            categories[rec.category].append(rec)

        # Sort recommendations by savings (highest first)
        sorted_recs = sorted(self.recommendations, key=lambda x: x.potential_monthly_savings, reverse=True)

        for i, rec in enumerate(sorted_recs, 1):
            severity_indicator = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢",
            }.get(rec.severity, "⚪")

            lines.append(f"{i}. {severity_indicator} {rec.recommendation}")
            lines.append(f"   Current Cost: ${rec.current_monthly_cost:.2f}/month")
            lines.append(f"   💰 Potential Savings: ${rec.potential_monthly_savings:.2f}/month ({rec.savings_percentage:.0f}%)")
            lines.append(f"   📅 Annual Savings: ${rec.potential_monthly_savings * 12:.2f}/year")
            lines.append("")
            lines.append("   Implementation:")
            for step in rec.implementation_steps:
                lines.append(f"   {step}")
            lines.append("")
            lines.append("-" * 80)
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def get_total_potential_savings(self) -> float:
        """Get total potential monthly savings"""
        return sum(rec.potential_monthly_savings for rec in self.recommendations)

    def get_high_priority_recommendations(self) -> List[OptimizationRecommendation]:
        """Get high severity recommendations"""
        return [rec for rec in self.recommendations if rec.severity == "high"]
