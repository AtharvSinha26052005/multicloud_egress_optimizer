"""
Pricing Validation -- Compares live API prices vs fallback hardcoded values.

Implements O1 evidence: proves we query real public pricing APIs.
Output saved to results/tables/pricing_api_comparison.csv.
"""

import csv
import os
import json
import logging
from datetime import datetime
from typing import Dict

from src.pricing.fallback_data import COMPUTE_CATALOG, EGRESS_RATES, PROVIDERS

logger = logging.getLogger(__name__)

API_DOCS = {
    "AWS": "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json",
    "Azure": "https://prices.azure.com/api/retail/prices",
    "GCP": "https://cloudbilling.googleapis.com/v1/services",
}


def _try_aws_live() -> Dict[str, float]:
    """Attempt to fetch a few EC2 prices from AWS Bulk Pricing API."""
    results = {}
    try:
        import urllib.request, json as _json
        url = ("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/"
               "AmazonEC2/current/us-east-1/index.json")
        req = urllib.request.Request(url, headers={"User-Agent": "P5-EgressOptimizer/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read(10_000_000))
            products = data.get("products", {})
            prices_map = data.get("terms", {}).get("OnDemand", {})

            for sku, prod in list(products.items())[:5000]:
                attrs = prod.get("attributes", {})
                itype = attrs.get("instanceType", "")
                if itype not in ["t3.medium", "t3.large", "t3.xlarge", "r5.xlarge", "t3.small"]:
                    continue
                if attrs.get("operatingSystem") != "Linux":
                    continue
                if attrs.get("tenancy") != "Shared":
                    continue
                od = prices_map.get(sku, {})
                for offer in od.values():
                    for pd in offer.get("priceDimensions", {}).values():
                        uom = pd.get("unit", "")
                        if "Hrs" in uom or "Hour" in uom:
                            pph = float(pd.get("pricePerUnit", {}).get("USD", 0))
                            results[itype] = round(pph * 24 * 30, 2)
    except Exception as e:
        logger.warning(f"AWS live fetch failed: {e}")
    return results


def _try_azure_live() -> Dict[str, float]:
    """Attempt to fetch Azure VM prices from Retail Prices API."""
    results = {}
    try:
        import urllib.request, urllib.parse, json as _json
        filter_q = "serviceName eq 'Virtual Machines' and armRegionName eq 'eastus' and priceType eq 'Consumption'"
        url = f"https://prices.azure.com/api/retail/prices?$filter={urllib.parse.quote(filter_q)}&$top=100"
        req = urllib.request.Request(url, headers={"User-Agent": "P5-EgressOptimizer/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read(1_000_000))
            for item in data.get("Items", []):
                name = item.get("skuName", "")
                pph = item.get("retailPrice", 0)
                if pph > 0 and name:
                    results[name] = round(pph * 24 * 30, 2)
    except Exception as e:
        logger.warning(f"Azure live fetch failed: {e}")
    return results


def run_validation() -> Dict:
    """
    Run pricing validation: compare live vs fallback prices.
    Returns a summary dict and saves CSV to results/tables/.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    print(f"\n[Pricing Validation] {timestamp}")
    print(f"  Fallback data: Aug 2026 verified prices (Review 1 baseline)")
    print(f"  Attempting live API queries...")

    aws_live = _try_aws_live()
    azure_live = _try_azure_live()

    aws_ok = len(aws_live) > 0
    azure_ok = len(azure_live) > 0
    print(f"  AWS API:   {"OK (" + str(len(aws_live)) + " prices)" if aws_ok else "FAILED -- using fallback"}")
    print(f"  Azure API: {"OK (" + str(len(azure_live)) + " prices)" if azure_ok else "FAILED -- using fallback"}")
    print(f"  GCP API:   Skipped (requires OAuth -- using fallback)")

    rows = []
    for comp_type, providers in COMPUTE_CATALOG.items():
        for prov, info in providers.items():
            fallback_price = info["price_monthly"]
            instance = info["instance"]

            # Try to find live price
            live_price = None
            if prov == "AWS" and aws_live:
                live_price = aws_live.get(instance)
            elif prov == "Azure" and azure_live:
                live_price = azure_live.get(instance)

            delta_pct = None
            if live_price is not None and fallback_price > 0:
                delta_pct = round((live_price - fallback_price) / fallback_price * 100, 2)

            rows.append({
                "component_type": comp_type,
                "provider": prov,
                "instance": instance,
                "fallback_price_monthly": fallback_price,
                "live_price_monthly": live_price,
                "delta_pct": delta_pct,
                "status": "live" if live_price else "fallback",
            })

    # Save CSV
    os.makedirs("results/tables", exist_ok=True)
    csv_path = "results/tables/pricing_api_comparison.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved: {csv_path}")

    # Print summary table
    print(f"\n  {"Component":>20} {"Provider":>8} {"Fallback":>10} {"Live":>10} {"Delta":>8}")
    print(f"  {"-"*60}")
    for row in rows[:15]:  # Show first 15
        live = f"${row["live_price_monthly"]:.2f}" if row["live_price_monthly"] else "N/A"
        delta = f"{row["delta_pct"]:+.1f}%" if row["delta_pct"] is not None else "N/A"
        print(f"  {row["component_type"]:>20} {row["provider"]:>8} ${row["fallback_price_monthly"]:>8.2f} {live:>10} {delta:>8}")

    summary = {
        "timestamp": timestamp,
        "aws_live": aws_ok,
        "azure_live": azure_ok,
        "gcp_live": False,
        "total_entries": len(rows),
        "live_entries": sum(1 for r in rows if r["status"] == "live"),
        "fallback_entries": sum(1 for r in rows if r["status"] == "fallback"),
        "csv_path": csv_path,
    }
    return summary


if __name__ == "__main__":
    result = run_validation()
    print(f"\n  Summary: {result}")