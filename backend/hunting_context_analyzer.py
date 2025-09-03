#!/usr/bin/env python3
"""
Hunting Context Analyzer - Real-Time Decision System

Determines what hunters should actually DO right now based on current time,
legal light, and deer behavior patterns. Provides contextually appropriate
recommendations instead of generic planning advice.

Author: GitHub Copilot
Version: 1.0.0
Date: September 3, 2025
"""

import logging
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class HuntingContext(Enum):
    """Current hunting context based on time and conditions"""
    ACTIVE_HUNT = "active_hunt"           # Currently in legal light, hunt in progress
    END_OF_DAY = "end_of_day"            # Legal light ending soon (< 30 min)
    POST_HUNT = "post_hunt"              # After legal light ends
    PRE_HUNT = "pre_hunt"                # Before legal light begins
    PLANNING_MODE = "planning_mode"       # >2 hours from next hunt window

class ActionContext(Enum):
    """What the hunter should actually do right now"""
    STAY_PUT = "stay_put"                # Don't move, optimize current position
    LAST_CHANCE = "last_chance"          # Final opportunity setup
    PACK_OUT = "pack_out"                # Hunt over, exit quietly
    SCOUT_MODE = "scout_mode"            # Observe without hunting
    PLAN_TOMORROW = "plan_tomorrow"      # Prepare for next hunt

def calculate_legal_hunting_hours(hunt_date: date) -> Tuple[time, time]:
    """
    Calculate legal hunting hours for Vermont based on date.
    Vermont: 30 minutes before sunrise to 30 minutes after sunset.
    """
    # Vermont sunrise/sunset approximations (Montpelier)
    sunrise_times = {
        1: (7, 26), 2: (7, 8), 3: (6, 27), 4: (6, 31), 5: (5, 41), 6: (5, 9),
        7: (5, 10), 8: (5, 38), 9: (6, 13), 10: (6, 48), 11: (7, 28), 12: (7, 6)
    }
    
    sunset_times = {
        1: (16, 22), 2: (17, 0), 3: (17, 39), 4: (19, 18), 5: (19, 54), 6: (20, 27),
        7: (20, 38), 8: (20, 14), 9: (19, 26), 10: (18, 31), 11: (16, 40), 12: (16, 13)
    }
    
    month = hunt_date.month
    sunrise_hour, sunrise_min = sunrise_times.get(month, (6, 30))
    sunset_hour, sunset_min = sunset_times.get(month, (18, 30))
    
    # Create datetime objects for calculation
    sunrise_dt = datetime.combine(hunt_date, time(sunrise_hour, sunrise_min))
    sunset_dt = datetime.combine(hunt_date, time(sunset_hour, sunset_min))
    
    # Calculate legal hours (30 min before sunrise to 30 min after sunset)
    earliest_hunting = (sunrise_dt - timedelta(minutes=30)).time()
    latest_hunting = (sunset_dt + timedelta(minutes=30)).time()
    
    return earliest_hunting, latest_hunting

def analyze_hunting_context(current_time: datetime) -> Dict:
    """
    Analyze current hunting context and determine appropriate actions.
    
    Args:
        current_time: Current datetime
        
    Returns:
        Dict with context analysis and recommended actions
    """
    hunt_date = current_time.date()
    current_time_only = current_time.time()
    
    # Get legal hunting hours
    earliest_hunt, latest_hunt = calculate_legal_hunting_hours(hunt_date)
    
    # Calculate time differences
    current_dt = datetime.combine(hunt_date, current_time_only)
    earliest_dt = datetime.combine(hunt_date, earliest_hunt)
    latest_dt = datetime.combine(hunt_date, latest_hunt)
    
    # Determine context
    if current_time_only < earliest_hunt:
        # Before legal light
        time_to_hunt = (earliest_dt - current_dt).total_seconds() / 3600  # hours
        if time_to_hunt < 2:
            context = HuntingContext.PRE_HUNT
            action = ActionContext.SCOUT_MODE
        else:
            context = HuntingContext.PLANNING_MODE
            action = ActionContext.PLAN_TOMORROW
            
    elif current_time_only > latest_hunt:
        # After legal light
        context = HuntingContext.POST_HUNT
        action = ActionContext.PACK_OUT
        
    else:
        # During legal hunting hours
        time_remaining = (latest_dt - current_dt).total_seconds() / 60  # minutes
        if time_remaining < 30:
            context = HuntingContext.END_OF_DAY
            action = ActionContext.LAST_CHANCE if time_remaining > 10 else ActionContext.STAY_PUT
        else:
            context = HuntingContext.ACTIVE_HUNT
            action = ActionContext.STAY_PUT if current_time_only.hour >= 17 else ActionContext.SCOUT_MODE
    
    # Calculate next hunt window
    if current_time_only > latest_hunt:
        # Next hunt is tomorrow morning
        next_hunt_date = hunt_date + timedelta(days=1)
        next_earliest, _ = calculate_legal_hunting_hours(next_hunt_date)
        next_hunt_dt = datetime.combine(next_hunt_date, next_earliest)
        hours_to_next_hunt = (next_hunt_dt - current_dt).total_seconds() / 3600
    else:
        # Next hunt is this evening or tomorrow
        if current_time_only < earliest_hunt:
            next_hunt_dt = earliest_dt
        else:
            # Currently hunting, next is tomorrow
            next_hunt_date = hunt_date + timedelta(days=1)
            next_earliest, _ = calculate_legal_hunting_hours(next_hunt_date)
            next_hunt_dt = datetime.combine(next_hunt_date, next_earliest)
        hours_to_next_hunt = (next_hunt_dt - current_dt).total_seconds() / 3600
    
    return {
        'context': context,
        'action': action,
        'legal_hours': {
            'earliest': earliest_hunt.strftime('%H:%M'),
            'latest': latest_hunt.strftime('%H:%M')
        },
        'current_status': {
            'is_legal_light': earliest_hunt <= current_time_only <= latest_hunt,
            'time_remaining_minutes': max(0, (latest_dt - current_dt).total_seconds() / 60) if current_time_only <= latest_hunt else 0,
            'hours_to_next_hunt': hours_to_next_hunt
        },
        'recommendations': _get_context_specific_recommendations(context, action, current_time_only, latest_hunt)
    }

def _get_context_specific_recommendations(context: HuntingContext, action: ActionContext, 
                                        current_time: time, latest_hunt: time) -> Dict:
    """Generate context-specific recommendations based on hunting situation"""
    
    if context == HuntingContext.END_OF_DAY:
        if action == ActionContext.STAY_PUT:
            return {
                'primary': "🛑 STAY PUT - Movement is over for the day",
                'secondary': "Legal light ends in minutes. Any movement now will spook deer.",
                'specific_actions': [
                    "Remain completely still in current position",
                    "Observe deer movement patterns for tomorrow's intel",
                    "Wait 30+ minutes after dark before moving",
                    "Exit as quietly as possible when ready"
                ],
                'timing': "Hunt over in < 10 minutes"
            }
        else:  # LAST_CHANCE
            return {
                'primary': "⚡ LAST CHANCE - Final setup opportunity",
                'secondary': f"Legal light ends at {latest_hunt.strftime('%H:%M')}. Quick setup only.",
                'specific_actions': [
                    "Move to closest high-probability observation point",
                    "Set up within 5 minutes maximum",
                    "Focus on open areas where deer might feed",
                    "Prepare for low-light observation"
                ],
                'timing': f"Final hunting window: {(datetime.combine(date.today(), latest_hunt) - datetime.combine(date.today(), current_time)).seconds // 60} minutes"
            }
            
    elif context == HuntingContext.POST_HUNT:
        return {
            'primary': "🌙 HUNT OVER - Quiet exit mode",
            'secondary': "Legal hunting hours have ended. Focus on exit strategy.",
            'specific_actions': [
                "Wait minimum 30 minutes before moving (let deer settle)",
                "Use headlamp on red setting for navigation",
                "Take notes on deer movement observed today",
                "Plan tomorrow's strategy based on today's observations"
            ],
            'timing': "Next hunt window: Tomorrow morning"
        }
        
    elif context == HuntingContext.ACTIVE_HUNT:
        if current_time.hour >= 17:  # Evening hunt
            return {
                'primary': "🦌 EVENING HUNT ACTIVE - Bedding to feeding movement",
                'secondary': "Deer should start moving from bedding areas to feeding areas.",
                'specific_actions': [
                    "Watch travel corridors between bedding and feeding areas",
                    "Focus on field edges and openings",
                    "Prepare for deer movement in next 1-2 hours",
                    "Stay alert for feeding activity"
                ],
                'timing': "Prime evening movement period"
            }
        else:  # Morning/midday
            return {
                'primary': "☀️ MIDDAY SCOUTING - Low activity period",
                'secondary': "Deer likely bedded. Use time for observation and intelligence gathering.",
                'specific_actions': [
                    "Observe bedding area boundaries (from distance)",
                    "Note travel routes and sign",
                    "Position for evening movement",
                    "Minimize disturbance to bedded deer"
                ],
                'timing': "Building intel for evening hunt"
            }
            
    else:  # PRE_HUNT or PLANNING_MODE
        return {
            'primary': "📋 PLANNING MODE - Prepare for next hunt",
            'secondary': "Use this time to plan and prepare for the next hunting window.",
            'specific_actions': [
                "Review wind direction for next hunt period",
                "Check weather conditions and thermal predictions",
                "Plan approach routes and stand locations",
                "Prepare gear and equipment"
            ],
            'timing': "Next hunt preparation time"
        }

def create_time_aware_prediction_context(prediction_result: Dict, current_time: datetime) -> Dict:
    """
    Modify prediction results to be contextually appropriate for current time.
    
    Args:
        prediction_result: Standard prediction output
        current_time: Current datetime
        
    Returns:
        Modified prediction with time-appropriate context
    """
    context_analysis = analyze_hunting_context(current_time)
    
    # Override generic recommendations with time-specific ones
    prediction_result['hunting_context'] = context_analysis
    prediction_result['context_override'] = True
    prediction_result['original_timestamp'] = prediction_result.get('timestamp', 'unknown')
    prediction_result['context_timestamp'] = current_time.isoformat()
    
    # Modify stand recommendations based on context
    if 'mature_buck_analysis' in prediction_result:
        stands = prediction_result['mature_buck_analysis'].get('stand_recommendations', [])
        for stand in stands:
            _add_context_to_stand(stand, context_analysis)
    
    # Add context-specific summary
    prediction_result['context_summary'] = {
        'situation': context_analysis['context'].value,
        'recommended_action': context_analysis['action'].value,
        'primary_guidance': context_analysis['recommendations']['primary'],
        'time_remaining': context_analysis['current_status']['time_remaining_minutes']
    }
    
    return prediction_result

def _add_context_to_stand(stand: Dict, context_analysis: Dict) -> None:
    """Add time-context information to individual stand recommendations"""
    context = context_analysis['context']
    
    if context in [HuntingContext.END_OF_DAY, HuntingContext.POST_HUNT]:
        stand['context_note'] = "⚠️ Hunt window ending/ended - Observation only"
        stand['action_priority'] = "LOW"
    elif context == HuntingContext.ACTIVE_HUNT:
        stand['context_note'] = "✅ Active hunting window - Move with caution"
        stand['action_priority'] = "HIGH"
    else:
        stand['context_note'] = "📋 Planning mode - Prepare for next hunt"
        stand['action_priority'] = "MEDIUM"
