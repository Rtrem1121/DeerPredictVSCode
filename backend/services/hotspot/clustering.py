"""Stand-point extraction and DBSCAN clustering for hotspot analysis."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.utils.geo import haversine


def _meters_to_radians(meters: float) -> float:
    return meters / 6371000.0


def extract_stand_points(prediction: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Pull stand-site points from a full prediction payload."""
    stands: List[Dict[str, Any]] = []

    wind_thermal = prediction.get("wind_thermal_analysis") if isinstance(prediction, dict) else None
    if not isinstance(wind_thermal, dict):
        wind_thermal = None

    wind_summary = prediction.get("wind_summary") if isinstance(prediction, dict) else None
    if not isinstance(wind_summary, dict):
        wind_summary = None
    wind_overall = wind_summary.get("overall_wind_conditions") if isinstance(wind_summary, dict) else None
    if not isinstance(wind_overall, dict):
        wind_overall = None

    context_summary = prediction.get("context_summary") if isinstance(prediction, dict) else None
    if not isinstance(context_summary, dict):
        context_summary = None

    optimized = prediction.get("optimized_points") if isinstance(prediction, dict) else None
    if isinstance(optimized, dict):
        stand_sites = optimized.get("stand_sites")
        if isinstance(stand_sites, list):
            for s in stand_sites:
                if not isinstance(s, dict):
                    continue
                lat = s.get("lat")
                lon = s.get("lon")
                if lat is None or lon is None:
                    continue
                stands.append(
                    {
                        "lat": float(lat),
                        "lon": float(lon),
                        "score": float(s.get("score", 0.0) or 0.0),
                        "strategy": s.get("strategy") or s.get("description") or "stand_site",
                        "source": "optimized_points.stand_sites",
                        "description": s.get("description"),
                        "confidence": s.get("confidence"),
                        "wind_thermal": wind_thermal,
                        "wind_overall": wind_overall,
                        "context_summary": context_summary,
                        "raw": s,
                    }
                )

    mba = prediction.get("mature_buck_analysis") if isinstance(prediction, dict) else None
    if isinstance(mba, dict):
        stand_recs = mba.get("stand_recommendations")
        if isinstance(stand_recs, list):
            for s in stand_recs:
                if not isinstance(s, dict):
                    continue
                lat = s.get("lat")
                lon = s.get("lon")
                if lat is None or lon is None:
                    continue
                stands.append(
                    {
                        "lat": float(lat),
                        "lon": float(lon),
                        "score": float(s.get("score", 0.0) or 0.0),
                        "strategy": s.get("strategy") or s.get("type") or "stand_recommendation",
                        "source": "mature_buck_analysis.stand_recommendations",
                        "description": s.get("description") or s.get("reason"),
                        "confidence": s.get("confidence"),
                        "wind_thermal": wind_thermal,
                        "wind_overall": wind_overall,
                        "context_summary": context_summary,
                        "raw": s,
                    }
                )

    return stands


def stand_summary_for_report(stand: Dict[str, Any]) -> Dict[str, Any]:
    """Create a slimmed-down stand dict for JSON reports."""
    return {
        "lat": float(stand.get("lat")) if stand.get("lat") is not None else None,
        "lon": float(stand.get("lon")) if stand.get("lon") is not None else None,
        "score": float(stand.get("score", 0.0) or 0.0),
        "strategy": stand.get("strategy"),
        "source": stand.get("source"),
        "description": stand.get("description"),
        "confidence": stand.get("confidence"),
        "wind_thermal": stand.get("wind_thermal"),
        "wind_overall": stand.get("wind_overall"),
        "context_summary": stand.get("context_summary"),
    }


def best_site_score_0_200(*, support: int, avg_stand_score_0_10: float) -> float:
    """Composite UX score (approx 0‥200)."""
    s = 15.0 + (5.0 * float(max(0, support))) + (10.0 * float(max(0.0, min(10.0, avg_stand_score_0_10))))
    return float(max(0.0, min(200.0, s)))


def cluster_stands(
    points: List[Dict[str, Any]],
    epsilon_m: float,
    min_samples: int,
) -> List[Dict[str, Any]]:
    """Cluster stand points with DBSCAN (haversine metric) and return ranked clusters."""
    if not points:
        return []

    try:
        import numpy as np  # type: ignore
        from sklearn.cluster import DBSCAN  # type: ignore

        coords = np.radians(np.array([[p["lat"], p["lon"]] for p in points], dtype=float))
        clustering = DBSCAN(eps=_meters_to_radians(epsilon_m), min_samples=min_samples, metric="haversine")
        labels = clustering.fit_predict(coords)

        clusters: Dict[int, List[int]] = {}
        for idx, label in enumerate(labels):
            if int(label) == -1:
                continue
            clusters.setdefault(int(label), []).append(idx)

        out: List[Dict[str, Any]] = []
        for label, idxs in clusters.items():
            cluster_points = [points[i] for i in idxs]
            centroid_lat = sum(p["lat"] for p in cluster_points) / len(cluster_points)
            centroid_lon = sum(p["lon"] for p in cluster_points) / len(cluster_points)

            best_i = 0
            best_sum = float("inf")
            for i, p in enumerate(cluster_points):
                s = sum(haversine(p["lat"], p["lon"], q["lat"], q["lon"]) for q in cluster_points)
                if s < best_sum:
                    best_sum = s
                    best_i = i

            medoid = cluster_points[best_i]
            best_point = max(cluster_points, key=lambda s: float(s.get("score", 0.0)))
            avg_score = sum(p.get("score", 0.0) for p in cluster_points) / len(cluster_points)
            out.append(
                {
                    "cluster_id": label,
                    "size": len(cluster_points),
                    "centroid": {"lat": centroid_lat, "lon": centroid_lon},
                    "medoid": {"lat": medoid["lat"], "lon": medoid["lon"]},
                    "avg_score": avg_score,
                    "best_score": float(best_point.get("score", 0.0) or 0.0),
                    "medoid_point": stand_summary_for_report(medoid),
                    "best_point": stand_summary_for_report(best_point),
                    "strategies": sorted({str(p.get("strategy") or "") for p in cluster_points if p.get("strategy")}),
                    "points": [
                        {
                            "lat": p["lat"],
                            "lon": p["lon"],
                            "score": p.get("score", 0.0),
                            "strategy": p.get("strategy"),
                            "source": p.get("source"),
                        }
                        for p in cluster_points
                    ],
                }
            )

        out.sort(key=lambda c: (c["size"], c["avg_score"]), reverse=True)
        return out

    except Exception:
        return []
