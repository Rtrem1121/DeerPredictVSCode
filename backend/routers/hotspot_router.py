from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from backend.services.hotspot_job_service import get_hotspot_job_service


hotspot_router = APIRouter(tags=["property-hotspots"])


class Corner(BaseModel):
    lat: float
    lon: float


class RunHotspotRequest(BaseModel):
    corners: List[Corner] = Field(..., description="Property boundary corners (lat/lon) in order")
    mode: str = Field(
        "lidar_first",
        description="Hotspot job mode. 'lidar_first' does LiDAR shortlisting then runs full predictions on top K. 'sample_predict' runs full predictions on random samples.",
    )

    # sample_predict params
    num_sample_points: int = Field(25, ge=5, le=500)

    # lidar_first params
    lidar_grid_points: int = Field(120000, ge=5000, le=200000)
    lidar_top_k: int = Field(30, ge=5, le=50)
    lidar_sample_radius_m: int = Field(30, ge=5, le=120)

    epsilon_meters: float = Field(75.0, ge=10.0, le=500.0)
    min_samples: int = Field(2, ge=2, le=20)

    date_time: str = Field(..., description="ISO datetime, e.g. 2025-10-15T10:30:00Z")
    season: str = Field("fall")
    hunting_pressure: str = Field("high")


class RunHotspotResponse(BaseModel):
    success: bool
    job_id: Optional[str] = None
    error: Optional[str] = None


class RunHotspotReportResponse(BaseModel):
    success: bool
    report: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None
    error: Optional[str] = None


class JobStatusResponse(BaseModel):
    success: bool
    job: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@hotspot_router.post("/property-hotspots/run", response_model=RunHotspotResponse)
async def run_property_hotspots(request: RunHotspotRequest) -> RunHotspotResponse:
    try:
        service = get_hotspot_job_service()
        corners = [(c.lat, c.lon) for c in request.corners]

        # Enforce LiDAR-first pipeline for property scans
        mode = "lidar_first"

        total = request.num_sample_points if mode == "sample_predict" else request.lidar_top_k
        job = service.create_job(total=total, message="Queued")

        # Run in a background thread so the FastAPI event loop stays responsive.
        import asyncio

        def _runner() -> None:
            asyncio.run(
                service.run_job(
                    job.job_id,
                    corners=corners,
                    mode=mode,
                    num_sample_points=request.num_sample_points,
                    lidar_grid_points=request.lidar_grid_points,
                    lidar_top_k=request.lidar_top_k,
                    lidar_sample_radius_m=request.lidar_sample_radius_m,
                    epsilon_meters=request.epsilon_meters,
                    min_samples=request.min_samples,
                    date_time=request.date_time,
                    season=request.season,
                    hunting_pressure=request.hunting_pressure,
                )
            )

        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, _runner)

        return RunHotspotResponse(success=True, job_id=job.job_id)
    except Exception as e:
        return RunHotspotResponse(success=False, error=str(e))


@hotspot_router.post("/property-hotspots/analyze", response_model=RunHotspotReportResponse)
async def analyze_property_hotspots(request: RunHotspotRequest) -> RunHotspotReportResponse:
    """Run a LiDAR-first property scan and return the report in the response."""
    try:
        service = get_hotspot_job_service()
        corners = [(c.lat, c.lon) for c in request.corners]

        mode = "lidar_first"
        total = request.num_sample_points if mode == "sample_predict" else request.lidar_top_k
        job = service.create_job(total=total, message="Queued")

        await service.run_job(
            job.job_id,
            corners=corners,
            mode=mode,
            num_sample_points=request.num_sample_points,
            lidar_grid_points=request.lidar_grid_points,
            lidar_top_k=request.lidar_top_k,
            lidar_sample_radius_m=request.lidar_sample_radius_m,
            epsilon_meters=request.epsilon_meters,
            min_samples=request.min_samples,
            date_time=request.date_time,
            season=request.season,
            hunting_pressure=request.hunting_pressure,
        )

        job = service.get_job(job.job_id)
        if not job or not job.report_path:
            return RunHotspotReportResponse(success=False, error="Report not available", job_id=job.job_id)

        path = Path(job.report_path)
        if not path.exists():
            return RunHotspotReportResponse(success=False, error="Report file missing", job_id=job.job_id)

        report = json.loads(path.read_text(encoding="utf-8"))
        return RunHotspotReportResponse(success=True, report=report, job_id=job.job_id)
    except Exception as e:
        return RunHotspotReportResponse(success=False, error=str(e))


@hotspot_router.get("/property-hotspots/status/{job_id}", response_model=JobStatusResponse)
async def get_hotspot_status(job_id: str) -> JobStatusResponse:
    service = get_hotspot_job_service()
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(success=True, job=job.__dict__)


@hotspot_router.get("/property-hotspots/report/{job_id}")
async def get_hotspot_report(job_id: str) -> Dict[str, Any]:
    service = get_hotspot_job_service()
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.report_path:
        raise HTTPException(status_code=409, detail="Report not available yet")

    path = Path(job.report_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file missing")

    return json.loads(path.read_text(encoding="utf-8"))


@hotspot_router.get("/property-hotspots/map/{job_id}")
async def get_hotspot_map(job_id: str) -> HTMLResponse:
    service = get_hotspot_job_service()
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.map_path:
        raise HTTPException(status_code=409, detail="Map not available yet")

    path = Path(job.map_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Map file missing")

    return HTMLResponse(content=path.read_text(encoding="utf-8"))
