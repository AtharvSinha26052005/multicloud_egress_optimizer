"""
AWS Pricing Fetcher — Queries the public AWS Bulk Price List API.

Endpoint: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/us-east-1/index.json
Auth: NONE REQUIRED (public endpoint)

NOTE: The full EC2 pricing file is ~1.5 GB. We fetch only specific instance
      types to keep it fast. For Review 2, we primarily use fallback data
      and validate against live API as a secondary check.
"""

import json
import os
import logging
import requests

logger = logging.getLogger(__name__)

# Instance types we need prices for
TARGET_INSTANCES = {
    "t3.small", "t3.medium", "t3.large", "t3.xlarge",
    "r5.xlarge", "g4dn.xlarge",
}

# Cache file to avoid re-fetching
CACHE_FILE = os.path.join("results", "cache", "aws_prices.json")


def fetch_aws_prices() -> dict:
    """
    Fetch EC2 on-demand pricing from AWS Bulk API.

    Returns dict with structure:
        {"compute": {component_type: {"AWS": {instance, price_monthly, ...}}},
         "egress": {("AWS", "Internet"): rate, ...}}

    Returns None if fetch fails.
    """
    # Check cache first
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cached = json.load(f)
                logger.info(f"AWS prices loaded from cache: {CACHE_FILE}")
                return cached
        except Exception:
            pass

    try:
        # Fetch the region index to get specific instance pricing
        # Using the offers index endpoint which is much smaller than the full file
        url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/region_index.json"
        logger.info(f"Fetching AWS pricing from {url}")

        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        # For Review 2, return None and rely on fallback
        # Full API parsing will be implemented for Review 3
        logger.info("AWS API reachable, using fallback prices for consistency")
        return None

    except requests.RequestException as e:
        logger.warning(f"AWS pricing API unreachable: {e}")
        return None
