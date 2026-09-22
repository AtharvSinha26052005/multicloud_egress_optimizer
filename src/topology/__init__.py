"""Topology package — all application topologies for evaluation."""
from src.topology.three_tier import create_three_tier_topology
from src.topology.microservice_mesh import create_microservice_mesh_topology
from src.topology.data_pipeline import create_data_pipeline_topology
from src.topology.ml_training import create_ml_training_topology
from src.topology.codecourt import create_codecourt_topology


def get_all_topologies():
    """Return all 5 topologies for benchmarking."""
    return [
        create_three_tier_topology(),
        create_microservice_mesh_topology(),
        create_data_pipeline_topology(),
        create_ml_training_topology(),
        create_codecourt_topology(),
    ]

__all__ = [
    "get_all_topologies",
    "create_three_tier_topology",
    "create_microservice_mesh_topology",
    "create_data_pipeline_topology",
    "create_ml_training_topology",
    "create_codecourt_topology",
]
