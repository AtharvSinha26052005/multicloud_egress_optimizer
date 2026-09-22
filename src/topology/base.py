"""
Base classes for application topologies.

A Topology defines:
- A set of Components (with resource requirements and a type for pricing lookup)
- A traffic matrix (which component sends how much data to which other component)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import networkx as nx


@dataclass
class Component:
    """One deployable unit of an application."""
    name: str                  # Unique identifier, e.g., "web_tier"
    component_type: str        # Key into COMPUTE_CATALOG, e.g., "web_tier"
    vcpu: int                  # vCPU requirement
    ram_gb: int                # RAM in GB
    description: str = ""      # Human-readable role description


class Topology:
    """
    Application topology — components + traffic matrix.

    The traffic matrix is a dict mapping (source_name, destination_name) → GB/month.
    Destination can be another component name or "Internet" for outbound traffic.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.components: List[Component] = []
        self.traffic_matrix: Dict[Tuple[str, str], float] = {}

    def add_component(self, component: Component):
        """Add a component to the topology."""
        self.components.append(component)

    def add_traffic(self, src: str, dst: str, gb_per_month: float):
        """
        Add a traffic edge between two components.

        Args:
            src: Source component name
            dst: Destination component name, or "Internet"
            gb_per_month: Data transfer volume in GB per month
        """
        self.traffic_matrix[(src, dst)] = gb_per_month

    def scale_traffic(self, multiplier: float) -> "Topology":
        """
        Create a copy of this topology with all traffic volumes scaled.
        Used for parameter sweep experiments.

        Args:
            multiplier: Factor to multiply all traffic volumes by

        Returns:
            New Topology with scaled traffic
        """
        scaled = Topology(
            name=f"{self.name} (traffic×{multiplier})",
            description=self.description,
        )
        scaled.components = self.components.copy()
        scaled.traffic_matrix = {
            edge: vol * multiplier
            for edge, vol in self.traffic_matrix.items()
        }
        return scaled

    def set_traffic_volume(self, base_volume: float) -> "Topology":
        """
        Create a copy with all non-internet traffic edges set to base_volume.
        Internet traffic stays at original. Used for controlled experiments.
        """
        scaled = Topology(name=f"{self.name} ({base_volume}GB)", description=self.description)
        scaled.components = self.components.copy()
        for (src, dst), vol in self.traffic_matrix.items():
            if dst == "Internet":
                scaled.traffic_matrix[(src, dst)] = vol
            else:
                scaled.traffic_matrix[(src, dst)] = base_volume
        return scaled

    def to_graph(self) -> nx.DiGraph:
        """
        Convert topology to a NetworkX directed graph.
        Used by TEAP Phase 1 for community detection.

        Node attributes: component data
        Edge attributes: traffic_gb (weight)
        """
        G = nx.DiGraph()
        for comp in self.components:
            G.add_node(comp.name, component=comp)

        for (src, dst), traffic_gb in self.traffic_matrix.items():
            if dst != "Internet":  # Internet is not a placeable component
                G.add_edge(src, dst, weight=traffic_gb, traffic_gb=traffic_gb)

        return G

    def get_component(self, name: str) -> Component:
        """Get a component by name."""
        for comp in self.components:
            if comp.name == name:
                return comp
        raise KeyError(f"Component '{name}' not found in topology '{self.name}'")

    @property
    def num_components(self) -> int:
        return len(self.components)

    @property
    def component_names(self) -> List[str]:
        return [c.name for c in self.components]

    def __repr__(self):
        edges = len(self.traffic_matrix)
        total_traffic = sum(self.traffic_matrix.values())
        return (f"Topology('{self.name}', components={self.num_components}, "
                f"edges={edges}, total_traffic={total_traffic:.0f} GB/mo)")
