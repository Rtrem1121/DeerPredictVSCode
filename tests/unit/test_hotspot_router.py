"""Comprehensive tests for the hotspot router endpoints."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers.hotspot_router import hotspot_router


# ---------------------------------------------------------------------------
# Fake service
# ---------------------------------------------------------------------------

@dataclass
class _FakeJob:
    job_id: str
    status: str
    created_at: str
    updated_at: str
    total: int
    completed: int
    message: str
    error: Optional[str] = None
    report_path: Optional[str] = None
    map_path: Optional[str] = None


class _FakeHotspotService:
    """Deterministic (no I/O) stand-in for HotspotJobService."""

    def __init__(self, tmp_path: Path) -> None:
        self._jobs: Dict[str, _FakeJob] = {}
        self._tmp = tmp_path
        self.last_mode: Optional[str] = None
        self.last_kwargs: Dict[str, Any] = {}

    def create_job(self, total: int, message: str) -> _FakeJob:
        job = _FakeJob(
            job_id="fake-job-001",
            status="queued",
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
            total=total,
            completed=0,
            message=message,
        )
        self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[_FakeJob]:
        return self._jobs.get(job_id)

    async def run_job(self, job_id: str, *, mode: str, **kwargs: Any) -> None:
        self.last_mode = mode
        self.last_kwargs = kwargs
        job = self._jobs[job_id]

        # Build a realistic-looking report
        report = {
            "job_id": job_id,
            "inputs": {"mode": mode, **{k: str(v) for k, v in kwargs.items()}},
            "best_stand_site": {"lat": 44.05, "lon": -72.55},
            "clusters": [],
            "stand_points_count": 5,
        }
        report_path = self._tmp / job_id / "hotspot_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        map_html = "<html><body><h3>Map stub</h3></body></html>"
        map_path = self._tmp / job_id / "hotspot_map.html"
        map_path.write_text(map_html, encoding="utf-8")

        job.status = "completed"
        job.report_path = str(report_path)
        job.map_path = str(map_path)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_service(tmp_path: Path) -> _FakeHotspotService:
    return _FakeHotspotService(tmp_path)


@pytest.fixture()
def client(fake_service: _FakeHotspotService, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(
        "backend.routers.hotspot_router.get_hotspot_job_service",
        lambda: fake_service,
    )
    app = FastAPI()
    app.include_router(hotspot_router)
    c = TestClient(app)
    c.fake = fake_service  # type: ignore[attr-defined]
    return c


def _default_payload(**overrides: Any) -> Dict[str, Any]:
    base = {
        "corners": [
            {"lat": 44.1, "lon": -72.6},
            {"lat": 44.1, "lon": -72.5},
            {"lat": 44.0, "lon": -72.5},
            {"lat": 44.0, "lon": -72.6},
        ],
        "mode": "lidar_first",
        "num_sample_points": 15,
        "lidar_grid_points": 5000,
        "lidar_top_k": 10,
        "lidar_sample_radius_m": 30,
        "epsilon_meters": 75,
        "min_samples": 2,
        "date_time": "2025-10-15T10:30:00Z",
        "season": "rut",
        "hunting_pressure": "high",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# POST /property-hotspots/run
# ---------------------------------------------------------------------------

class TestRunEndpoint:
    def test_success(self, client: TestClient):
        resp = client.post("/property-hotspots/run", json=_default_payload())
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["job_id"] == "fake-job-001"

    def test_forces_lidar_first_regardless_of_mode(self, client: TestClient):
        """Router should override mode to lidar_first."""
        resp = client.post("/property-hotspots/run", json=_default_payload(mode="sample_predict"))
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        # Job total should be lidar_top_k, not num_sample_points
        assert client.fake._jobs["fake-job-001"].total == 10  # type: ignore[attr-defined]

    def test_missing_required_fields(self, client: TestClient):
        """Request without required fields should fail validation."""
        resp = client.post("/property-hotspots/run", json={"corners": []})
        assert resp.status_code == 422

    def test_invalid_corner_types(self, client: TestClient):
        payload = _default_payload()
        payload["corners"] = [{"lat": "not_a_number", "lon": -72.5}]
        resp = client.post("/property-hotspots/run", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /property-hotspots/analyze
# ---------------------------------------------------------------------------

class TestAnalyzeEndpoint:
    def test_success_returns_report(self, client: TestClient):
        resp = client.post("/property-hotspots/analyze", json=_default_payload())
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["report"] is not None
        assert data["report"]["job_id"] == "fake-job-001"
        assert data["report"]["best_stand_site"]["lat"] == 44.05

    def test_mode_is_lidar_first(self, client: TestClient):
        resp = client.post("/property-hotspots/analyze", json=_default_payload())
        data = resp.json()
        assert data["report"]["inputs"]["mode"] == "lidar_first"
        assert client.fake.last_mode == "lidar_first"  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# GET /property-hotspots/status/{job_id}
# ---------------------------------------------------------------------------

class TestStatusEndpoint:
    def test_existing_job(self, client: TestClient, fake_service: _FakeHotspotService):
        fake_service.create_job(total=5, message="testing")
        resp = client.get("/property-hotspots/status/fake-job-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["job"]["job_id"] == "fake-job-001"
        assert data["job"]["status"] == "queued"

    def test_missing_job_returns_404(self, client: TestClient):
        resp = client.get("/property-hotspots/status/nonexistent-id")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /property-hotspots/report/{job_id}
# ---------------------------------------------------------------------------

class TestReportEndpoint:
    def test_completed_job_returns_report(self, client: TestClient):
        # Run analyze to create a completed job with report
        client.post("/property-hotspots/analyze", json=_default_payload())
        resp = client.get("/property-hotspots/report/fake-job-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == "fake-job-001"

    def test_missing_job_returns_404(self, client: TestClient):
        resp = client.get("/property-hotspots/report/nonexistent-id")
        assert resp.status_code == 404

    def test_job_without_report_returns_409(self, client: TestClient, fake_service: _FakeHotspotService):
        fake_service.create_job(total=5, message="no report yet")
        resp = client.get("/property-hotspots/report/fake-job-001")
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# GET /property-hotspots/map/{job_id}
# ---------------------------------------------------------------------------

class TestMapEndpoint:
    def test_completed_job_returns_html(self, client: TestClient):
        client.post("/property-hotspots/analyze", json=_default_payload())
        resp = client.get("/property-hotspots/map/fake-job-001")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Map stub" in resp.text

    def test_missing_job_returns_404(self, client: TestClient):
        resp = client.get("/property-hotspots/map/nonexistent-id")
        assert resp.status_code == 404

    def test_job_without_map_returns_409(self, client: TestClient, fake_service: _FakeHotspotService):
        fake_service.create_job(total=5, message="no map yet")
        resp = client.get("/property-hotspots/map/fake-job-001")
        assert resp.status_code == 409
