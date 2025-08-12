"""
Vermont Deer Prediction System Backend Package
"""

# Version information
__version__ = "1.0.0"

# Expose key components at package level
from .core import get_prediction_core
from .mature_buck_predictor import MatureBuckPreferences, MatureBuckBehaviorModel
from .scoring_engine import get_scoring_engine, ScoringContext
from .scouting_data_manager import get_scouting_data_manager
from .scouting_prediction_enhancer import get_scouting_enhancer
from .distance_scorer import get_distance_scorer