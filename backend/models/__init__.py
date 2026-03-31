"""
Domain Models for Deer Prediction System

Provides clean separation of concerns for terrain, bedding sites, and stand positions.
Supports Vermont whitetail deer ecology with biological validation.
"""

from .terrain import TerrainMetrics, TerrainGrid, AspectCalculator
from .bedding_site import BeddingZone, BeddingZoneCandidate, BeddingScoreBreakdown
from .stand_site import StandPosition, StandType, ScentManagementResult
from .buck_event import BuckEvent, BuckClass, EventSource, MovementType
from .evidence_weights import (
    compute_evidence_weight,
    recency_weight,
    source_quality_for_observation,
    maturity_multiplier,
    pattern_bonus,
)
from .evidence_cluster import EvidenceCluster, build_clusters

__all__ = [
    'TerrainMetrics',
    'TerrainGrid',
    'AspectCalculator',
    'BeddingZone',
    'BeddingZoneCandidate',
    'BeddingScoreBreakdown',
    'StandPosition',
    'StandType',
    'ScentManagementResult',
    'BuckEvent',
    'BuckClass',
    'EventSource',
    'MovementType',
    'compute_evidence_weight',
    'recency_weight',
    'source_quality_for_observation',
    'maturity_multiplier',
    'pattern_bonus',
    'EvidenceCluster',
    'build_clusters',
]
