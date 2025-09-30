"""Data contract utilities for scouting data imports.

This module focuses on defining canonical waypoint records and helper
functions that convert GPX waypoints into the existing
`ScoutingObservation` schema. The actual persistence layer is handled by
`ScoutingDataManager`; these helpers are intentionally side-effect free
so they can be validated in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Iterable, List, Optional
from xml.etree import ElementTree as ET

from backend.scouting_models import ObservationType


@dataclass(frozen=True)
class WaypointRecord:
    """Lightweight representation of a GPX waypoint.

    Attributes
    ----------
    lat, lon: Geographic coordinates in decimal degrees.
    elevation_m: Optional elevation in meters.
    time_utc: Optional UTC timestamp extracted from the GPX waypoint.
    name: Waypoint name/label.
    description: Optional extended description.
    symbol: Optional symbol identifier provided by the GPS exporter.
    """

    lat: float
    lon: float
    elevation_m: Optional[float]
    time_utc: Optional[datetime]
    name: str
    description: Optional[str]
    symbol: Optional[str]

    @classmethod
    def from_element(cls, element: ET.Element) -> "WaypointRecord":
        """Create a record from a `<wpt>` element.

        Parameters
        ----------
        element:
            The XML element representing a waypoint. Namespaces are
            already resolved by callers via `ElementTree`.
        """

        lat = float(element.attrib["lat"])
        lon = float(element.attrib["lon"])

        elevation: Optional[float] = None
        timestamp: Optional[datetime] = None
        name: str = ""
        description: Optional[str] = None
        symbol: Optional[str] = None

        for child in element:
            tag = child.tag.split("}")[-1]
            text = (child.text or "").strip()
            if not text:
                continue

            if tag == "ele":
                try:
                    elevation = float(text)
                except ValueError:
                    # Leave elevation as None if parsing fails
                    elevation = None
            elif tag == "time":
                timestamp = _parse_iso8601(text)
            elif tag == "name":
                name = text
            elif tag == "desc":
                description = text
            elif tag == "sym":
                symbol = text

        return cls(
            lat=lat,
            lon=lon,
            elevation_m=elevation,
            time_utc=timestamp,
            name=name,
            description=description,
            symbol=symbol,
        )
def load_gpx_waypoints(path: Path | str) -> List[WaypointRecord]:
    """Load waypoints from a GPX file path."""

    gpx_path = Path(path)
    if not gpx_path.exists():
        raise FileNotFoundError(gpx_path)

    tree = ET.parse(gpx_path)
    return _waypoints_from_tree(tree)


def load_gpx_waypoints_from_bytes(data: bytes) -> List[WaypointRecord]:
    """Load waypoints from raw GPX bytes."""

    if not data:
        return []
    tree = ET.parse(BytesIO(data))
    return _waypoints_from_tree(tree)


def canonical_observation_payload(record: WaypointRecord) -> dict:
    """Convert a waypoint into a dictionary compatible with
    `ScoutingObservation`.

    The importer layer can enrich this payload further (for example,
    attaching GPX metadata), but the core fields are validated here so
    downstream units can rely on a consistent schema.
    """

    inference_source = " ".join(
        filter(None, [record.name, record.description, record.symbol])
    ).lower()

    observation_type = _infer_observation_type(inference_source)

    notes_parts: List[str] = []
    if record.name:
        notes_parts.append(record.name.strip())
    if record.description:
        notes_parts.append(record.description.strip())
    if record.symbol:
        notes_parts.append(f"[symbol:{record.symbol.strip()}]")
    if record.elevation_m is not None:
        notes_parts.append(f"Elevation {record.elevation_m:.0f}m")

    timestamp = record.time_utc or datetime.now(timezone.utc)

    payload = {
        "lat": record.lat,
        "lon": record.lon,
        "observation_type": observation_type,
        "notes": "\n".join(notes_parts),
        # Default to a moderate confidence; downstream calibration can
        # adjust this based on historical accuracy.
        "confidence": 6,
        "timestamp": timestamp,
        "photo_urls": [],
        "weather_conditions": None,
        "scrape_details": None,
        "rub_details": None,
        "bedding_details": None,
        "camera_details": None,
        "tracks_details": None,
    }

    # Attach type-specific defaults to ease later enrichment.
    if observation_type == ObservationType.FRESH_SCRAPE:
        payload["scrape_details"] = {
            "size": "Medium",
            "freshness": "Recent",
            "licking_branch": True,
            "multiple_scrapes": False,
        }
    elif observation_type == ObservationType.RUB_LINE:
        payload["rub_details"] = {
            "tree_diameter_inches": 4,
            "rub_height_inches": 36,
            "direction": "Multiple",
            "tree_species": None,
            "multiple_rubs": True,
        }
    elif observation_type == ObservationType.BEDDING_AREA:
        payload["bedding_details"] = {
            "number_of_beds": 1,
            "bed_size": "Medium (young buck)",
            "cover_type": "Unknown",
            "visibility": "Moderate",
            "escape_routes": 2,
        }
    elif observation_type == ObservationType.TRAIL_CAMERA:
        payload["camera_details"] = {
            "camera_brand": None,
            "setup_date": timestamp,
            "total_photos": 0,
            "deer_photos": 0,
            "mature_buck_photos": 0,
            "peak_activity_time": None,
            "battery_level": None,
        }
    elif observation_type == ObservationType.DEER_TRACKS:
        payload["tracks_details"] = {
            "track_size_inches": 3.0,
            "track_depth": "Medium",
            "number_of_tracks": 1,
            "direction_of_travel": "Unknown",
            "gait_pattern": "Walking",
        }

    return payload


def _waypoints_from_tree(tree: ET.ElementTree) -> List[WaypointRecord]:
    root = tree.getroot()
    namespace = _detect_namespace(root)
    waypoints: List[WaypointRecord] = []
    for element in root.findall(f"{namespace}wpt"):
        waypoints.append(WaypointRecord.from_element(element))
    return waypoints


def _parse_iso8601(value: str) -> datetime:
    """Parse ISO 8601 timestamp strings, including trailing Z."""

    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        # Some exporters omit timezone info; treat as naive UTC
        dt = datetime.fromisoformat(value)
        dt = dt.replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _detect_namespace(element: ET.Element) -> str:
    """Return the XML namespace string (including braces) or empty."""

    if element.tag[0] == "{":
        uri = element.tag[1:].split("}")[0]
        return f"{{{uri}}}"
    return ""


_KEYWORD_MAP: List[tuple[ObservationType, tuple[str, ...]]] = [
    (ObservationType.FRESH_SCRAPE, ("scrape", "licking", "scrapes")),
    # Prioritise bedding-related keywords before rub detection so mixed
    # phrases like "buck bed hair and rub" classify as bedding areas.
    (ObservationType.BEDDING_AREA, ("bed", "bedding")),
    (ObservationType.RUB_LINE, ("rub", "rubs", "rubline")),
    (ObservationType.TRAIL_CAMERA, ("camera", "trail cam")),
    (ObservationType.DEER_TRACKS, ("track", "tracks", "trail")),
    (ObservationType.FEEDING_SIGN, ("acorn", "apple", "feeding", "food")),
    (ObservationType.DEER_SIGHTING, ("buck", "doe", "deer", "sighting")),
]


def _infer_observation_type(text: str) -> ObservationType:
    for obs_type, keywords in _KEYWORD_MAP:
        if any(keyword in text for keyword in keywords):
            return obs_type
    return ObservationType.OTHER_SIGN


__all__ = [
    "WaypointRecord",
    "load_gpx_waypoints",
    "canonical_observation_payload",
]
