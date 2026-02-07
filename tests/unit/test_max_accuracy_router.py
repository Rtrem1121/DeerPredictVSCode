"""Tests for the max-accuracy router endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers.max_accuracy_router import max_accuracy_router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def jobs_dir(tmp_path: Path) -> Path:
    d = tmp_path / "max_accuracy_jobs"
    d.mkdir()
    return d


@pytest.fixture()
def client(jobs_dir: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(
        "backend.routers.max_accuracy_router._resolve_jobs_dir",
        lambda: jobs_dir,
    )
    app = FastAPI()
    app.include_router(max_accuracy_router)
    c = TestClient(app)
    c.jobs_dir = jobs_dir  # type: ignore[attr-defined]
    return c


def _default_payload(**overrides: Any) -> Dict[str, Any]:
    base = {
        "corners": [
            {"lat": 44.1, "lon": -72.6},
            {"lat": 44.1, "lon": -72.5},
            {"lat": 44.0, "lon": -72.5},
            {"lat": 44.0, "lon": -72.6},
        ],
        "date_time": "2025-10-15T10:30:00Z",
        "season": "rut",
        "hunting_pressure": "medium",
    }
    base.update(overrides)
    return base


def _fake_report(corners, **kwargs) -> Dict[str, Any]:
    return {
        "stands": [
            {"lat": 44.05, "lon": -72.55, "score": 85.2, "label": "bench_saddle"},
        ],
        "run_time_s": 1.23,
        "config_used": {},
    }


# ---------------------------------------------------------------------------
# POST /property-hotspots/max-accuracy/analyze
# ---------------------------------------------------------------------------

class TestAnalyzeEndpoint:
    @patch("backend.routers.max_accuracy_router.MaxAccuracyPipeline")
    def test_success(self, MockPipeline, client: TestClient):
        mock = MockPipeline.return_value
        mock.run.return_value = _fake_report([])

        resp = client.post("/property-hotspots/max-accuracy/analyze", json=_default_payload())
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["report"] is not None
        assert data["report"]["stands"][0]["score"] == 85.2
        assert data["job_id"] is not None

    @patch("backend.routers.max_accuracy_router.MaxAccuracyPipeline")
    def test_report_persisted_to_disk(self, MockPipeline, client: TestClient):
        mock = MockPipeline.return_value
        mock.run.return_value = _fake_report([])

        resp = client.post("/property-hotspots/max-accuracy/analyze", json=_default_payload())
        data = resp.json()
        job_id = data["job_id"]
        report_path = client.jobs_dir / job_id / "max_accuracy_report.json"  # type: ignore[attr-defined]
        assert report_path.exists()

    @patch("backend.routers.max_accuracy_router.MaxAccuracyPipeline")
    def test_pipeline_error_report(self, MockPipeline, client: TestClient):
        mock = MockPipeline.return_value
        mock.run.return_value = {"error": "DEM not found"}

        resp = client.post("/property-hotspots/max-accuracy/analyze", json=_default_payload())
        data = resp.json()
        assert data["success"] is False
        assert "DEM not found" in data["error"]

    @patch("backend.routers.max_accuracy_router.MaxAccuracyPipeline")
    def test_pipeline_exception(self, MockPipeline, client: TestClient):
        mock = MockPipeline.return_value
        mock.run.side_effect = RuntimeError("rasterio failed")

        resp = client.post("/property-hotspots/max-accuracy/analyze", json=_default_payload())
        data = resp.json()
        assert data["success"] is False
        assert "rasterio failed" in data["error"]

    def test_too_few_corners(self, client: TestClient):
        payload = _default_payload(corners=[{"lat": 44.0, "lon": -72.5}, {"lat": 44.1, "lon": -72.6}])
        with patch("backend.routers.max_accuracy_router.MaxAccuracyPipeline"):
            resp = client.post("/property-hotspots/max-accuracy/analyze", json=payload)
        data = resp.json()
        assert data["success"] is False

    def test_missing_required_fields(self, client: TestClient):
        resp = client.post("/property-hotspots/max-accuracy/analyze", json={})
        assert resp.status_code == 422

    @patch("backend.routers.max_accuracy_router.MaxAccuracyPipeline")
    def test_config_overrides_applied(self, MockPipeline, client: TestClient):
        mock = MockPipeline.return_value
        mock.run.return_value = _fake_report([])

        payload = _default_payload(config={"grid_spacing_m": 15, "top_k_stands": 20})
        resp = client.post("/property-hotspots/max-accuracy/analyze", json=payload)
        assert resp.status_code == 200
        # Pipeline constructor was called with a config object
        config_arg = MockPipeline.call_args[0][0]
        assert config_arg.grid_spacing_m == 15
        assert config_arg.top_k_stands == 20


# ---------------------------------------------------------------------------
# POST /property-hotspots/max-accuracy/run  (background job)
# ---------------------------------------------------------------------------

class TestRunEndpoint:
    @patch("backend.routers.max_accuracy_router.MaxAccuracyPipeline")
    def test_returns_job_id_immediately(self, MockPipeline, client: TestClient):
        mock = MockPipeline.return_value
        mock.run.return_value = _fake_report([])

        resp = client.post("/property-hotspots/max-accuracy/run", json=_default_payload())
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["job_id"] is not None

    @patch("backend.routers.max_accuracy_router.MaxAccuracyPipeline")
    def test_writes_status_file(self, MockPipeline, client: TestClient):
        mock = MockPipeline.return_value
        mock.run.return_value = _fake_report([])

        resp = client.post("/property-hotspots/max-accuracy/run", json=_default_payload())
        job_id = resp.json()["job_id"]
        status_path = client.jobs_dir / job_id / "status.json"  # type: ignore[attr-defined]
        assert status_path.exists()
        status = json.loads(status_path.read_text(encoding="utf-8"))
        assert status["job_id"] == job_id

    def test_too_few_corners_returns_error(self, client: TestClient):
        payload = _default_payload(corners=[{"lat": 44.0, "lon": -72.5}])
        with patch("backend.routers.max_accuracy_router.MaxAccuracyPipeline"):
            resp = client.post("/property-hotspots/max-accuracy/run", json=payload)
        data = resp.json()
        assert data["success"] is False


# ---------------------------------------------------------------------------
# GET /property-hotspots/max-accuracy/report/{job_id}
# ---------------------------------------------------------------------------

class TestReportEndpoint:
    def test_existing_report(self, client: TestClient):
        job_id = "test-report-001"
        report_dir = client.jobs_dir / job_id  # type: ignore[attr-defined]
        report_dir.mkdir()
        report = {"stands": [{"lat": 44.0, "lon": -72.5, "score": 90}], "job_id": job_id}
        (report_dir / "max_accuracy_report.json").write_text(
            json.dumps(report), encoding="utf-8"
        )

        resp = client.get(f"/property-hotspots/max-accuracy/report/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["report"]["stands"][0]["score"] == 90

    def test_missing_report_returns_error(self, client: TestClient):
        resp = client.get("/property-hotspots/max-accuracy/report/nonexistent")
        data = resp.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower() or "Report not found" in data["error"]
