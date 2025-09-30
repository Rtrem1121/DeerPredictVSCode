"""Phase 1 contract tests for historical scouting data imports."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from backend.scouting_import import (
    WaypointRecord,
    canonical_observation_payload,
    load_gpx_waypoints,
)
from backend.scouting_models import ObservationType, ScoutingObservation

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> Path:
    path = FIXTURES_DIR / name
    assert path.exists(), f"Missing fixture: {name}"
    return path


def test_sample_json_matches_observation_schema():
    data = json.loads(_load_fixture("sample_scouting_observations.json").read_text())
    observations = data.get("observations", [])
    assert observations, "Fixture should contain at least one observation"

    for idx, raw_obs in enumerate(observations):
        obs = ScoutingObservation(**raw_obs)
        assert obs.lat == pytest.approx(raw_obs["lat"]), f"Latitude mismatch at #{idx}"
        assert obs.lon == pytest.approx(raw_obs["lon"]), f"Longitude mismatch at #{idx}"
        assert 1 <= obs.confidence <= 10
        assert isinstance(obs.timestamp, datetime)


def test_gpx_waypoints_parse_into_records():
    waypoints = load_gpx_waypoints(_load_fixture("sample_waypoints.gpx"))
    assert len(waypoints) == 3

    first = waypoints[0]
    assert isinstance(first, WaypointRecord)
    assert first.elevation_m == pytest.approx(444.0)
    assert first.time_utc.tzinfo is not None, "Timestamp should be timezone-aware"
    assert "rub" in first.name.lower()


def test_canonical_payload_produces_valid_observations():
    waypoints = load_gpx_waypoints(_load_fixture("sample_waypoints.gpx"))

    expected_types = {
        0: ObservationType.RUB_LINE,
        1: ObservationType.BEDDING_AREA,
        2: ObservationType.DEER_TRACKS,
    }

    for idx, record in enumerate(waypoints):
        payload = canonical_observation_payload(record)
        obs = ScoutingObservation(**payload)

        assert obs.observation_type == expected_types[idx]
        assert obs.timestamp.tzinfo is not None
        assert obs.confidence == 6
        assert not obs.photo_urls

        # Ensure nested detail models exist when expected
        if obs.observation_type == ObservationType.RUB_LINE:
            assert obs.rub_details is not None
            assert obs.rub_details.multiple_rubs is True
        if obs.observation_type == ObservationType.BEDDING_AREA:
            assert obs.bedding_details is not None
            assert obs.bedding_details.number_of_beds >= 1
        if obs.observation_type == ObservationType.DEER_TRACKS:
            assert obs.tracks_details is not None
            assert obs.tracks_details.track_depth in {"Medium", "Shallow", "Deep", "Very Deep"}
