"""
Unified Pricing Model — Single interface to query compute + egress costs
across AWS, GCP, and Azure.

Implements O1: "Build a unified cost model spanning compute, storage and
inter-provider network transfer for at least three public cloud providers
using published pricing data."

The model tries live APIs first, falls back to hardcoded verified prices.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.pricing.fallback_data import get_fallback_prices, PROVIDERS

logger = logging.getLogger(__name__)


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a placement decision."""
    compute: float = 0.0
    egress: float = 0.0
    total: float = 0.0
    compute_details: Dict[str, float] = field(default_factory=dict)  # {component: cost}
    egress_details: Dict[str, float] = field(default_factory=dict)   # {"src->dst": cost}

    def __post_init__(self):
        self.total = self.compute + self.egress


class PricingModel:
    """
    Unified pricing model that provides:
    - get_compute_cost(component_type, provider) → monthly cost in USD
    - get_egress_rate(src_provider, dst_provider) → $/GB
    - get_total_cost(placement, topology) → CostBreakdown

    The model loads data from live APIs when available, falling back to
    hardcoded Aug 2026 prices (which are also the regression test baseline).
    """

    def __init__(self, use_live_apis: bool = False):
        """
        Args:
            use_live_apis: If True, attempt to fetch from live AWS/Azure/GCP APIs
                           before falling back. Default False for reproducibility.
        """
        self.source = "fallback"
        self.providers = PROVIDERS

        # Start with fallback prices (always available)
        fallback = get_fallback_prices()
        self._compute_catalog = fallback["compute"]
        self._egress_rates = fallback["egress"]

        # Attempt live API fetch if requested
        if use_live_apis:
            self._try_live_apis()

        logger.info(f"PricingModel initialized. Source: {self.source}. "
                     f"Providers: {self.providers}. "
                     f"Component types: {len(self._compute_catalog)}")

    def _try_live_apis(self):
        """Attempt to fetch live pricing data. Falls back gracefully on failure."""
        try:
            from src.pricing.aws_pricing import fetch_aws_prices
            aws_data = fetch_aws_prices()
            if aws_data:
                self._merge_live_data("AWS", aws_data)
                self.source = "live+fallback"
                logger.info("AWS live pricing loaded successfully")
        except Exception as e:
            logger.warning(f"AWS pricing fetch failed, using fallback: {e}")

        try:
            from src.pricing.azure_pricing import fetch_azure_prices
            azure_data = fetch_azure_prices()
            if azure_data:
                self._merge_live_data("Azure", azure_data)
                self.source = "live+fallback"
                logger.info("Azure live pricing loaded successfully")
        except Exception as e:
            logger.warning(f"Azure pricing fetch failed, using fallback: {e}")

        try:
            from src.pricing.gcp_pricing import fetch_gcp_prices
            gcp_data = fetch_gcp_prices()
            if gcp_data:
                self._merge_live_data("GCP", gcp_data)
                self.source = "live+fallback"
                logger.info("GCP live pricing loaded successfully")
        except Exception as e:
            logger.warning(f"GCP pricing fetch failed, using fallback: {e}")

    def _merge_live_data(self, provider: str, live_data: dict):
        """Merge live API data into the catalog, overwriting fallback for that provider."""
        for comp_type, provider_data in live_data.get("compute", {}).items():
            if comp_type in self._compute_catalog and provider in provider_data:
                self._compute_catalog[comp_type][provider] = provider_data[provider]

        for key, rate in live_data.get("egress", {}).items():
            if key in self._egress_rates:
                self._egress_rates[key] = rate

    # ─── PUBLIC API ────────────────────────────────────────────

    def get_compute_cost(self, component_type: str, provider: str) -> float:
        """
        Get monthly compute cost for a component type on a specific provider.

        Args:
            component_type: Key from COMPUTE_CATALOG (e.g., "web_tier", "db_tier")
            provider: "AWS", "GCP", or "Azure"

        Returns:
            Monthly cost in USD

        Raises:
            KeyError: If component_type or provider not found
        """
        if component_type not in self._compute_catalog:
            raise KeyError(f"Unknown component type: '{component_type}'. "
                           f"Available: {list(self._compute_catalog.keys())}")
        if provider not in self._compute_catalog[component_type]:
            raise KeyError(f"Unknown provider: '{provider}'. Available: {PROVIDERS}")

        return self._compute_catalog[component_type][provider]["price_monthly"]

    def get_instance_name(self, component_type: str, provider: str) -> str:
        """Get the instance type name (e.g., 't3.medium') for display purposes."""
        return self._compute_catalog[component_type][provider]["instance"]

    def get_egress_rate(self, src_provider: str, dst_provider: str) -> float:
        """
        Get egress rate in $/GB for data transfer from src to dst provider.

        Key property: Same-provider transfer is FREE ($0.00).
        This is the fundamental insight the greedy algorithm ignores.

        Args:
            src_provider: Sending provider ("AWS", "GCP", "Azure")
            dst_provider: Receiving provider, or "Internet"

        Returns:
            Cost per GB in USD
        """
        key = (src_provider, dst_provider)
        if key not in self._egress_rates:
            # If exact pair not found, use the sender's general outbound rate
            for k, v in self._egress_rates.items():
                if k[0] == src_provider and k[1] != src_provider:
                    return v
            raise KeyError(f"No egress rate for {src_provider} → {dst_provider}")
        return self._egress_rates[key]

    def get_total_cost(self, placement: Dict[str, str], topology) -> CostBreakdown:
        """
        Calculate total monthly cost for a given placement.

        This is the core function that both the greedy baseline and our
        TEAP algorithm use to evaluate placement quality.

        Args:
            placement: {component_name: provider} mapping
            topology: Topology object with components and traffic_matrix

        Returns:
            CostBreakdown with compute, egress, total, and detailed breakdowns
        """
        breakdown = CostBreakdown()

        # 1. Compute costs — sum of VM prices for each component on its assigned provider
        for component in topology.components:
            provider = placement[component.name]
            cost = self.get_compute_cost(component.component_type, provider)
            breakdown.compute += cost
            breakdown.compute_details[component.name] = cost

        # 2. Egress costs — for each traffic edge, charge if src and dst are on different providers
        for (src_name, dst_name), traffic_gb in topology.traffic_matrix.items():
            if dst_name == "Internet":
                # Internet-bound traffic always costs egress regardless of provider
                src_provider = placement[src_name]
                rate = self.get_egress_rate(src_provider, "Internet")
                cost = traffic_gb * rate
            else:
                src_provider = placement[src_name]
                dst_provider = placement[dst_name]
                rate = self.get_egress_rate(src_provider, dst_provider)
                cost = traffic_gb * rate

            breakdown.egress += cost
            edge_key = f"{src_name}({src_provider})→{dst_name}({dst_name if dst_name == 'Internet' else placement.get(dst_name, '?')})"
            breakdown.egress_details[edge_key] = cost

        # 3. Total
        breakdown.total = round(breakdown.compute + breakdown.egress, 2)
        breakdown.compute = round(breakdown.compute, 2)
        breakdown.egress = round(breakdown.egress, 2)

        return breakdown

    def get_cheapest_provider(self, component_type: str) -> Tuple[str, float]:
        """Find the cheapest provider for a component type. Used by greedy baseline."""
        best_provider = None
        best_cost = float("inf")
        for provider in self.providers:
            cost = self.get_compute_cost(component_type, provider)
            if cost < best_cost:
                best_cost = cost
                best_provider = provider
        return best_provider, best_cost

    def get_all_compute_prices(self, component_type: str) -> Dict[str, float]:
        """Get compute prices on all providers for a component type."""
        return {
            provider: self.get_compute_cost(component_type, provider)
            for provider in self.providers
        }

    def __repr__(self):
        return (f"PricingModel(source={self.source}, providers={self.providers}, "
                f"component_types={len(self._compute_catalog)})")
