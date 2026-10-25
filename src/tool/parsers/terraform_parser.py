"""Terraform HCL parser (MVP) for the Cloud Optimizer Tool."""
import re
from typing import List, Dict

INSTANCE_TYPE_MAP = {
    "t3.micro":        {"vcpu": 2, "ram_gb": 1,  "type": "frontend"},
    "t3.small":        {"vcpu": 2, "ram_gb": 2,  "type": "frontend"},
    "t3.medium":       {"vcpu": 2, "ram_gb": 4,  "type": "web_tier"},
    "t3.large":        {"vcpu": 2, "ram_gb": 8,  "type": "api_gateway"},
    "t3.xlarge":       {"vcpu": 4, "ram_gb": 16, "type": "app_tier"},
    "t3.2xlarge":      {"vcpu": 8, "ram_gb": 32, "type": "app_tier"},
    "r5.large":        {"vcpu": 2, "ram_gb": 16, "type": "db_tier"},
    "r5.xlarge":       {"vcpu": 4, "ram_gb": 32, "type": "db_tier"},
    "r5.2xlarge":      {"vcpu": 8, "ram_gb": 64, "type": "db_tier"},
    "db.t3.medium":    {"vcpu": 2, "ram_gb": 4,  "type": "db_tier"},
    "db.r5.xlarge":    {"vcpu": 4, "ram_gb": 32, "type": "db_tier"},
    "g4dn.xlarge":     {"vcpu": 4, "ram_gb": 16, "type": "gpu_worker"},
    "n1-standard-2":   {"vcpu": 2, "ram_gb": 7,  "type": "web_tier"},
    "n1-standard-4":   {"vcpu": 4, "ram_gb": 15, "type": "app_tier"},
    "e2-medium":       {"vcpu": 1, "ram_gb": 4,  "type": "web_tier"},
    "Standard_D2s_v3": {"vcpu": 2, "ram_gb": 8,  "type": "api_gateway"},
    "Standard_D4s_v3": {"vcpu": 4, "ram_gb": 16, "type": "app_tier"},
    "Standard_E4s_v3": {"vcpu": 4, "ram_gb": 32, "type": "db_tier"},
}

_BLOCK_RE = re.compile(
    r'resource\s+"([\w_]+)"\s+"(\w+)"\s+\{([^}]+)\}',
    re.DOTALL,
)
_ATTR_NAMES = ["instance_type", "instance_class", "machine_type", "vm_size", "size"]


def parse_terraform(content: str) -> List[Dict]:
    """
    Parse Terraform HCL and extract compute resources.
    Returns list of dicts with name, instance_type, vcpu, ram_gb, component_type.

    NOTE: Traffic volumes are NOT in Terraform files.
    After parsing, users must supply traffic via the JSON/YAML format or Manual Builder.
    """
    resources = []
    for match in _BLOCK_RE.finditer(content):
        res_name = match.group(2)
        body = match.group(3)
        # Find instance type
        itype = None
        for attr in _ATTR_NAMES:
            pat = attr + r'\s*=\s*"([^"]+)"'
            m = re.search(pat, body)
            if m:
                itype = m.group(1)
                break
        # Find role from tags if present
        role_m = re.search(r'Role\s*=\s*"([^"]+)"', body)
        role = role_m.group(1) if role_m else None
        info = INSTANCE_TYPE_MAP.get(itype or "", {"vcpu": 2, "ram_gb": 4, "type": "app_tier"})
        resources.append({
            "name": res_name,
            "instance_type": itype or "unknown",
            "vcpu": info["vcpu"],
            "ram_gb": info["ram_gb"],
            "component_type": role or info["type"],
        })
    return resources
