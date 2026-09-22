"""
Fallback Pricing Data — Hardcoded verified prices from August 2026.

WHY: If live APIs (AWS/Azure/GCP) are unreachable during demo or testing,
     we fall back to these verified prices. These are the exact same numbers
     used in Review 1 and serve as the ground truth for regression testing.

SOURCE: AWS EC2 On-Demand Pricing, GCP VM Instance Pricing, Azure VM Pricing
        All retrieved and verified on 25 August 2026, us-east-1 / us-central1 / eastus regions.
"""

# Decision D004: Hardcoded fallback ensures demo never fails on network issues.
# These prices are also the regression test baseline — Review 1 numbers must not change.

# ─────────────────────────────────────────────────────────
# COMPUTE PRICES ($/month, on-demand, Linux)
# Structure: {component_spec: {provider: {"instance": name, "price": monthly_cost}}}
# component_spec is a tuple (vCPU, RAM_GB) for matching
# ─────────────────────────────────────────────────────────

COMPUTE_CATALOG = {
    # Web Tier — 2 vCPU, 4 GB RAM
    "web_tier": {
        "AWS":   {"instance": "t3.medium",       "vcpu": 2, "ram_gb": 4,  "price_monthly": 30.37},
        "GCP":   {"instance": "e2-medium",        "vcpu": 1, "ram_gb": 4,  "price_monthly": 24.27},
        "Azure": {"instance": "Standard_B2s",     "vcpu": 2, "ram_gb": 4,  "price_monthly": 35.04},
    },
    # App Tier — 4 vCPU, 16 GB RAM
    "app_tier": {
        "AWS":   {"instance": "t3.xlarge",        "vcpu": 4, "ram_gb": 16, "price_monthly": 121.47},
        "GCP":   {"instance": "e2-standard-4",    "vcpu": 4, "ram_gb": 16, "price_monthly": 97.83},
        "Azure": {"instance": "Standard_D4s_v3",  "vcpu": 4, "ram_gb": 16, "price_monthly": 110.40},
    },
    # DB Tier — 4 vCPU, 32 GB RAM (memory-optimised)
    "db_tier": {
        "AWS":   {"instance": "r5.xlarge",        "vcpu": 4, "ram_gb": 32, "price_monthly": 183.96},
        "GCP":   {"instance": "n2-highmem-4",     "vcpu": 4, "ram_gb": 32, "price_monthly": 162.40},
        "Azure": {"instance": "Standard_E4s_v3",  "vcpu": 4, "ram_gb": 32, "price_monthly": 157.44},
    },
    # API Gateway — 2 vCPU, 8 GB RAM (for microservice/codecourt topologies)
    "api_gateway": {
        "AWS":   {"instance": "t3.large",         "vcpu": 2, "ram_gb": 8,  "price_monthly": 60.74},
        "GCP":   {"instance": "e2-standard-2",    "vcpu": 2, "ram_gb": 8,  "price_monthly": 48.92},
        "Azure": {"instance": "Standard_D2s_v3",  "vcpu": 2, "ram_gb": 8,  "price_monthly": 55.20},
    },
    # Worker / Compute-Heavy — 4 vCPU, 16 GB RAM (same as app but different role)
    "worker": {
        "AWS":   {"instance": "t3.xlarge",        "vcpu": 4, "ram_gb": 16, "price_monthly": 121.47},
        "GCP":   {"instance": "e2-standard-4",    "vcpu": 4, "ram_gb": 16, "price_monthly": 97.83},
        "Azure": {"instance": "Standard_D4s_v3",  "vcpu": 4, "ram_gb": 16, "price_monthly": 110.40},
    },
    # Cache / Redis — 2 vCPU, 8 GB RAM
    "cache": {
        "AWS":   {"instance": "t3.large",         "vcpu": 2, "ram_gb": 8,  "price_monthly": 60.74},
        "GCP":   {"instance": "e2-standard-2",    "vcpu": 2, "ram_gb": 8,  "price_monthly": 48.92},
        "Azure": {"instance": "Standard_D2s_v3",  "vcpu": 2, "ram_gb": 8,  "price_monthly": 55.20},
    },
    # Frontend / Nginx — 1 vCPU, 2 GB RAM (small)
    "frontend": {
        "AWS":   {"instance": "t3.small",         "vcpu": 2, "ram_gb": 2,  "price_monthly": 15.18},
        "GCP":   {"instance": "e2-small",          "vcpu": 0.5, "ram_gb": 2, "price_monthly": 12.23},
        "Azure": {"instance": "Standard_B1ms",    "vcpu": 1, "ram_gb": 2,  "price_monthly": 14.60},
    },
    # GPU / ML Training — 4 vCPU, 16 GB RAM + GPU equivalent cost
    "gpu_worker": {
        "AWS":   {"instance": "g4dn.xlarge",      "vcpu": 4, "ram_gb": 16, "price_monthly": 379.08},
        "GCP":   {"instance": "n1-standard-4+T4", "vcpu": 4, "ram_gb": 15, "price_monthly": 342.55},
        "Azure": {"instance": "Standard_NC4as_T4_v3", "vcpu": 4, "ram_gb": 28, "price_monthly": 394.20},
    },
    # Storage / Data Lake — 2 vCPU, 8 GB RAM
    "storage": {
        "AWS":   {"instance": "t3.large",         "vcpu": 2, "ram_gb": 8,  "price_monthly": 60.74},
        "GCP":   {"instance": "e2-standard-2",    "vcpu": 2, "ram_gb": 8,  "price_monthly": 48.92},
        "Azure": {"instance": "Standard_D2s_v3",  "vcpu": 2, "ram_gb": 8,  "price_monthly": 55.20},
    },
    # Message Queue — 2 vCPU, 4 GB RAM
    "message_queue": {
        "AWS":   {"instance": "t3.medium",        "vcpu": 2, "ram_gb": 4,  "price_monthly": 30.37},
        "GCP":   {"instance": "e2-medium",         "vcpu": 1, "ram_gb": 4,  "price_monthly": 24.27},
        "Azure": {"instance": "Standard_B2s",     "vcpu": 2, "ram_gb": 4,  "price_monthly": 35.04},
    },
}

# ─────────────────────────────────────────────────────────
# EGRESS RATES ($/GB)
# Key insight exploited by TEAP Phase 3:
#   Azure ($0.087) < AWS ($0.09) < GCP ($0.12)
#   When two clusters MUST be split, put the high-traffic sender
#   on the cheaper-egress provider.
# ─────────────────────────────────────────────────────────

EGRESS_RATES = {
    # (source_provider, destination_provider) → $/GB
    # Same provider = FREE (intra-region)
    ("AWS", "AWS"):     0.00,
    ("AWS", "GCP"):     0.09,
    ("AWS", "Azure"):   0.09,
    ("AWS", "Internet"): 0.09,

    ("GCP", "GCP"):     0.00,
    ("GCP", "AWS"):     0.12,
    ("GCP", "Azure"):   0.12,
    ("GCP", "Internet"): 0.12,

    ("Azure", "Azure"): 0.00,
    ("Azure", "AWS"):   0.087,
    ("Azure", "GCP"):   0.087,
    ("Azure", "Internet"): 0.087,
}

PROVIDERS = ["AWS", "GCP", "Azure"]


def get_fallback_prices():
    """
    Returns the complete fallback pricing dataset.

    Returns:
        dict with keys:
            - "compute": COMPUTE_CATALOG
            - "egress": EGRESS_RATES
            - "providers": PROVIDERS
            - "source": description string
    """
    return {
        "compute": COMPUTE_CATALOG,
        "egress": EGRESS_RATES,
        "providers": PROVIDERS,
        "source": "Hardcoded fallback — verified Aug 2026 public pricing (Review 1 baseline)",
    }
