"""
ILP Solver — Integer Linear Programming exact solver using PuLP/CBC.

Strategy: Model placement as a binary optimisation problem.
           Variables x[i,j] = 1 if component i is on provider j.
           Minimise compute cost + egress cost.
           Egress term is linearised from quadratic using auxiliary variables.

This is the "exact" approach — guaranteed optimal but slow for large N.

Time complexity: Worst case exponential, but typically fast for N ≤ 15
"""

from typing import Dict
import pulp
from src.algorithms.base import PlacementSolver
from src.pricing.unified_model import PricingModel


class ILPSolver(PlacementSolver):
    """
    Exact ILP solver using PuLP with CBC backend.

    The objective function minimises:
        Total = Σ compute_cost[i,j] × x[i,j]
              + Σ traffic[i,k] × egress_rate[j] × y[i,k,j,l]   for j≠l

    where y[i,k,j,l] linearises the product x[i,j] × x[k,l] using
    McCormick envelope constraints.
    """

    name = "ILP"

    def _solve_impl(self, topology, pricing: PricingModel) -> Dict[str, str]:
        components = topology.components
        providers = pricing.providers
        comp_names = [c.name for c in components]

        # ─── Create the ILP problem ───
        prob = pulp.LpProblem("MultiCloudPlacement", pulp.LpMinimize)

        # ─── Decision variables: x[i,j] = 1 if component i is on provider j ───
        x = {}
        for comp in components:
            for prov in providers:
                x[comp.name, prov] = pulp.LpVariable(
                    f"x_{comp.name}_{prov}", cat="Binary"
                )

        # ─── Constraint: each component assigned to exactly one provider ───
        for comp in components:
            prob += (
                pulp.lpSum(x[comp.name, prov] for prov in providers) == 1,
                f"assign_{comp.name}"
            )

        # ─── Compute cost terms ───
        compute_cost = pulp.lpSum(
            pricing.get_compute_cost(comp.component_type, prov) * x[comp.name, prov]
            for comp in components
            for prov in providers
        )

        # ─── Egress cost terms (linearised) ───
        # For each traffic edge (src, dst) with traffic volume T:
        # If src is on provider j and dst is on provider l where j ≠ l:
        #   egress = T × egress_rate(j)
        #
        # We introduce auxiliary binary variable y[src,dst,j,l] to represent
        # the product x[src,j] × x[dst,l] and add McCormick constraints.
        egress_cost_terms = []
        y = {}

        for (src_name, dst_name), traffic_gb in topology.traffic_matrix.items():
            if dst_name == "Internet":
                # Internet egress: just sum over providers for the src component
                for prov in providers:
                    rate = pricing.get_egress_rate(prov, "Internet")
                    egress_cost_terms.append(traffic_gb * rate * x[src_name, prov])
            elif dst_name in comp_names:
                # Inter-component egress: need to know both src and dst providers
                for j in providers:
                    for l in providers:
                        if j == l:
                            continue  # Same provider = free, skip

                        rate = pricing.get_egress_rate(j, l)
                        if rate == 0:
                            continue

                        # Auxiliary variable y[src,dst,j,l] = x[src,j] × x[dst,l]
                        var_name = f"y_{src_name}_{dst_name}_{j}_{l}"
                        y_var = pulp.LpVariable(var_name, 0, 1, cat="Binary")
                        y[src_name, dst_name, j, l] = y_var

                        # McCormick linearisation constraints:
                        # y ≤ x[src,j]
                        prob += y_var <= x[src_name, j], f"mc1_{var_name}"
                        # y ≤ x[dst,l]
                        prob += y_var <= x[dst_name, l], f"mc2_{var_name}"
                        # y ≥ x[src,j] + x[dst,l] - 1
                        prob += y_var >= x[src_name, j] + x[dst_name, l] - 1, f"mc3_{var_name}"

                        # Add egress cost term
                        egress_cost_terms.append(traffic_gb * rate * y_var)

        egress_cost = pulp.lpSum(egress_cost_terms) if egress_cost_terms else 0

        # ─── Objective: minimise total cost ───
        prob += compute_cost + egress_cost, "TotalCost"

        # ─── Solve ───
        prob.solve(pulp.PULP_CBC_CMD(msg=0))  # msg=0 suppresses CBC output

        # ─── Extract solution ───
        if prob.status != pulp.constants.LpStatusOptimal:
            # Fallback to greedy if ILP fails (shouldn't happen for feasible problems)
            from src.algorithms.greedy import GreedySolver
            return GreedySolver()._solve_impl(topology, pricing)

        placement = {}
        for comp in components:
            for prov in providers:
                if pulp.value(x[comp.name, prov]) > 0.5:
                    placement[comp.name] = prov
                    break

        return placement
