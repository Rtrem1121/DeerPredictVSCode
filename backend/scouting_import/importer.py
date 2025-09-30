"""Scouting data import pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from backend.scouting_data_manager import (
    ScoutingDataManager,
    get_scouting_data_manager,
)
from backend.scouting_models import ObservationType, ScoutingObservation, ScoutingQuery

from .contracts import (
    WaypointRecord,
    canonical_observation_payload,
    load_gpx_waypoints,
    load_gpx_waypoints_from_bytes,
)


@dataclass
class ImportSummary:
    """Summary of a scouting import operation."""

    total_waypoints: int
    imported: int
    duplicates: int
    errors: List[str]
    dry_run: bool
    source: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "total_waypoints": self.total_waypoints,
            "imported": self.imported,
            "duplicates": self.duplicates,
            "errors": self.errors,
            "dry_run": self.dry_run,
            "source": self.source,
        }


class ScoutingImporter:
    """Import scouting observations from historical data sources."""

    def __init__(
        self,
        data_manager: Optional[ScoutingDataManager] = None,
    *,
    dedupe_radius_miles: float = 0.15,
    dedupe_time_days: int = 365,
    dedupe_time_window_hours: int = 48,
    ) -> None:
        self._data_manager = data_manager or get_scouting_data_manager()
        self.dedupe_radius_miles = dedupe_radius_miles
        self.dedupe_time_days = dedupe_time_days
        self.dedupe_time_window_hours = dedupe_time_window_hours

    # Public API -----------------------------------------------------------------

    def import_gpx_file(self, path: str | Path, *, dry_run: bool = False) -> ImportSummary:
        records = load_gpx_waypoints(path)
        return self.import_records(records, dry_run=dry_run, source=str(path))

    def import_gpx_bytes(
        self,
        data: bytes,
        *,
        filename: Optional[str] = None,
        dry_run: bool = False,
    ) -> ImportSummary:
        records = load_gpx_waypoints_from_bytes(data)
        return self.import_records(records, dry_run=dry_run, source=filename)

    def import_records(
        self,
        records: Iterable[WaypointRecord],
        *,
        dry_run: bool = False,
        source: Optional[str] = None,
    ) -> ImportSummary:
        summary = ImportSummary(
            total_waypoints=0,
            imported=0,
            duplicates=0,
            errors=[],
            dry_run=dry_run,
            source=source,
        )

        for record in records:
            summary.total_waypoints += 1
            try:
                payload = canonical_observation_payload(record)
                observation = ScoutingObservation(**payload)

                if self._is_duplicate(observation):
                    summary.duplicates += 1
                    continue

                if not dry_run:
                    self._data_manager.add_observation(observation)

                summary.imported += 1
            except Exception as exc:  # pragma: no cover - defensive
                summary.errors.append(f"{record.name or 'waypoint'}: {exc}")

        return summary

    # Internal helpers -----------------------------------------------------------

    def _is_duplicate(self, observation: ScoutingObservation) -> bool:
        query = ScoutingQuery(
            lat=observation.lat,
            lon=observation.lon,
            radius_miles=self.dedupe_radius_miles,
            observation_types=[observation.observation_type],
            days_back=self.dedupe_time_days,
        )

        existing = self._data_manager.get_observations(query)
        time_window = timedelta(hours=self.dedupe_time_window_hours)

        for existing_obs in existing:
            if existing_obs.observation_type != observation.observation_type:
                continue

            if self._time_difference(existing_obs.timestamp, observation.timestamp) > time_window:
                continue

            if self._notes_match(existing_obs, observation):
                return True

        return False

    @staticmethod
    def _time_difference(first: datetime, second: datetime) -> timedelta:
        first_dt = ScoutingImporter._as_utc(first)
        second_dt = ScoutingImporter._as_utc(second)
        return abs(first_dt - second_dt)

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _notes_match(existing: ScoutingObservation, new_observation: ScoutingObservation) -> bool:
        existing_notes = (existing.notes or "").strip().lower()
        new_notes = (new_observation.notes or "").strip().lower()
        return existing_notes == new_notes or not new_notes


__all__ = ["ImportSummary", "ScoutingImporter"]
