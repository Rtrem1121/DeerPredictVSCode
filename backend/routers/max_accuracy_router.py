from __future__ import annotations

import copy
import json
import logging
import os
import re
import socket
import shutil
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from backend.max_accuracy import MaxAccuracyConfig, MaxAccuracyPipeline

logger = logging.getLogger(__name__)

JOB_RETENTION_DAYS = 7


def _parse_stale_minutes() -> int:
    raw = os.getenv("MAX_ACCURACY_STALE_MINUTES", "30")
    try:
        value = int(raw)
        if value <= 0:
            raise ValueError("must be positive")
        return value
    except ValueError:
        logger.warning(
            "Invalid MAX_ACCURACY_STALE_MINUTES=%r — defaulting to 30 minutes", raw
        )
        return 30


STALE_JOB_MINUTES = _parse_stale_minutes()


def _parse_max_workers() -> int:
    raw = os.getenv("MAX_ACCURACY_MAX_WORKERS", "2")
    try:
        value = int(raw)
        if value <= 0:
            raise ValueError("must be positive")
        return min(value, 16)
    except ValueError:
        logger.warning(
            "Invalid MAX_ACCURACY_MAX_WORKERS=%r — defaulting to 2", raw
        )
        return 2


def _parse_max_inflight() -> int:
    raw = os.getenv("MAX_ACCURACY_MAX_INFLIGHT")
    if raw is None:
        return _parse_max_workers()
    try:
        value = int(raw)
        if value <= 0:
            raise ValueError("must be positive")
        return min(value, 64)
    except ValueError:
        logger.warning(
            "Invalid MAX_ACCURACY_MAX_INFLIGHT=%r — defaulting to worker count",
            raw,
        )
        return _parse_max_workers()


# Dedicated executor for the long-running pipeline.run() call. Using
# loop.run_in_executor(None, ...) shares FastAPI's default 10-thread
# pool with every sync handler; one queued max-accuracy run there can
# starve /health checks. A small dedicated pool also gives us a real
# capacity ceiling so we can reject the (N+1)-th submission instead of
# silently queuing it indefinitely.
_MAX_ACCURACY_EXECUTOR = ThreadPoolExecutor(
    max_workers=_parse_max_workers(),
    thread_name_prefix="maxacc-worker",
)
# Track in-flight worker futures by job_id so they survive the request
# scope (without this, the only reference is the add_done_callback
# closure — fragile if the closure is dropped).
_INFLIGHT_FUTURES: Dict[str, "Future[None]"] = {}
_INFLIGHT_LOCK = threading.Lock()
_MAX_INFLIGHT = _parse_max_inflight()


max_accuracy_router = APIRouter(tags=["property-hotspots", "max-accuracy"])


class Corner(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)


class MaxAccuracyConfigOverrides(BaseModel):
    grid_spacing_m: Optional[int] = Field(None, ge=5, le=100)
    max_candidates: Optional[int] = Field(None, ge=500, le=50000)
    top_k_stands: Optional[int] = Field(None, ge=5, le=100)
    gee_sample_k: Optional[int] = Field(None, ge=0, le=2000)
    wind_offset_m: Optional[float] = Field(None, ge=10.0, le=250.0)
    behavior_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    tpi_small_m: Optional[int] = Field(None, ge=20, le=200)
    tpi_large_m: Optional[int] = Field(None, ge=60, le=600)
    min_per_quadrant: Optional[int] = Field(None, ge=0, le=20)
    enable_tiling: Optional[bool] = None
    tile_size_px: Optional[int] = Field(None, ge=256, le=8192)
    # Bedding identification thresholds
    bedding_min_shelter: Optional[float] = Field(None, ge=0.0, le=1.0)
    bedding_min_bench: Optional[float] = Field(None, ge=0.0, le=1.0)
    bedding_min_roughness: Optional[float] = Field(None, ge=0.0, le=20.0)
    bedding_slope_min: Optional[float] = Field(None, ge=0.0, le=45.0)
    bedding_slope_max: Optional[float] = Field(None, ge=0.0, le=45.0)
    bedding_min_aspect_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    bedding_proximity_weight: Optional[float] = Field(None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def tpi_scales_must_be_ordered(self) -> "MaxAccuracyConfigOverrides":
        small = self.tpi_small_m
        large = self.tpi_large_m
        if small is not None and large is not None and small >= large:
            raise ValueError(
                f"tpi_small_m ({small}) must be less than tpi_large_m ({large})"
            )
        return self

    @model_validator(mode="after")
    def bedding_slope_must_be_ordered(self) -> "MaxAccuracyConfigOverrides":
        slope_min = self.bedding_slope_min
        slope_max = self.bedding_slope_max
        if slope_min is not None and slope_max is not None and slope_min >= slope_max:
            raise ValueError(
                f"bedding_slope_min ({slope_min}) must be less than "
                f"bedding_slope_max ({slope_max})"
            )
        return self


class MaxAccuracyRequest(BaseModel):
    corners: List[Corner] = Field(..., description="Property boundary corners (lat/lon) in order")
    date_time: str = Field(..., description="ISO datetime, e.g. 2025-10-15T10:30:00Z")
    season: str = Field("rut")
    hunting_pressure: str = Field("medium")
    config: Optional[MaxAccuracyConfigOverrides] = None


class MaxAccuracyResponse(BaseModel):
    success: bool
    report: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None
    error: Optional[str] = None


def _resolve_jobs_dir() -> Path:
    base_dir = Path(__file__).resolve().parents[2]
    jobs_dir = Path(os.getenv("MAX_ACCURACY_JOBS_DIR", "data/max_accuracy_jobs"))
    if not jobs_dir.is_absolute():
        jobs_dir = base_dir / jobs_dir
    return jobs_dir


def _cleanup_old_jobs(max_age_days: int = JOB_RETENTION_DAYS) -> None:
    """Delete job directories older than *max_age_days* from both
    max_accuracy_jobs and the legacy hotspot_jobs folder."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    dirs_to_scan: list[Path] = [_resolve_jobs_dir()]

    # Also clean the legacy hotspot_jobs directory
    base_dir = Path(__file__).resolve().parents[2]
    hotspot_dir = base_dir / Path(os.getenv("HOTSPOT_JOBS_DIR", "data/hotspot_jobs"))
    if hotspot_dir.exists():
        dirs_to_scan.append(hotspot_dir)

    removed = 0
    removed_ids: list[str] = []
    for parent in dirs_to_scan:
        if not parent.is_dir():
            continue
        for child in parent.iterdir():
            if not child.is_dir():
                continue
            try:
                mtime = datetime.fromtimestamp(child.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    shutil.rmtree(child, ignore_errors=True)
                    removed += 1
                    removed_ids.append(child.name)
            except OSError:
                logger.debug("Job cleanup: failed to inspect/remove %s", child, exc_info=True)
    if removed_ids:
        with _STATUS_LOCKS_GUARD:
            for jid in removed_ids:
                _STATUS_LOCKS.pop(jid, None)
    if removed:
        logger.info("Job cleanup: removed %d job directories older than %d days", removed, max_age_days)


def run_startup_cleanup_jobs() -> None:
    """Cleanup retained jobs at service startup."""
    try:
        _cleanup_old_jobs()
    except Exception:
        logger.debug("Max-accuracy startup cleanup failed", exc_info=True)


def _build_pipeline(request: MaxAccuracyRequest) -> tuple[MaxAccuracyPipeline, list[tuple[float, float]]]:
    if len(request.corners) < 3:
        raise HTTPException(status_code=400, detail="At least 3 corners are required")

    config = MaxAccuracyConfig()
    if request.config:
        for key, value in request.config.model_dump(exclude_none=True).items():
            setattr(config, key, value)

    corners = [(c.lat, c.lon) for c in request.corners]
    return MaxAccuracyPipeline(config), corners


def _read_status(job_id: str) -> Optional[Dict[str, Any]]:
    status_path = _resolve_jobs_dir() / job_id / "status.json"
    if not status_path.exists():
        return None


_JOB_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


def _validate_job_id(job_id: str) -> None:
    if not _JOB_ID_PATTERN.fullmatch(job_id):
        raise HTTPException(status_code=400, detail="Invalid job_id format")
    try:
        return json.loads(status_path.read_text(encoding="utf-8"))
    except Exception:
        logger.debug("Failed to read status for job %s", job_id, exc_info=True)
        return None


def _is_job_stale(status: Dict[str, Any], stale_minutes: int = STALE_JOB_MINUTES) -> bool:
    if status.get("state") not in {"queued", "running"}:
        return False
    updated_at = status.get("updated_at")
    if not updated_at:
        return False
    try:
        updated = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
    except ValueError:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)
    return updated < cutoff


# One lock per job_id so concurrent writers (worker progress thread +
# any reaper) don't truncate each other's writes mid-flight.
_STATUS_LOCKS: Dict[str, threading.Lock] = {}
_STATUS_LOCKS_GUARD = threading.Lock()


def _status_lock(job_id: str) -> threading.Lock:
    with _STATUS_LOCKS_GUARD:
        lock = _STATUS_LOCKS.get(job_id)
        if lock is None:
            lock = threading.Lock()
            _STATUS_LOCKS[job_id] = lock
        return lock


def _write_status(job_id: str, status: Dict[str, Any]) -> None:
    jobs_dir = _resolve_jobs_dir()
    job_dir = jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    status_path = job_dir / "status.json"
    tmp_path = status_path.with_suffix(".json.tmp")
    payload = json.dumps(status, indent=2)
    with _status_lock(job_id):
        # Write-then-rename for atomic publish: a concurrent reader
        # never sees a partially written status.json.
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, status_path)


def _persist_report(report: Dict[str, Any], job_id: str | None = None) -> Dict[str, Any]:
    job_id = job_id or uuid.uuid4().hex
    jobs_dir = _resolve_jobs_dir()
    job_dir = jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    report_path = job_dir / "max_accuracy_report.json"
    # Deep-copy so we never mutate the caller's dict (callers may keep a
    # reference to the in-memory report and we trim terrain_candidates
    # below for on-disk persistence).
    report_payload = copy.deepcopy(report)

    # Persist only the top-N terrain candidates to prevent oversized report payloads.
    top_n = int(os.getenv("MAX_ACCURACY_REPORT_TERRAIN_TOP_N", "1000"))
    terrain_candidates = report_payload.get("terrain_candidates")
    if isinstance(terrain_candidates, list) and top_n > 0 and len(terrain_candidates) > top_n:
        report_payload["terrain_candidates_total"] = len(terrain_candidates)
        report_payload["terrain_candidates_trimmed"] = True
        report_payload["terrain_candidates"] = terrain_candidates[:top_n]

    report_payload["job_id"] = job_id
    report_payload["report_path"] = str(report_path)
    report_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    return report_payload


@max_accuracy_router.post("/property-hotspots/max-accuracy/analyze", response_model=MaxAccuracyResponse)
async def analyze_max_accuracy(request: MaxAccuracyRequest) -> MaxAccuracyResponse:
    try:
        pipeline, corners = _build_pipeline(request)
        report = pipeline.run(
            corners,
            date_time=request.date_time,
            season=request.season,
            hunting_pressure=request.hunting_pressure,
        )

        if isinstance(report, dict) and report.get("error"):
            return MaxAccuracyResponse(success=False, error=str(report.get("error")))

        report_payload = _persist_report(report)

        return MaxAccuracyResponse(success=True, report=report_payload, job_id=report_payload.get("job_id"))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("MaxAccuracy /analyze unhandled error")
        return MaxAccuracyResponse(success=False, error=str(exc))


@max_accuracy_router.post("/property-hotspots/max-accuracy/run", response_model=MaxAccuracyResponse)
async def run_max_accuracy(request: MaxAccuracyRequest) -> MaxAccuracyResponse:
    try:
        pipeline, corners = _build_pipeline(request)

        with _INFLIGHT_LOCK:
            if len(_INFLIGHT_FUTURES) >= _MAX_INFLIGHT:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        f"Max-accuracy capacity reached ({_MAX_INFLIGHT} in flight). "
                        "Try again shortly."
                    ),
                )

        job_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        _write_status(
            job_id,
            {
                "job_id": job_id,
                "state": "queued",
                "stage": "queued",
                "started_at": now,
                "updated_at": now,
                "worker_pid": os.getpid(),
                "worker_host": socket.gethostname(),
            },
        )

        def _progress(stage: str, payload: Dict[str, Any]) -> None:
            previous = _read_status(job_id) or {}
            status = {
                "job_id": job_id,
                "state": "error" if stage == "error" else ("completed" if stage == "complete" else "running"),
                "stage": stage,
                "payload": payload,
                "started_at": previous.get("started_at", now),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "worker_pid": previous.get("worker_pid", os.getpid()),
                "worker_host": previous.get("worker_host", socket.gethostname()),
            }
            _write_status(job_id, status)

        def _runner() -> None:
            try:
                report = pipeline.run(
                    corners,
                    date_time=request.date_time,
                    season=request.season,
                    hunting_pressure=request.hunting_pressure,
                    progress_callback=_progress,
                )
                if isinstance(report, dict) and report.get("error"):
                    _progress("error", {"error": str(report.get("error"))})
                    return
                report_payload = _persist_report(report, job_id=job_id)
                _progress("complete", {"report_path": report_payload.get("report_path")})
                # Housekeeping: purge old jobs after each successful run
                try:
                    _cleanup_old_jobs()
                except Exception:
                    logger.debug("Job cleanup after run failed for job %s", job_id, exc_info=True)
            except Exception as exc:
                _progress("error", {"error": str(exc)})

        future = _MAX_ACCURACY_EXECUTOR.submit(_runner)
        with _INFLIGHT_LOCK:
            _INFLIGHT_FUTURES[job_id] = future

        def _on_done(f: "Future[None]") -> None:
            with _INFLIGHT_LOCK:
                _INFLIGHT_FUTURES.pop(job_id, None)
            exc = f.exception()
            if exc is not None:
                logger.error(
                    "MaxAccuracy worker raised an unhandled exception for job %s",
                    job_id, exc_info=exc,
                )
                # Worker died before writing terminal status — record it
                # so the GET /report path doesn't have to wait for the
                # stale-job timer to expire.
                try:
                    _progress("error", {"error": f"Worker crashed: {exc}"})
                except Exception:
                    logger.debug(
                        "Failed to record terminal error for job %s", job_id,
                        exc_info=True,
                    )

        future.add_done_callback(_on_done)

        return MaxAccuracyResponse(success=True, job_id=job_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("MaxAccuracy /run unhandled error")
        return MaxAccuracyResponse(success=False, error=str(exc))


@max_accuracy_router.get("/property-hotspots/max-accuracy/report/{job_id}", response_model=MaxAccuracyResponse)
async def get_max_accuracy_report(job_id: str) -> MaxAccuracyResponse:
    try:
        _validate_job_id(job_id)
        jobs_dir = _resolve_jobs_dir()
        report_path = jobs_dir / job_id / "max_accuracy_report.json"
        if not report_path.exists():
            status = _read_status(job_id)
            if not status:
                raise HTTPException(status_code=404, detail="Report not found")

            # Report stale-ness derived from timestamp, but DO NOT persist
            # the mutation. Writing 'stale' from the read path races the
            # worker's progress writes and the worker doesn't observe it
            # to actually cancel. The stale label is purely informational.
            error_payload = (status.get("payload") or {}).get("error")
            if not error_payload and _is_job_stale(status):
                error_payload = (
                    f"Job exceeded stale threshold of {STALE_JOB_MINUTES} "
                    "minutes without completion"
                )

            return MaxAccuracyResponse(
                success=False,
                error=str(error_payload or f"Job state: {status.get('state', 'unknown')}"),
                job_id=job_id,
            )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        return MaxAccuracyResponse(success=True, report=report, job_id=job_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("MaxAccuracy /report unhandled error for job %s", job_id)
        return MaxAccuracyResponse(success=False, error=str(exc), job_id=job_id)
