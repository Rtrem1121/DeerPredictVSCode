"""HotspotJob lifecycle management and orchestration.

This module owns the HotspotJob dataclass and HotspotJobService class.
All heavy-lifting (polygon sampling, LiDAR scoring, clustering, map rendering)
is delegated to sibling modules under ``backend.services.hotspot``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    """Return current UTC time as an ISO-8601 string ending in 'Z'.

    Wraps timezone-aware datetime.now() and replaces the offset with 'Z'
    for consistent on-disk format. Avoids deprecated datetime.utcnow().
    """
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

from backend.services.hotspot.clustering import (
    best_site_score_0_200,
    cluster_stands,
    extract_stand_points,
)
from backend.services.hotspot.lidar_scoring import lidar_shortlist_points
from backend.services.hotspot.map_builder import build_map_html
from backend.services.hotspot.polygon import (
    generate_grid_points_in_polygon,
    sample_points_in_polygon,
    stable_seed_from_corners,
)


def _parse_dt_to_eastern(date_time: str) -> datetime:
    dt = datetime.fromisoformat(date_time.replace("Z", "+00:00"))
    eastern = ZoneInfo("America/New_York")
    return dt.astimezone(eastern) if dt.tzinfo else dt.replace(tzinfo=eastern)


@dataclass
class HotspotJob:
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


class HotspotJobService:
    def __init__(self) -> None:
        self._jobs: Dict[str, HotspotJob] = {}
        self._lock = threading.Lock()

    def _job_state_path(self, job_id: str) -> Path:
        jobs_dir = Path(os.getenv("HOTSPOT_JOBS_DIR", "/app/data/hotspot_jobs"))
        return jobs_dir / job_id / "job_state.json"

    def _persist_job_state(self, job: HotspotJob) -> None:
        try:
            state_path = self._job_state_path(job.job_id)
            state_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "job_id": job.job_id,
                "status": job.status,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "total": job.total,
                "completed": job.completed,
                "message": job.message,
                "error": job.error,
                "report_path": job.report_path,
                "map_path": job.map_path,
            }
            state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            return

    def _recover_job_from_disk(self, job_id: str) -> Optional[HotspotJob]:
        jobs_dir = Path(os.getenv("HOTSPOT_JOBS_DIR", "/app/data/hotspot_jobs"))
        job_dir = jobs_dir / job_id
        if not job_dir.exists():
            return None

        state_path = job_dir / "job_state.json"
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
                status = state.get("status") or "unknown"
                report_path = state.get("report_path")
                map_path = state.get("map_path")
                if status != "completed" and not report_path:
                    status = "interrupted"
                return HotspotJob(
                    job_id=job_id,
                    status=status,
                    created_at=state.get("created_at") or _utc_now_iso(),
                    updated_at=state.get("updated_at") or _utc_now_iso(),
                    total=int(state.get("total") or 0),
                    completed=int(state.get("completed") or 0),
                    message=state.get("message") or "Recovered from disk",
                    error=state.get("error"),
                    report_path=report_path,
                    map_path=map_path,
                )
            except Exception:
                logger.debug("Failed to recover hotspot job state from %s", state_path, exc_info=True)

        report_path_f = job_dir / "hotspot_report.json"
        map_path_f = job_dir / "hotspot_map.html"
        if not report_path_f.exists() and not map_path_f.exists():
            return None

        now = _utc_now_iso()
        status = "completed" if report_path_f.exists() else "unknown"
        job = HotspotJob(
            job_id=job_id,
            status=status,
            created_at=now,
            updated_at=now,
            total=0,
            completed=0,
            message="Recovered from disk",
            report_path=str(report_path_f) if report_path_f.exists() else None,
            map_path=str(map_path_f) if map_path_f.exists() else None,
        )
        return job

    def create_job(self, total: int, message: str) -> HotspotJob:
        job_id = str(uuid.uuid4())
        now = _utc_now_iso()
        job = HotspotJob(
            job_id=job_id,
            status="queued",
            created_at=now,
            updated_at=now,
            total=total,
            completed=0,
            message=message,
        )
        with self._lock:
            self._jobs[job_id] = job
        self._persist_job_state(job)
        return job

    def get_job(self, job_id: str) -> Optional[HotspotJob]:
        with self._lock:
            job = self._jobs.get(job_id)
        if job:
            return job

        recovered = self._recover_job_from_disk(job_id)
        if recovered:
            with self._lock:
                self._jobs[job_id] = recovered
            return recovered
        return None

    def update_job(self, job_id: str, **kwargs) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for k, v in kwargs.items():
                if hasattr(job, k):
                    setattr(job, k, v)
            job.updated_at = _utc_now_iso()
        self._persist_job_state(job)

    async def run_job(
        self,
        job_id: str,
        *,
        corners: List[Tuple[float, float]],
        mode: str,
        num_sample_points: int,
        lidar_grid_points: int,
        lidar_top_k: int,
        lidar_sample_radius_m: int,
        epsilon_meters: float,
        min_samples: int,
        date_time: str,
        season: str,
        hunting_pressure: str,
    ) -> None:
        from backend.services.prediction_service import get_prediction_service

        jobs_dir = Path(os.getenv("HOTSPOT_JOBS_DIR", "/app/data/hotspot_jobs"))
        jobs_dir.mkdir(parents=True, exist_ok=True)
        job_dir = jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        self.update_job(job_id, status="running", message="Preparing hotspot run")

        effective_epsilon = epsilon_meters
        if season in ["rut", "pre_rut", "post_rut"]:
            effective_epsilon = max(float(epsilon_meters), 150.0)

        service = get_prediction_service()
        target_dt = _parse_dt_to_eastern(date_time)

        lidar_shortlist: List[Dict[str, Any]] = []
        lidar_meta: Dict[str, Any] = {}

        if mode == "lidar_first":
            self.update_job(job_id, message=f"Generating grid (~{lidar_grid_points} points)")
            grid_points = generate_grid_points_in_polygon(corners, lidar_grid_points)

            self.update_job(job_id, message=f"Scoring {len(grid_points)} points with LiDAR (local DEM)")
            lidar_shortlist, lidar_meta = lidar_shortlist_points(
                corners,
                grid_points,
                sample_radius_m=lidar_sample_radius_m,
                top_k=lidar_top_k,
            )

            if not lidar_shortlist:
                self.update_job(job_id, message="LiDAR shortlist unavailable; falling back to random sample predictions")
                mode = "sample_predict"
            else:
                total = len(lidar_shortlist)
                self.update_job(job_id, total=total, completed=0, message=f"Running full predictions for top {total} LiDAR candidates")
        else:
            self.update_job(job_id, message="Sampling points inside property")
            seed = stable_seed_from_corners(corners)
            sample_points = sample_points_in_polygon(corners, num_sample_points, seed=seed)
            total = len(sample_points)
            self.update_job(job_id, total=total, completed=0, message="Running predictions")

        all_stands: List[Dict[str, Any]] = []
        per_point_best: List[Dict[str, Any]] = []

        if mode == "lidar_first" and lidar_shortlist:
            query_points = [(r["lat"], r["lon"]) for r in lidar_shortlist]
        else:
            seed = stable_seed_from_corners(corners)
            query_points = sample_points_in_polygon(corners, num_sample_points, seed=seed)

        total = len(query_points)
        max_concurrency = int(os.getenv("HOTSPOT_PREDICTION_CONCURRENCY", "3"))
        max_concurrency = max(1, min(10, max_concurrency))
        self.update_job(job_id, message=f"Running predictions ({total} points, concurrency={max_concurrency})", completed=0, total=total)

        sem = asyncio.Semaphore(max_concurrency)

        async def _predict_one(idx: int, lat: float, lon: float) -> Tuple[int, float, float, Any]:
            async with sem:
                self.update_job(job_id, message=f"Predicting {idx}/{total}")
                return (
                    idx,
                    lat,
                    lon,
                    await asyncio.wait_for(
                        service.predict(
                            lat=lat,
                            lon=lon,
                            time_of_day=target_dt.hour,
                            season=season,
                            hunting_pressure=hunting_pressure,
                            target_datetime=target_dt,
                        ),
                        timeout=180,
                    ),
                )

        tasks = [asyncio.create_task(_predict_one(i, lat, lon)) for i, (lat, lon) in enumerate(query_points, 1)]

        done_count = 0
        for fut in asyncio.as_completed(tasks):
            try:
                idx, lat, lon, prediction = await fut
                stands = extract_stand_points(prediction)
                all_stands.extend(stands)

                if stands:
                    best = max(stands, key=lambda s: float(s.get("score", 0.0)))
                    per_point_best.append(
                        {
                            "query_lat": lat,
                            "query_lon": lon,
                            "best_lat": best["lat"],
                            "best_lon": best["lon"],
                            "best_score": best.get("score", 0.0),
                            "best_strategy": best.get("strategy"),
                        }
                    )
            except Exception as e:
                all_stands.append(
                    {
                        "lat": None,
                        "lon": None,
                        "score": 0.0,
                        "strategy": "prediction_error",
                        "source": "error",
                        "error": str(e),
                    }
                )
            finally:
                done_count += 1
                self.update_job(job_id, completed=done_count, message=f"Predictions: {done_count}/{total}")

        self.update_job(job_id, message="Clustering stand points")
        clusters = cluster_stands(all_stands, effective_epsilon, min_samples)

        best_stand_site: Optional[Dict[str, Any]] = None
        if clusters:
            top = clusters[0]
            medoid_point = top.get("medoid_point") if isinstance(top, dict) else None
            if not isinstance(medoid_point, dict):
                medoid_point = {"lat": float(top["medoid"]["lat"]), "lon": float(top["medoid"]["lon"])}
            support = int(top.get("size", 0) or 0)
            avg_score = float(top.get("avg_score", 0.0) or 0.0)
            best_stand_site = {
                "lat": float(medoid_point.get("lat")),
                "lon": float(medoid_point.get("lon")),
                "supporting_predictions": support,
                "cluster_avg_score_0_10": avg_score,
                "stand_score_0_10": float(medoid_point.get("score", 0.0) or 0.0),
                "best_site_score_0_200": best_site_score_0_200(support=support, avg_stand_score_0_10=avg_score),
                "strategy": medoid_point.get("strategy"),
                "description": medoid_point.get("description"),
                "confidence": medoid_point.get("confidence"),
                "wind_thermal": medoid_point.get("wind_thermal"),
                "wind_overall": medoid_point.get("wind_overall"),
                "context_summary": medoid_point.get("context_summary"),
                "sources": ["cluster_medoid"],
                "reason": "Densest consensus cluster medoid (most repeatable across sample points)",
            }
        elif all_stands:
            best = max(all_stands, key=lambda s: float(s.get("score", 0.0)))
            support = 1
            avg_score = float(best.get("score", 0.0) or 0.0)
            best_stand_site = {
                "lat": float(best["lat"]),
                "lon": float(best["lon"]),
                "supporting_predictions": support,
                "cluster_avg_score_0_10": avg_score,
                "stand_score_0_10": float(best.get("score", 0.0) or 0.0),
                "best_site_score_0_200": best_site_score_0_200(support=support, avg_stand_score_0_10=avg_score),
                "strategy": best.get("strategy"),
                "description": best.get("description"),
                "confidence": best.get("confidence"),
                "wind_thermal": best.get("wind_thermal"),
                "wind_overall": best.get("wind_overall"),
                "context_summary": best.get("context_summary"),
                "sources": [str(best.get("source"))],
                "reason": "Fallback to highest scoring stand point (no clusters formed)",
            }

        baseline = best_stand_site

        report = {
            "job_id": job_id,
            "generated_at": _utc_now_iso(),
            "inputs": {
                "corners": [{"lat": c[0], "lon": c[1]} for c in corners],
                "mode": mode,
                "num_sample_points": num_sample_points,
                "lidar_grid_points": lidar_grid_points,
                "lidar_top_k": lidar_top_k,
                "lidar_sample_radius_m": lidar_sample_radius_m,
                "epsilon_meters": effective_epsilon,
                "min_samples": min_samples,
                "date_time": date_time,
                "season": season,
                "hunting_pressure": hunting_pressure,
            },
            "lidar_shortlist": lidar_shortlist,
            "lidar_meta": lidar_meta,
            "best_stand_site": best_stand_site,
            "baseline_stand": baseline,
            "clusters": clusters,
            "per_sample_point_best": per_point_best,
            "stand_points_count": len(all_stands),
        }

        report_path = job_dir / "hotspot_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        self.update_job(job_id, message="Building map")
        html = build_map_html(corners, all_stands, clusters, best_stand_site)
        map_path = job_dir / "hotspot_map.html"
        map_path.write_text(html, encoding="utf-8")

        self.update_job(
            job_id,
            status="completed",
            message="Completed",
            report_path=str(report_path),
            map_path=str(map_path),
        )


_hotspot_job_service: Optional[HotspotJobService] = None


def get_hotspot_job_service() -> HotspotJobService:
    global _hotspot_job_service
    if _hotspot_job_service is None:
        _hotspot_job_service = HotspotJobService()
    return _hotspot_job_service
