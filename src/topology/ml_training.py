"""3-Component ML Training Pipeline topology."""
from src.topology.base import Topology, Component


def create_ml_training_topology() -> Topology:
    """
    3-component ML workflow: Data Loader → GPU Trainer → Model Registry.
    Heavy data flow from loader to trainer (large datasets).
    """
    t = Topology(
        name="ML Training",
        description="Data loading, GPU training, model storage",
    )

    t.add_component(Component("data_loader", "storage", vcpu=2, ram_gb=8,
                              description="Dataset loading and preprocessing"))
    t.add_component(Component("trainer", "gpu_worker", vcpu=4, ram_gb=16,
                              description="GPU training server"))
    t.add_component(Component("model_registry", "cache", vcpu=2, ram_gb=8,
                              description="Model checkpoint storage"))

    t.add_traffic("data_loader", "trainer", 500)      # Training data batches
    t.add_traffic("trainer", "model_registry", 50)    # Model checkpoints
    t.add_traffic("model_registry", "Internet", 5)    # Model serving / download

    return t
