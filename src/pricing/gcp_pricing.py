"""
GCP Pricing Fetcher — Uses cached Infracost data or GCP Cloud Billing API.

The GCP Cloud Billing Catalog API requires an API key (free tier).
For Review 2, we use fallback data for consistency.
"""

import logging

logger = logging.getLogger(__name__)


def fetch_gcp_prices() -> dict:
    """
    Fetch GCP pricing. For Review 2, returns None (uses fallback).
    Full implementation with Cloud Billing API for Review 3.
    """
    logger.info("GCP pricing: using fallback data for Review 2")
    return None
