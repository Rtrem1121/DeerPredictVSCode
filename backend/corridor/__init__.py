"""Movement corridor engine for mature buck habitat modeling."""

from .cost_surface import compute_movement_cost, SEASON_PROFILES
from .pathfinder import dijkstra_path, accumulate_corridors
from .corridor_engine import CorridorEngine, CorridorConfig, CorridorResult
from .stand_reasoning import generate_stand_narrative, enrich_stands_with_corridor_proximity

__all__ = [
    "compute_movement_cost",
    "SEASON_PROFILES",
    "dijkstra_path",
    "accumulate_corridors",
    "CorridorEngine",
    "CorridorConfig",
    "CorridorResult",
    "generate_stand_narrative",
    "enrich_stands_with_corridor_proximity",
]
