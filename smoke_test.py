
import sys; sys.path.insert(0,".")
from src.pricing.unified_model import PricingModel
from src.topology.base import Topology, Component
from src.algorithms.greedy import GreedySolver
from src.algorithms.teap import TEAPSolver
from src.algorithms.ilp_solver import ILPSolver

pricing = PricingModel()
topo = Topology(name="Test", description="Smoke test")
topo.add_component(Component("web_server","web_tier",2,4))
topo.add_component(Component("app_server","app_tier",4,16))
topo.add_component(Component("database","db_tier",4,32))
topo.add_traffic("web_server","app_server",100)
topo.add_traffic("app_server","database",200)
topo.add_traffic("web_server","Internet",50)

g = GreedySolver().solve(topo, pricing)
t = TEAPSolver().solve(topo, pricing)
ilp = ILPSolver().solve(topo, pricing)

savings = g.cost.total - t.cost.total
savings_pct = savings / g.cost.total * 100
print("Greedy: $" + str(round(g.cost.total,2)) + " | TEAP: $" + str(round(t.cost.total,2)) + " | ILP: $" + str(round(ilp.cost.total,2)))
print("Savings: $" + str(round(savings,2)) + " (" + str(round(savings_pct,1)) + "%)")
print("TEAP placement:", t.placement)
print("egress_details:", dict(t.cost.egress_details))
components_to_move = sum(1 for k in t.placement if t.placement[k] != g.placement.get(k))
print("Components to move:", components_to_move)
print("SMOKE TEST PASSED")

