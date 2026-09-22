"""5-Component CodeCourt topology — real-world case study."""
from src.topology.base import Topology, Component


def create_codecourt_topology() -> Topology:
    """
    CodeCourt online judge — 5 real components:
    Nginx → API Server → Redis (BullMQ) → Judge Workers → PostgreSQL

    Based on the actual CodeCourt architecture. Traffic estimates are
    derived from typical online judge workloads (hundreds of submissions/day).
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
                              description="PostgreSQL — users, submissions, results"))

    # Communication pattern based on CodeCourt's actual architecture
    t.add_traffic("nginx", "api_server", 50)          # Frontend API calls
    t.add_traffic("api_server", "redis", 30)          # Job enqueue
    t.add_traffic("redis", "judge_workers", 100)      # Job dispatch + code payloads
    t.add_traffic("judge_workers", "postgres", 80)    # Write results back
    t.add_traffic("api_server", "postgres", 60)       # User queries, submission history
    t.add_traffic("judge_workers", "redis", 40)       # Job completion events
    t.add_traffic("nginx", "Internet", 15)            # Static assets, CDN misses

    return t
