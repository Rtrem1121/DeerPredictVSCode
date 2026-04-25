"""Mature buck detection event model.

First-class record for individual trail-camera or manual detection events.
Each event captures a single observation of a buck at a specific time and
place, with structured fields for maturity, behavior, and confidence.
"""

from __future__ import annotations

from datetime import datetime, timezone, date
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class BuckClass(str, Enum):
    """Antler classification for observed bucks."""
    SPIKE = "spike"
    FOUR_POINTER = "4-pointer"
    SIX_POINTER = "6-pointer"
    EIGHT_POINTER = "8-pointer"
    TEN_POINTER = "10-pointer"
    UNKNOWN_MATURE = "unknown_mature"
    UNKNOWN = "unknown"


class EventSource(str, Enum):
    """Where the detection event originated."""
    MOULTRIE = "moultrie"
    BUSHNELL = "bushnell"
    STEALTH_CAM = "stealth_cam"
    RECONYX = "reconyx"
    MANUAL = "manual"
    OTHER = "other"


class MovementType(str, Enum):
    """Observed movement behaviour at the detection point."""
    CROSSING = "crossing"
    TRAIL = "trail"
    SCRAPE_CHECK = "scrape_check"
    BEDDING_EDGE = "bedding_edge"
    FEEDING = "feeding"
    CRUISING = "cruising"
    UNKNOWN = "unknown"


def _is_daylight(ts: datetime) -> bool:
    """Approximate daylight check using civil-twilight estimation.

    Uses a simple solar-noon heuristic for the latitude band
    42–45°N (Vermont). Accurate to roughly ±20 minutes which is
    fine for a boolean flag; proper ephemeris calculation can replace
    this later if needed.
    """
    # Approximate sunrise/sunset offsets by month for ~44°N
    # (hours before/after solar noon ~12:15 local)
    _offsets_by_month = {
        1: 4.5, 2: 5.0, 3: 5.8, 4: 6.5, 5: 7.0, 6: 7.5,
        7: 7.3, 8: 6.7, 9: 5.8, 10: 5.0, 11: 4.5, 12: 4.3,
    }
    # Convert to US/Eastern naive hour for comparison.
    # DST in the US is approximately Mar 8 – Nov 1 (second Sunday of
    # March to first Sunday of November).  Using fixed dates is accurate
    # to within a week at the boundaries, which is sufficient for a
    # binary daylight flag.
    utc_hour = ts.hour + ts.minute / 60.0
    dst = (
        4 if (ts.month > 3 and ts.month < 11)
        or (ts.month == 3 and ts.day >= 8)
        or (ts.month == 11 and ts.day <= 1)
        else 5
    )
    local_hour = (utc_hour - dst) % 24

    half_day = _offsets_by_month.get(ts.month, 6.0)
    solar_noon = 12.25  # ~12:15 for Vermont longitude
    sunrise = solar_noon - half_day
    sunset = solar_noon + half_day
    # Civil twilight buffer: 30 minutes
    return (sunrise - 0.5) <= local_hour <= (sunset + 0.5)


class BuckEvent(BaseModel):
    """A single mature-buck detection event.

    This is the atomic unit of camera/manual observation data.  Multiple
    events at the same location form the basis for evidence clusters.
    """

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    timestamp: datetime = Field(...)
    source: EventSource = Field(default=EventSource.MANUAL)
    buck_class: BuckClass = Field(default=BuckClass.UNKNOWN)
    buck_id: Optional[str] = Field(
        None, description="Optional label for a specific buck, e.g. 'creek-8pt'"
    )
    target_buck: bool = Field(default=False)
    daylight: Optional[bool] = Field(
        None, description="Auto-computed from timestamp if not set"
    )
    movement_type: MovementType = Field(default=MovementType.UNKNOWN)
    repeat_location: bool = Field(default=False)
    confidence: int = Field(default=7, ge=1, le=10)
    notes: Optional[str] = Field(None)

    @field_validator("timestamp", mode="before")
    def ensure_utc(cls, v):
        if isinstance(v, str):
            v = v.replace("Z", "+00:00")
            v = datetime.fromisoformat(v)
        if isinstance(v, datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            else:
                v = v.astimezone(timezone.utc)
            return v
        raise ValueError("timestamp must be a datetime or ISO string")

    def model_post_init(self, __context) -> None:
        if self.daylight is None:
            object.__setattr__(
                self, "daylight", _is_daylight(self.timestamp)
            )

    # -- Maturity helpers --------------------------------------------------

    @property
    def is_mature(self) -> bool:
        return self.buck_class in {
            BuckClass.EIGHT_POINTER,
            BuckClass.TEN_POINTER,
            BuckClass.UNKNOWN_MATURE,
        }

    @property
    def maturity_weight(self) -> float:
        """Multiplier for evidence weighting based on buck maturity."""
        _weights = {
            BuckClass.SPIKE: 0.3,
            BuckClass.FOUR_POINTER: 0.5,
            BuckClass.SIX_POINTER: 0.8,
            BuckClass.EIGHT_POINTER: 1.2,
            BuckClass.TEN_POINTER: 1.3,
            BuckClass.UNKNOWN_MATURE: 1.1,
            BuckClass.UNKNOWN: 0.6,
        }
        base = _weights.get(self.buck_class, 0.6)
        if self.target_buck:
            base *= 1.25
        if self.repeat_location:
            base *= 1.15
        return round(min(base, 2.0), 3)

    # -- Serialisation -----------------------------------------------------

    def to_dict(self) -> dict:
        data = self.model_dump()
        data["timestamp"] = self.timestamp.isoformat()
        data["source"] = self.source.value
        data["buck_class"] = self.buck_class.value
        data["movement_type"] = self.movement_type.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "BuckEvent":
        return cls(**data)
