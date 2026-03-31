"""Data contract utilities for scouting data imports.

This module focuses on defining canonical waypoint records and helper
functions that convert GPX waypoints into the existing
`ScoutingObservation` schema. The actual persistence layer is handled by
`ScoutingDataManager`; these helpers are intentionally side-effect free
so they can be validated in isolation.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
from xml.etree import ElementTree as ET

from backend.scouting_models import ObservationType


# ---------------------------------------------------------------------------
# Date extraction from waypoint text (OnX / common hunting-GPS patterns)
# ---------------------------------------------------------------------------

# Patterns ordered from most precise to least precise.
_DATE_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
    # MM/DD/YY HH:MM  e.g. "09/13/25 11:52"
    (re.compile(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\s+(\d{1,2}):(\d{2})\b'), 'datetime', 'exact'),
    # MM/DD/YYYY or MM/DD/YY  e.g. "10/1/20"
    (re.compile(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b'), 'date', 'day'),
    # YYYY-MM-DD (ISO-like in free text)
    (re.compile(r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b'), 'iso_date', 'day'),
    # Month DD, YYYY  e.g. "October 1, 2020"
    (re.compile(
        r'\b(January|February|March|April|May|June|July|August|September|'
        r'October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b',
        re.IGNORECASE,
    ), 'long_date', 'day'),
    # Mon YYYY  e.g. "Oct 2020" (no day)
    (re.compile(
        r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\b',
        re.IGNORECASE,
    ), 'month_year', 'month'),
    # Bare 4-digit year  e.g. "scrape 2017"  (only 2000–2039 to avoid
    # matching elevation or other numeric noise)
    (re.compile(r'\b(20[0-3]\d)\b'), 'year_only', 'year'),
]

_MONTH_NAMES = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
    'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
    'oct': 10, 'nov': 11, 'dec': 12,
}


def _expand_two_digit_year(y: int) -> int:
    """Convert 2-digit year to 4-digit (00-39 → 2000s, 40-99 → 1900s)."""
    if y < 100:
        return y + 2000 if y < 40 else y + 1900
    return y


def parse_date_from_text(text: str) -> Tuple[Optional[datetime], str]:
    """Extract the best date from free-form waypoint text.

    Returns
    -------
    (datetime_utc | None, precision)
        precision is one of: 'exact', 'day', 'month', 'year', 'none'
    """
    if not text:
        return None, 'none'

    for pattern, kind, precision in _DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        try:
            if kind == 'datetime':
                month, day, year = int(m.group(1)), int(m.group(2)), _expand_two_digit_year(int(m.group(3)))
                hour, minute = int(m.group(4)), int(m.group(5))
                return datetime(year, month, day, hour, minute, tzinfo=timezone.utc), precision
            elif kind == 'date':
                month, day, year = int(m.group(1)), int(m.group(2)), _expand_two_digit_year(int(m.group(3)))
                return datetime(year, month, day, tzinfo=timezone.utc), precision
            elif kind == 'iso_date':
                year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
                return datetime(year, month, day, tzinfo=timezone.utc), precision
            elif kind == 'long_date':
                month = _MONTH_NAMES[m.group(1).lower()]
                day, year = int(m.group(2)), int(m.group(3))
                return datetime(year, month, day, tzinfo=timezone.utc), precision
            elif kind == 'month_year':
                month = _MONTH_NAMES[m.group(1).lower()]
                year = int(m.group(2))
                return datetime(year, month, 1, tzinfo=timezone.utc), precision
            elif kind == 'year_only':
                year = int(m.group(1))
                return datetime(year, 1, 1, tzinfo=timezone.utc), precision
        except (ValueError, KeyError):
            continue

    return None, 'none'


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
    date_precision: str = "none"  # 'exact' | 'day' | 'month' | 'year' | 'none'

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

        # Determine date precision from source
        if timestamp is not None:
            date_precision = "exact"
        else:
            # Attempt to extract a date from the name/description text
            text_for_date = " ".join(filter(None, [name, description]))
            parsed_dt, date_precision = parse_date_from_text(text_for_date)
            if parsed_dt is not None:
                timestamp = parsed_dt

        return cls(
            lat=lat,
            lon=lon,
            elevation_m=elevation,
            time_utc=timestamp,
            name=name,
            description=description,
            symbol=symbol,
            date_precision=date_precision,
        )


# ── Track records ────────────────────────────────────────────────────────

class TrackType(str, Enum):
    """Classification for imported GPX tracks."""
    ACCESS = "access"
    SCOUTING_WALK = "scouting_walk"
    DEER_ROUTE_OBSERVATION = "deer_route_observation"
    UNKNOWN = "unknown"


_TRACK_TYPE_KEYWORDS: List[Tuple[TrackType, Tuple[str, ...]]] = [
    (TrackType.ACCESS, ("walk in", "walk-in", "walkin", "access", "route in",
                        "route out", "approach", "parking", "truck", "atv")),
    (TrackType.SCOUTING_WALK, ("scout", "scouting", "recon", "explore",
                               "check", "hang camera", "set cam")),
    (TrackType.DEER_ROUTE_OBSERVATION, ("deer trail", "deer route", "game trail",
                                       "buck trail", "doe trail", "track deer",
                                       "follow deer", "blood trail")),
]


def _infer_track_type(name: str, description: Optional[str] = None) -> TrackType:
    text = " ".join(filter(None, [name, description])).lower()
    for ttype, keywords in _TRACK_TYPE_KEYWORDS:
        if any(kw in text for kw in keywords):
            return ttype
    return TrackType.UNKNOWN


@dataclass(frozen=True)
class TrackPoint:
    """A single point within a GPX track segment."""
    lat: float
    lon: float
    elevation_m: Optional[float] = None
    time_utc: Optional[datetime] = None


@dataclass(frozen=True)
class TrackRecord:
    """A GPX track with classified type and computed geometry."""
    name: str
    track_type: TrackType
    points: Tuple[TrackPoint, ...] = field(default_factory=tuple)
    total_distance_m: float = 0.0
    description: Optional[str] = None

    @property
    def is_access(self) -> bool:
        return self.track_type == TrackType.ACCESS

    @property
    def should_influence_deer_model(self) -> bool:
        return self.track_type == TrackType.DEER_ROUTE_OBSERVATION


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
    dlat, dlon = rlat2 - rlat1, rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _compute_track_distance(pts: Tuple[TrackPoint, ...]) -> float:
    d = 0.0
    for i in range(1, len(pts)):
        d += _haversine_m(pts[i - 1].lat, pts[i - 1].lon, pts[i].lat, pts[i].lon)
    return round(d, 1)


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


def load_gpx_tracks(path: Path | str) -> List[TrackRecord]:
    """Load tracks from a GPX file path."""
    gpx_path = Path(path)
    if not gpx_path.exists():
        raise FileNotFoundError(gpx_path)
    tree = ET.parse(gpx_path)
    return _tracks_from_tree(tree)


def load_gpx_tracks_from_bytes(data: bytes) -> List[TrackRecord]:
    """Load tracks from raw GPX bytes."""
    if not data:
        return []
    tree = ET.parse(BytesIO(data))
    return _tracks_from_tree(tree)


def load_kml_waypoints(path: Path | str) -> List[WaypointRecord]:
    """Load waypoints from a KML file path."""

    kml_path = Path(path)
    if not kml_path.exists():
        raise FileNotFoundError(kml_path)

    tree = ET.parse(kml_path)
    return _placemarks_from_tree(tree)


def load_kml_waypoints_from_bytes(data: bytes) -> List[WaypointRecord]:
    """Load waypoints from raw KML bytes."""

    if not data:
        return []
    tree = ET.parse(BytesIO(data))
    return _placemarks_from_tree(tree)


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

    # Adjust default confidence based on date precision
    base_confidence = 6
    if record.date_precision == "none":
        base_confidence = 4  # undated waypoints get lower confidence
    elif record.date_precision == "year":
        base_confidence = 5

    payload = {
        "lat": record.lat,
        "lon": record.lon,
        "observation_type": observation_type,
        "notes": "\n".join(notes_parts),
        "confidence": base_confidence,
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


def _tracks_from_tree(tree: ET.ElementTree) -> List[TrackRecord]:
    """Parse all ``<trk>`` elements from a GPX tree."""
    root = tree.getroot()
    ns = _detect_namespace(root)
    tracks: List[TrackRecord] = []

    for trk in root.findall(f"{ns}trk"):
        name = ""
        description = None
        for child in trk:
            tag = child.tag.split("}")[-1]
            text = (child.text or "").strip()
            if tag == "name" and text:
                name = text
            elif tag == "desc" and text:
                description = text

        points: List[TrackPoint] = []
        for seg in trk.findall(f"{ns}trkseg"):
            for trkpt in seg.findall(f"{ns}trkpt"):
                lat = float(trkpt.attrib["lat"])
                lon = float(trkpt.attrib["lon"])
                ele: Optional[float] = None
                ts: Optional[datetime] = None
                for child in trkpt:
                    tag = child.tag.split("}")[-1]
                    text = (child.text or "").strip()
                    if not text:
                        continue
                    if tag == "ele":
                        try:
                            ele = float(text)
                        except ValueError:
                            pass
                    elif tag == "time":
                        ts = _parse_iso8601(text)
                points.append(TrackPoint(lat=lat, lon=lon, elevation_m=ele, time_utc=ts))

        pts_tuple = tuple(points)
        track_type = _infer_track_type(name, description)
        tracks.append(TrackRecord(
            name=name,
            track_type=track_type,
            points=pts_tuple,
            total_distance_m=_compute_track_distance(pts_tuple),
            description=description,
        ))

    return tracks


def _placemarks_from_tree(tree: ET.ElementTree) -> List[WaypointRecord]:
    root = tree.getroot()
    namespace = _detect_namespace(root)
    placemarks: List[WaypointRecord] = []

    for placemark in root.findall(f".//{namespace}Placemark"):
        name = ""
        description = None
        timestamp = None
        coords_text = None

        for child in placemark:
            tag = child.tag.split("}")[-1]
            text = (child.text or "").strip()
            if tag == "name" and text:
                name = text
            elif tag == "description" and text:
                description = text
            elif tag == "TimeStamp":
                when = child.find(f"{namespace}when")
                if when is not None and when.text:
                    timestamp = _parse_iso8601(when.text.strip())

        point = placemark.find(f".//{namespace}Point/{namespace}coordinates")
        if point is not None and point.text:
            coords_text = point.text.strip()

        if not coords_text:
            continue

        parts = [p for p in coords_text.replace("\n", " ").split() if p]
        # Use first coordinate if multiple are present.
        lon_lat_alt = parts[0].split(",")
        if len(lon_lat_alt) < 2:
            continue

        lon = float(lon_lat_alt[0])
        lat = float(lon_lat_alt[1])
        elevation = None
        if len(lon_lat_alt) >= 3:
            try:
                elevation = float(lon_lat_alt[2])
            except ValueError:
                elevation = None

        placemarks.append(
            WaypointRecord(
                lat=lat,
                lon=lon,
                elevation_m=elevation,
                time_utc=timestamp,
                name=name,
                description=description,
                symbol=None,
            )
        )

    return placemarks


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
    "TrackRecord",
    "TrackPoint",
    "TrackType",
    "load_gpx_waypoints",
    "load_gpx_waypoints_from_bytes",
    "load_gpx_tracks",
    "load_gpx_tracks_from_bytes",
    "load_kml_waypoints",
    "canonical_observation_payload",
    "parse_date_from_text",
]
