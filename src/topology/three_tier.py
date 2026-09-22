"""3-Tier Web Application — the Review 1 baseline topology."""
from src.topology.base import Topology, Component


def create_three_tier_topology() -> Topology:
    """
    Canonical 3-tier web application: Web → App → DB.
    This is the topology from Review 1 with verified baseline numbers.

    Data flow: Users → Web —(500GB)→ App —(200GB)→ DB —(10GB)→ Internet
    """
    t = Topology(
        name="3-Tier Web App",
        description="Frontend + REST API + PostgreSQL database",
    )

    t.add_component(Component("web_tier", "web_tier", vcpu=2, ram_gb=4,
                              description="Frontend / Load Balancer"))
    t.add_component(Component("app_tier", "app_tier", vcpu=4, ram_gb=16,
                              description="Business Logic / REST API"))
    t.add_component(Component("db_tier", "db_tier", vcpu=4, ram_gb=32,
                              description="PostgreSQL Database"))

    t.add_traffic("web_tier", "app_tier", 500)   # User requests forwarded
    t.add_traffic("app_tier", "db_tier", 200)     # DB queries
    t.add_traffic("db_tier", "Internet", 10)      # Backups / analytics export

    return t
