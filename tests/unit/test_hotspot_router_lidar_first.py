"""Tests for enforcing LiDAR-first property scans."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers.hotspot_router import hotspot_router


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
    def __init__(self, report_path: Path) -> None:
        self._job = _FakeJob(
            job_id="job-123",
            status="queued",
            created_at="now",
            updated_at="now",
            total=1,
            completed=0,
            message="queued",
        )
        self._report_path = report_path
        self.last_mode: Optional[str] = None

    def create_job(self, total: int, message: str) -> _FakeJob:
        self._job.total = total
        self._job.message = message
        return self._job

    def get_job(self, job_id: str) -> Optional[_FakeJob]:
        if job_id != self._job.job_id:
            return None
        return self._job

    async def run_job(self, job_id: str, *, mode: str, **kwargs: Any) -> None:
        self.last_mode = mode
        report = {
            "job_id": job_id,
            "inputs": {"mode": mode},
            "best_stand_site": {"lat": 44.0, "lon": -72.5},
        }
        self._report_path.write_text(json.dumps(report), encoding="utf-8")
        self._job.report_path = str(self._report_path)
        self._job.status = "completed"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    report_path = tmp_path / "hotspot_report.json"
    fake_service = _FakeHotspotService(report_path)

    def _get_service() -> _FakeHotspotService:
        return fake_service

    monkeypatch.setattr(
        "backend.routers.hotspot_router.get_hotspot_job_service",
        _get_service,
    )

    app = FastAPI()
    app.include_router(hotspot_router)
    client = TestClient(app)
    client.hotspot_service = fake_service
    return client


def _payload() -> Dict[str, Any]:
    return {
        "corners": [
            {"lat": 44.1, "lon": -72.6},
            {"lat": 44.1, "lon": -72.5},
            {"lat": 44.0, "lon": -72.5},
            {"lat": 44.0, "lon": -72.6},
        ],
        "mode": "sample_predict",
        "num_sample_points": 15,
        "lidar_grid_points": 5000,
        "lidar_top_k": 5,
        "lidar_sample_radius_m": 15,
        "epsilon_meters": 75,
        "min_samples": 2,
        "date_time": "2025-10-15T10:30:00Z",
        "season": "rut",
        "hunting_pressure": "high",
    }


def test_run_endpoint_forces_lidar_first(client: TestClient):
    payload = _payload()
    response = client.post("/property-hotspots/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    assert client.hotspot_service._job.total == payload["lidar_top_k"]


def test_analyze_endpoint_runs_lidar_first(client: TestClient):
    payload = _payload()
    response = client.post("/property-hotspots/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    assert data.get("report")
    assert data["report"]["inputs"]["mode"] == "lidar_first"
    assert client.hotspot_service.last_mode == "lidar_first"
