"""JSON/YAML architecture file parser for the Cloud Optimizer Tool."""
import json
import os
from src.topology.base import Topology, Component

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

AUTO_TYPE_MAP = {
    "nginx": "frontend", "cdn": "frontend", "web": "web_tier",
    "app": "app_tier", "api": "api_gateway", "gateway": "api_gateway",
    "worker": "worker", "job": "worker", "task": "worker",
    "redis": "cache", "cache": "cache", "memcache": "cache",
    "postgres": "db_tier", "mysql": "db_tier", "mongo": "db_tier", "db": "db_tier",
    "kafka": "message_queue", "rabbitmq": "message_queue", "queue": "message_queue",
    "storage": "storage", "s3": "storage", "blob": "storage",
    "gpu": "gpu_worker", "train": "gpu_worker",
}


def detect_type(name: str) -> str:
    """Auto-detect component type from its name."""
    nl = name.lower()
    for keyword, ctype in AUTO_TYPE_MAP.items():
        if keyword in nl:
            return ctype
    return "app_tier"


def parse_file(path: str) -> Topology:
    """Parse a JSON or YAML architecture file into a Topology object."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if path.endswith(".json"):
        arch = json.loads(content)
    elif YAML_AVAILABLE:
        arch = yaml.safe_load(content)
    else:
        raise ImportError("PyYAML not installed. Run: pip install pyyaml")
    return parse_dict(arch)


def parse_dict(arch: dict, name: str = "User Architecture") -> Topology:
    """Parse an architecture dict into a Topology."""
    topo = Topology(name=name, description="Parsed from user input")
    for comp in arch.get("components", []):
        ctype = comp.get("type", detect_type(comp.get("name", "")))
        topo.add_component(Component(
            name=comp["name"],
            component_type=ctype,
            vcpu=comp.get("vcpu", 2),
            ram_gb=comp.get("ram_gb", 4),
            description=comp.get("description", ""),
        ))
    for t in arch.get("traffic", []):
        topo.add_traffic(t["from"], t["to"], t["gb_per_month"])
    return topo
