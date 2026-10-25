"""5-Component CodeCourt topology -- real-world case study."""
from src.topology.base import Topology, Component


def create_codecourt_topology() -> Topology:
    """
    CodeCourt online judge -- 5 real components.
    R3 Audit: Added api_server->Internet 25 GB. Total traffic: 400 GB/mo.
    """
    t = Topology(
        name="CodeCourt",
        description="Online judge: frontend, API, queue, workers, database",
    )
    t.add_component(Component("nginx", "frontend", vcpu=1, ram_gb=2,
                              description="Nginx serving React frontend"))
    t.add_component(Component("api_server", "api_gateway", vcpu=2, ram_gb=8,
                              description="Express.js REST API"))
    t.add_component(Component("redis", "cache", vcpu=2, ram_gb=8,
                              description="Redis + BullMQ job queue"))
    t.add_component(Component("judge_workers", "worker", vcpu=4, ram_gb=16,
                              description="Docker-based code execution workers"))
    t.add_component(Component("postgres", "db_tier", vcpu=4, ram_gb=32,
                              description="PostgreSQL -- users, submissions, results"))
    t.add_traffic("nginx", "api_server", 50)
    t.add_traffic("api_server", "redis", 30)
    t.add_traffic("redis", "judge_workers", 100)
    t.add_traffic("judge_workers", "postgres", 80)
    t.add_traffic("api_server", "postgres", 60)
    t.add_traffic("judge_workers", "redis", 40)
    t.add_traffic("nginx", "Internet", 15)
    t.add_traffic("api_server", "Internet", 25)
    return t


CODECOURT_LATENCY_SLA = {
    "nginx": 50, "api_server": 100, "redis": 5,
    "judge_workers": 500, "postgres": 10,
}
