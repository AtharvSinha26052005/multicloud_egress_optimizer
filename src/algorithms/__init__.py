"""
Algorithm Solvers Package — All placement algorithms.

Implements O2: "Formulate multi-component workload placement as an
optimisation problem in which egress cost between communicating components
is represented explicitly."
"""
from src.algorithms.base import PlacementSolver, PlacementResult
from src.algorithms.greedy import GreedySolver
from src.algorithms.single_provider import SingleProviderSolver
from src.algorithms.exhaustive import ExhaustiveSolver
from src.algorithms.ilp_solver import ILPSolver
from src.algorithms.simulated_annealing import SASolver
from src.algorithms.teap import TEAPSolver

ALL_SOLVERS = [
    GreedySolver,
    SingleProviderSolver,
    ExhaustiveSolver,
    ILPSolver,
    SASolver,
    TEAPSolver,
]

__all__ = [
    "PlacementSolver", "PlacementResult",
    "GreedySolver", "SingleProviderSolver", "ExhaustiveSolver",
    "ILPSolver", "SASolver", "TEAPSolver",
    "ALL_SOLVERS",
]
