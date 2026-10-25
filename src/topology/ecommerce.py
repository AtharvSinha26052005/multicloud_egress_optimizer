"""6th topology: E-Commerce Platform (Review 3)."""
from src.topology.base import Topology, Component


def create_ecommerce_topology() -> Topology:
    """E-Commerce Platform -- 5 components representing an online store."""
    t = Topology(
        name="E-Commerce",
        description="Online store: CDN, storefront, cart, payment, inventory",
    )
    t.add_component(Component("cdn", "frontend", vcpu=1, ram_gb=2,
                              description="CDN / edge cache layer"))
    t.add_component(Component("storefront", "web_tier", vcpu=2, ram_gb=4,
                              description="Next.js product listing"))
    t.add_component(Component("cart_service", "api_gateway", vcpu=2, ram_gb=8,
                              description="Cart management microservice"))
    t.add_component(Component("payment_service", "api_gateway", vcpu=2, ram_gb=8,
                              description="Payment processing"))
    t.add_component(Component("inventory_db", "db_tier", vcpu=4, ram_gb=32,
                              description="PostgreSQL inventory + orders"))
    t.add_traffic("cdn", "storefront", 300)
    t.add_traffic("storefront", "cart_service", 80)
    t.add_traffic("cart_service", "payment_service", 40)
    t.add_traffic("cart_service", "inventory_db", 120)
    t.add_traffic("payment_service", "inventory_db", 60)
    t.add_traffic("cdn", "Internet", 500)
    t.add_traffic("storefront", "Internet", 200)
    return t


ECOMMERCE_LATENCY_SLA = {
    "cdn": 20, "storefront": 80, "cart_service": 150,
    "payment_service": 200, "inventory_db": 15,
}