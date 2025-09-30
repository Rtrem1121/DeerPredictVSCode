"""API-level tests for the scouting import endpoint."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.config_manager import get_config, reload_config
from backend.main import app
from backend.routers import scouting_router
from backend.services.scouting_service import ScoutingService

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CLIENT = TestClient(app)


def _set_import_enabled(enabled: bool) -> None:
    """Set the scouting import feature flag and refresh the service."""
    reload_config()
    config = get_config()
    config.update_config("scouting_import.enabled", enabled)
    scouting_router.scouting_service = ScoutingService()


@pytest.fixture()
def enable_import():
    previous_enabled = bool(
        get_config().get("scouting_import", {}).get("enabled", False)
    )
    _set_import_enabled(True)
    try:
        yield
    finally:
        _set_import_enabled(previous_enabled)


def test_import_endpoint_accepts_gpx_dry_run(enable_import):
    gpx_path = FIXTURES_DIR / "sample_waypoints.gpx"
    assert gpx_path.exists(), "Missing GPX fixture"

    with gpx_path.open("rb") as handle:
        response = CLIENT.post(
            "/scouting/import",
            params={"dry_run": "true"},
            files={"file": (gpx_path.name, handle, "application/gpx+xml")},
        )

    assert response.status_code == 200
    payload = response.json()

    assert payload["dry_run"] is True
    assert payload["total_waypoints"] == 3
    assert payload["imported"] >= 0
    assert payload["duplicates"] >= 0
    assert payload["imported"] + payload["duplicates"] == payload["total_waypoints"]
    assert payload["configuration"]["dedupe_radius_miles"] == pytest.approx(0.15, rel=0.01)


def test_import_endpoint_respects_feature_flag():
    _set_import_enabled(False)

    gpx_path = FIXTURES_DIR / "sample_waypoints.gpx"
    with gpx_path.open("rb") as handle:
        response = CLIENT.post(
            "/scouting/import",
            files={"file": (gpx_path.name, handle, "application/gpx+xml")},
        )

    assert response.status_code == 503
    payload = response.json()
    assert "disabled" in payload["detail"].lower()
