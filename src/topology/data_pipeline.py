"""4-Stage ETL Data Pipeline topology."""
from src.topology.base import Topology, Component


def create_data_pipeline_topology() -> Topology:
    """
    4-stage data pipeline: Ingestion → Transform → Analytics → Storage.
    Linear flow with heavy data transfer between stages.
    """
    t = Topology(
        name="Data Pipeline",
        description="4-stage ETL: ingest, transform, analyze, store",
    )

    t.add_component(Component("ingestion", "worker", vcpu=4, ram_gb=16,
                              description="Data ingestion from external sources"))
    t.add_component(Component("transform", "worker", vcpu=4, ram_gb=16,
                              description="Data cleaning and transformation"))
    t.add_component(Component("analytics", "worker", vcpu=4, ram_gb=16,
                              description="Analytics and aggregation engine"))
    t.add_component(Component("storage", "storage", vcpu=2, ram_gb=8,
                              description="Data lake / warehouse storage"))

    # Linear flow — heavy data between stages
    t.add_traffic("ingestion", "transform", 400)     # Raw data
    t.add_traffic("transform", "analytics", 300)     # Cleaned data
    t.add_traffic("analytics", "storage", 150)       # Aggregated results
    t.add_traffic("storage", "Internet", 30)         # Dashboard queries, exports

    return t
