"""Docker Compose parser for the Cloud Optimizer Tool."""
from src.topology.base import Topology, Component
from src.tool.parsers.json_parser import detect_type

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

IMAGE_TYPE_MAP = {
    "nginx": "frontend", "apache": "frontend", "haproxy": "frontend",
    "node": "app_tier", "python": "app_tier", "java": "app_tier", "go": "app_tier",
    "redis": "cache", "memcached": "cache",
    "postgres": "db_tier", "mysql": "db_tier", "mongodb": "db_tier",
    "rabbitmq": "message_queue", "kafka": "message_queue",
    "elasticsearch": "storage", "minio": "storage",
}


def image_to_type(image: str) -> str:
    """Map a Docker image name to a component type."""
    base = image.split(":")[0].split("/")[-1].lower()
    for k, v in IMAGE_TYPE_MAP.items():
        if k in base:
            return v
    return detect_type(base)


def parse_compose(content: str, default_traffic_gb: int = 50) -> Topology:
    """Parse a docker-compose YAML string into a Topology object."""
    if not YAML_AVAILABLE:
        raise ImportError("PyYAML not installed. Run: pip install pyyaml")
    dc = yaml.safe_load(content)
    services = dc.get("services", {})
    topo = Topology(
        name="Docker Architecture",
        description="Parsed from docker-compose.yml",
    )
    for svc_name, svc_cfg in services.items():
        image = svc_cfg.get("image", svc_name)
        ctype = image_to_type(image)
        topo.add_component(Component(
            name=svc_name,
            component_type=ctype,
            vcpu=2,
            ram_gb=4,
            description="Image: " + image,
        ))
    # Auto-connect based on depends_on
    for svc_name, svc_cfg in services.items():
        deps = svc_cfg.get("depends_on", [])
        if isinstance(deps, dict):
            deps = list(deps.keys())
        for dep in deps:
            if dep in services:
                topo.add_traffic(svc_name, dep, default_traffic_gb)
    # Internet egress from first service
    if services:
        first = list(services.keys())[0]
        topo.add_traffic(first, "Internet", 30)
    return topo
