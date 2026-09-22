"""5-Service Microservice Mesh topology."""
from src.topology.base import Topology, Component


def create_microservice_mesh_topology() -> Topology:
    """
    5-service mesh: API Gateway, Auth, Order, Payment, Notification.
    Each service communicates with 2-3 others, creating a dense graph
    that stresses the placement algorithm more than a linear topology.
    """
    t = Topology(
        name="Microservice Mesh",
        description="5-service e-commerce backend with mesh communication",
    )

    t.add_component(Component("api_gw", "api_gateway", vcpu=2, ram_gb=8,
                              description="API Gateway / Load Balancer"))
    t.add_component(Component("auth_svc", "cache", vcpu=2, ram_gb=8,
                              description="Authentication Service"))
    t.add_component(Component("order_svc", "worker", vcpu=4, ram_gb=16,
                              description="Order Processing Service"))
    t.add_component(Component("payment_svc", "worker", vcpu=4, ram_gb=16,
                              description="Payment Processing Service"))
    t.add_component(Component("notif_svc", "message_queue", vcpu=2, ram_gb=4,
                              description="Notification Service"))

    # Mesh communication pattern
    t.add_traffic("api_gw", "auth_svc", 300)        # Every request hits auth
    t.add_traffic("api_gw", "order_svc", 250)        # Order requests
    t.add_traffic("order_svc", "payment_svc", 200)   # Orders trigger payments
    t.add_traffic("order_svc", "notif_svc", 150)     # Order confirmations
    t.add_traffic("payment_svc", "notif_svc", 100)   # Payment receipts
    t.add_traffic("auth_svc", "order_svc", 50)       # Auth tokens forwarded
    t.add_traffic("notif_svc", "Internet", 20)       # Email/SMS outbound

    return t
