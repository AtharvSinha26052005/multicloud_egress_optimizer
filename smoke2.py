
import sys; sys.path.insert(0,".")
from src.algorithms.greedy import GreedySolver
from src.algorithms.teap import TEAPSolver
from src.algorithms.ilp_solver import ILPSolver
from src.tool.parsers.docker_parser import parse_compose
from src.pricing.unified_model import PricingModel
from src.topology.base import Topology, Component
import yaml, json

pricing = PricingModel()

# Test 1: YAML parse
test_yaml = """
components:
  - name: api
    type: app_tier
    vcpu: 4
    ram_gb: 8
  - name: db
    type: db_tier
    vcpu: 4
    ram_gb: 32
traffic:
  - from: api
    to: db
    gb_per_month: 200
  - from: api
    to: Internet
    gb_per_month: 50
"""
arch = yaml.safe_load(test_yaml)
topo = Topology(name="test")
for c in arch["components"]:
    topo.add_component(Component(name=c["name"],component_type=c["type"],vcpu=c["vcpu"],ram_gb=c["ram_gb"]))
for t in arch["traffic"]:
    topo.add_traffic(t["from"],t["to"],t["gb_per_month"])
g = GreedySolver().solve(topo,pricing)
t = TEAPSolver().solve(topo,pricing)
print("YAML test OK: Greedy=" + str(round(g.cost.total,2)) + " TEAP=" + str(round(t.cost.total,2)))

# Test 2: Docker compose
test_compose = """version: "3.9"
services:
  nginx:
    image: nginx
    depends_on: [api]
  api:
    image: python:3.11
    depends_on: [postgres]
  postgres:
    image: postgres:16
  redis:
    image: redis:7
"""
topo2 = parse_compose(test_compose)
g2 = GreedySolver().solve(topo2,pricing)
t2 = TEAPSolver().solve(topo2,pricing)
print("Docker test OK: " + str(len(topo2.components)) + " services, Greedy=" + str(round(g2.cost.total,2)) + " TEAP=" + str(round(t2.cost.total,2)))

print("ALL SMOKE TESTS PASSED")

