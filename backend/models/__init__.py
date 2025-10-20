"""
Domain Models for Deer Prediction System

Provides clean separation of concerns for terrain, bedding sites, and stand positions.
Supports Vermont whitetail deer ecology with biological validation.
"""

from .terrain import TerrainMetrics, TerrainGrid, AspectCalculator
from .bedding_site import BeddingZone, BeddingZoneCandidate, BeddingScoreBreakdown
from .stand_site import StandPosition, StandType, ScentManagementResult

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
]
