#!/usr/bin/env python3
"""
GPX Parser for Deer Prediction App

Safely parses GPX files and converts waypoints to scouting observations.
Handles various GPX formats from hunting GPS devices and apps.

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import logging
import re

try:
    from .scouting_models import ScoutingObservation, ObservationType
except ImportError:
    from scouting_models import ScoutingObservation, ObservationType

logger = logging.getLogger(__name__)


class GPXParser:
    """Safe GPX file parser for hunting waypoints"""
    
    def __init__(self):
        # Comprehensive mapping of hunting waypoint names/types to observation types
        # This expanded list should catch most hunting-related waypoints
        self.waypoint_type_mapping = {
            # Scrapes - all variations
            'scrape': ObservationType.FRESH_SCRAPE,
            'scrapes': ObservationType.FRESH_SCRAPE,
            'fresh scrape': ObservationType.FRESH_SCRAPE,
            'buck scrape': ObservationType.FRESH_SCRAPE,
            'big scrape': ObservationType.FRESH_SCRAPE,
            'new scrape': ObservationType.FRESH_SCRAPE,
            
            # Rubs - all variations
            'rub': ObservationType.RUB_LINE,
            'rubs': ObservationType.RUB_LINE,
            'buck rub': ObservationType.RUB_LINE,
            'rub line': ObservationType.RUB_LINE,
            'rubbing': ObservationType.RUB_LINE,
            'tree rub': ObservationType.RUB_LINE,
            
            # Bedding - all variations
            'bed': ObservationType.BEDDING_AREA,
            'beds': ObservationType.BEDDING_AREA,
            'bedding': ObservationType.BEDDING_AREA,
            'bedding area': ObservationType.BEDDING_AREA,
            'deer bed': ObservationType.BEDDING_AREA,
            'buck bed': ObservationType.BEDDING_AREA,
            'sleeping': ObservationType.BEDDING_AREA,
            'lay': ObservationType.BEDDING_AREA,
            'laying': ObservationType.BEDDING_AREA,
            
            # Tracks and trails
            'track': ObservationType.DEER_TRACKS,
            'tracks': ObservationType.DEER_TRACKS,
            'trail': ObservationType.DEER_TRACKS,
            'trails': ObservationType.DEER_TRACKS,
            'deer trail': ObservationType.DEER_TRACKS,
            'game trail': ObservationType.DEER_TRACKS,
            'path': ObservationType.DEER_TRACKS,
            'deer path': ObservationType.DEER_TRACKS,
            'hoofprint': ObservationType.DEER_TRACKS,
            'hoofprints': ObservationType.DEER_TRACKS,
            
            # Cameras
            'camera': ObservationType.TRAIL_CAMERA,
            'cam': ObservationType.TRAIL_CAMERA,
            'trail cam': ObservationType.TRAIL_CAMERA,
            'trailcam': ObservationType.TRAIL_CAMERA,
            'trail camera': ObservationType.TRAIL_CAMERA,
            'game camera': ObservationType.TRAIL_CAMERA,
            'scout cam': ObservationType.TRAIL_CAMERA,
            
            # Feeding areas
            'feed': ObservationType.FEEDING_SIGN,
            'feeding': ObservationType.FEEDING_SIGN,
            'food': ObservationType.FEEDING_SIGN,
            'food plot': ObservationType.FEEDING_SIGN,
            'browse': ObservationType.FEEDING_SIGN,
            'browsing': ObservationType.FEEDING_SIGN,
            'eating': ObservationType.FEEDING_SIGN,
            'acorn': ObservationType.FEEDING_SIGN,
            'acorns': ObservationType.FEEDING_SIGN,
            'oak': ObservationType.FEEDING_SIGN,
            'apple': ObservationType.FEEDING_SIGN,
            'apples': ObservationType.FEEDING_SIGN,
            'corn': ObservationType.FEEDING_SIGN,
            'mast': ObservationType.FEEDING_SIGN,
            
            # Scat and droppings
            'scat': ObservationType.SCAT_DROPPINGS,
            'droppings': ObservationType.SCAT_DROPPINGS,
            'poop': ObservationType.SCAT_DROPPINGS,
            'pellets': ObservationType.SCAT_DROPPINGS,
            'manure': ObservationType.SCAT_DROPPINGS,
            
            # Hunting locations - treat as OTHER_SIGN but still import
            'stand': ObservationType.OTHER_SIGN,
            'stands': ObservationType.OTHER_SIGN,
            'tree stand': ObservationType.OTHER_SIGN,
            'treestand': ObservationType.OTHER_SIGN,
            'ladder stand': ObservationType.OTHER_SIGN,
            'hang on': ObservationType.OTHER_SIGN,
            'climbing stand': ObservationType.OTHER_SIGN,
            'blind': ObservationType.OTHER_SIGN,
            'ground blind': ObservationType.OTHER_SIGN,
            'bow blind': ObservationType.OTHER_SIGN,
            'hunting spot': ObservationType.OTHER_SIGN,
            'hunt spot': ObservationType.OTHER_SIGN,
            'hunt': ObservationType.OTHER_SIGN,
            'hunting': ObservationType.OTHER_SIGN,
            'hunt area': ObservationType.OTHER_SIGN,
            'deer area': ObservationType.OTHER_SIGN,
            'buck area': ObservationType.OTHER_SIGN,
            
            # General deer-related terms
            'deer': ObservationType.OTHER_SIGN,
            'buck': ObservationType.OTHER_SIGN,
            'doe': ObservationType.OTHER_SIGN,
            'fawn': ObservationType.OTHER_SIGN,
            'antler': ObservationType.OTHER_SIGN,
            'antlers': ObservationType.OTHER_SIGN,
            'deer sign': ObservationType.OTHER_SIGN,
            'sign': ObservationType.OTHER_SIGN,
            
            # Terrain features that hunters commonly mark
            'crossing': ObservationType.OTHER_SIGN,
            'deer crossing': ObservationType.OTHER_SIGN,
            'funnel': ObservationType.OTHER_SIGN,
            'pinch': ObservationType.OTHER_SIGN,
            'pinch point': ObservationType.OTHER_SIGN,
            'saddle': ObservationType.OTHER_SIGN,
            'ridge': ObservationType.OTHER_SIGN,
            'draw': ObservationType.OTHER_SIGN,
            'bottom': ObservationType.OTHER_SIGN,
            'creek bottom': ObservationType.OTHER_SIGN,
            'field edge': ObservationType.OTHER_SIGN,
            'fence row': ObservationType.OTHER_SIGN,
            'transition': ObservationType.OTHER_SIGN,
            'edge': ObservationType.OTHER_SIGN,
            'thicket': ObservationType.OTHER_SIGN,
            'cover': ObservationType.OTHER_SIGN,
            'thick cover': ObservationType.OTHER_SIGN,
            
            # Observation/scouting terms
            'scout': ObservationType.OTHER_SIGN,
            'scouting': ObservationType.OTHER_SIGN,
            'observation': ObservationType.OTHER_SIGN,
            'watch': ObservationType.OTHER_SIGN,
            'lookout': ObservationType.OTHER_SIGN,
            'vantage': ObservationType.OTHER_SIGN,
            'overlook': ObservationType.OTHER_SIGN,
        }
    
    def parse_gpx_file(self, file_content: str) -> Dict[str, Any]:
        """
        Safely parse GPX file content and return waypoints
        
        Args:
            file_content: String content of GPX file
            
        Returns:
            Dict with parsed waypoints and metadata
        """
        try:
            # Parse XML safely
            root = ET.fromstring(file_content)
            
            # Handle different GPX namespaces
            namespace = self._detect_namespace(root)
            
            # Extract waypoints
            waypoints = self._extract_waypoints(root, namespace)
            
            # Extract metadata
            metadata = self._extract_metadata(root, namespace)
            
            return {
                'success': True,
                'waypoints': waypoints,
                'metadata': metadata,
                'total_waypoints': len(waypoints),
                'message': f"Successfully parsed {len(waypoints)} waypoints"
            }
            
        except ET.ParseError as e:
            logger.error(f"GPX XML parsing error: {e}")
            return {
                'success': False,
                'error': f"Invalid GPX file format: {e}",
                'waypoints': [],
                'metadata': {}
            }
        except Exception as e:
            logger.error(f"Unexpected GPX parsing error: {e}")
            return {
                'success': False,
                'error': f"Failed to parse GPX file: {e}",
                'waypoints': [],
                'metadata': {}
            }
    
    def convert_to_scouting_observations(self, waypoints: List[Dict]) -> List[ScoutingObservation]:
        """
        Convert GPX waypoints to scouting observations
        
        Args:
            waypoints: List of parsed waypoint dictionaries
            
        Returns:
            List of ScoutingObservation objects
        """
        observations = []
        
        for wp in waypoints:
            try:
                observation = self._convert_waypoint_to_observation(wp)
                if observation:
                    observations.append(observation)
            except Exception as e:
                logger.warning(f"Failed to convert waypoint '{wp.get('name', 'Unknown')}': {e}")
                continue
        
        logger.info(f"Converted {len(observations)} waypoints to scouting observations")
        return observations
    
    def _detect_namespace(self, root: ET.Element) -> str:
        """Detect GPX namespace from root element"""
        tag = root.tag
        if '}' in tag:
            return tag.split('}')[0] + '}'
        return ''
    
    def _extract_waypoints(self, root: ET.Element, namespace: str) -> List[Dict]:
        """Extract waypoints from GPX"""
        waypoints = []
        
        for wpt in root.findall(f'.//{namespace}wpt'):
            try:
                waypoint = self._parse_waypoint(wpt, namespace)
                if waypoint:
                    waypoints.append(waypoint)
            except Exception as e:
                logger.warning(f"Failed to parse waypoint: {e}")
                continue
        
        return waypoints
    
    def _parse_waypoint(self, wpt: ET.Element, namespace: str) -> Optional[Dict]:
        """Parse individual waypoint element"""
        try:
            # Required coordinates
            lat = float(wpt.get('lat', 0))
            lon = float(wpt.get('lon', 0))
            
            if lat == 0 or lon == 0:
                return None
            
            # Basic waypoint data
            waypoint = {
                'lat': lat,
                'lon': lon,
                'name': self._get_element_text(wpt, f'{namespace}name', 'Unnamed Waypoint'),
                'description': self._get_element_text(wpt, f'{namespace}desc', ''),
                'type': self._get_element_text(wpt, f'{namespace}type', ''),
                'symbol': self._get_element_text(wpt, f'{namespace}sym', ''),
                'elevation': self._get_element_text(wpt, f'{namespace}ele', None),
                'time': self._get_element_text(wpt, f'{namespace}time', None),
            }
            
            # Parse extensions for additional data
            extensions = wpt.find(f'{namespace}extensions')
            if extensions is not None:
                waypoint['extensions'] = self._parse_extensions(extensions)
            
            return waypoint
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid waypoint coordinates: {e}")
            return None
    
    def _get_element_text(self, parent: ET.Element, tag: str, default: Any = None) -> Any:
        """Safely get text from XML element"""
        element = parent.find(tag)
        if element is not None and element.text:
            return element.text.strip()
        return default
    
    def _parse_extensions(self, extensions: ET.Element) -> Dict[str, str]:
        """Parse GPX extensions for additional metadata"""
        ext_data = {}
        for child in extensions:
            if child.text:
                # Remove namespace from tag name
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                ext_data[tag] = child.text.strip()
        return ext_data
    
    def _extract_metadata(self, root: ET.Element, namespace: str) -> Dict[str, Any]:
        """Extract GPX file metadata"""
        metadata = {}
        
        # Look for metadata element
        meta = root.find(f'{namespace}metadata')
        if meta is not None:
            metadata['name'] = self._get_element_text(meta, f'{namespace}name')
            metadata['description'] = self._get_element_text(meta, f'{namespace}desc')
            metadata['author'] = self._get_element_text(meta, f'{namespace}author')
            metadata['time'] = self._get_element_text(meta, f'{namespace}time')
        
        # Creator info from root
        metadata['creator'] = root.get('creator', 'Unknown')
        metadata['version'] = root.get('version', '1.1')
        
        return metadata
    
    def _convert_waypoint_to_observation(self, waypoint: Dict) -> Optional[ScoutingObservation]:
        """Convert a waypoint dictionary to ScoutingObservation"""
        try:
            # Determine observation type from name/description/type
            obs_type = self._determine_observation_type(waypoint)
            
            # Skip waypoints that aren't hunting-related
            if obs_type is None:
                logger.info(f"⏭️ Skipping waypoint: {waypoint.get('name', 'Unknown')}")
                return None
            
            # Parse timestamp
            timestamp = self._parse_timestamp(waypoint.get('time'))
            
            # Estimate confidence based on available information
            confidence = self._estimate_confidence(waypoint)
            
            # Create observation
            observation = ScoutingObservation(
                lat=waypoint['lat'],
                lon=waypoint['lon'],
                observation_type=obs_type,
                notes=self._build_notes(waypoint),
                confidence=confidence,
                timestamp=timestamp
            )
            
            return observation
            
        except Exception as e:
            logger.error(f"Failed to convert waypoint to observation: {e}")
            return None
    
    def _determine_observation_type(self, waypoint: Dict) -> ObservationType:
        """Determine observation type from waypoint data with enhanced detection"""
        # Collect all text fields for analysis
        text_fields = [
            waypoint.get('name', ''),
            waypoint.get('description', ''),
            waypoint.get('type', ''),
            waypoint.get('symbol', '')
        ]
        
        # Combine all text and normalize
        full_text = ' '.join(text_fields).lower().strip()
        
        # Debug logging
        logger.info(f"🔍 Analyzing waypoint: '{waypoint.get('name', 'Unknown')}' - Full text: '{full_text[:100]}'")
        
        # Check for exact matches first
        for keyword, obs_type in self.waypoint_type_mapping.items():
            if keyword in full_text:
                logger.info(f"✅ Matched keyword '{keyword}' → {obs_type.value}")
                return obs_type
        
        # If no exact match, check for partial matches with hunting-related terms
        hunting_indicators = [
            'deer', 'buck', 'doe', 'hunt', 'bow', 'gun', 'season',
            'morning', 'evening', 'shot', 'kill', 'harvest',
            'antler', 'rack', 'horn', 'spike', 'point',
            'big', 'large', 'huge', 'monster', 'trophy',
            'good', 'great', 'best', 'prime', 'hot',
            'fresh', 'new', 'old', 'active', 'used',
            'wildlife', 'game', 'sign', 'bait', 'feeder'
        ]
        
        # Check if this seems hunting-related at all
        is_hunting_related = any(indicator in full_text for indicator in hunting_indicators)
        
        # Check for numbers/coordinates that might indicate hunting spots
        has_numbers = any(char.isdigit() for char in full_text)
        
        if is_hunting_related or (has_numbers and len(full_text) < 50):
            logger.info(f"📍 Waypoint seems hunting-related, categorizing as OTHER_SIGN: '{full_text[:50]}'")
            return ObservationType.OTHER_SIGN
        
        # Log what we're skipping and why
        logger.info(f"⏭️ Skipping non-hunting waypoint: '{full_text[:50]}'")
        
        # Return None to indicate this waypoint should be skipped
        return None
        if any(term in full_text for term in hunting_terms):
            return ObservationType.OTHER_SIGN
        
        # For non-hunting waypoints, skip them (return None to indicate skip)
        return None
    
    def _parse_timestamp(self, time_str: Optional[str]) -> datetime:
        """Parse timestamp from GPX time string"""
        if not time_str:
            return datetime.now()
        
        try:
            # Try ISO format first
            if 'T' in time_str:
                return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            else:
                # Try other common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                    try:
                        return datetime.strptime(time_str, fmt)
                    except ValueError:
                        continue
        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{time_str}': {e}")
        
        return datetime.now()
    
    def _estimate_confidence(self, waypoint: Dict) -> int:
        """Estimate confidence level based on available waypoint data with enhanced date precedence"""
        confidence = 5  # Base confidence
        
        # More detailed description = higher confidence
        desc = waypoint.get('description', '')
        if len(desc) > 50:
            confidence += 2
        elif len(desc) > 20:
            confidence += 1
        
        # ENHANCED: Recent waypoints get much higher confidence
        if waypoint.get('time'):
            try:
                wp_time = self._parse_timestamp(waypoint.get('time'))
                
                # Make both datetimes timezone-aware for proper comparison
                if wp_time.tzinfo is not None:
                    # wp_time is timezone-aware, make now() timezone-aware too
                    now = datetime.now(timezone.utc)
                else:
                    # wp_time is timezone-naive, use naive now()
                    now = datetime.now()
                
                days_old = (now - wp_time).days
                
                # NEW: Much more aggressive date-based confidence
                if days_old < 1:  # Today
                    confidence += 4  # Highest boost for today's data
                    logger.info(f"📅 TODAY'S DATA: +4 confidence boost")
                elif days_old < 7:  # This week
                    confidence += 3
                    logger.info(f"📅 This week: +3 confidence boost ({days_old} days old)")
                elif days_old < 30:  # This month
                    confidence += 2
                    logger.info(f"📅 This month: +2 confidence boost ({days_old} days old)")
                elif days_old < 365:  # This year
                    confidence += 1
                    logger.info(f"📅 This year: +1 confidence boost ({days_old} days old)")
                elif days_old < 1095:  # Last 3 years
                    confidence += 0  # No penalty, but no boost
                    logger.info(f"📅 Recent years: No boost ({days_old} days old)")
                else:  # Old data (3+ years)
                    confidence -= 1  # Slight penalty for very old data
                    logger.info(f"📅 Old data: -1 confidence penalty ({days_old} days old)")
                    
            except Exception as e:
                logger.warning(f"Failed to parse waypoint timestamp: {e}")
        
        # Ensure confidence stays within bounds
        return max(1, min(confidence, 10))
    
    def _build_notes(self, waypoint: Dict) -> str:
        """Build notes from waypoint data"""
        notes = []
        
        if waypoint.get('description'):
            notes.append(f"Description: {waypoint['description']}")
        
        if waypoint.get('symbol'):
            notes.append(f"Symbol: {waypoint['symbol']}")
        
        if waypoint.get('elevation'):
            notes.append(f"Elevation: {waypoint['elevation']}")
        
        if waypoint.get('extensions'):
            for key, value in waypoint['extensions'].items():
                notes.append(f"{key}: {value}")
        
        notes.append("Imported from GPX file")
        
        return " | ".join(notes)


def get_gpx_parser() -> GPXParser:
    """Get GPX parser instance"""
    return GPXParser()
