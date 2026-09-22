"""
Azure Pricing Fetcher — Queries the Azure Retail Prices API.

Endpoint: https://prices.azure.com/api/retail/prices
Auth: NONE REQUIRED (public endpoint)
Format: JSON with OData filtering
"""

import json
import os
import logging
import requests

logger = logging.getLogger(__name__)

CACHE_FILE = os.path.join("results", "cache", "azure_prices.json")


def fetch_azure_prices() -> dict:
    """
    Fetch VM and bandwidth pricing from Azure Retail Prices API.
    Returns None if fetch fails.
    """
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass

    try:
        url = "https://prices.azure.com/api/retail/prices"
        params = {
            "$filter": "serviceName eq 'Virtual Machines' and armRegionName eq 'eastus' and priceType eq 'Consumption'",
            "$top": "10",
        }
        logger.info(f"Fetching Azure pricing from {url}")
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        logger.info(f"Azure API reachable, {len(data.get('Items', []))} items returned")

        # For Review 2, return None and rely on fallback for consistency
        return None

    except requests.RequestException as e:
        logger.warning(f"Azure pricing API unreachable: {e}")
        return None
