#!/usr/bin/env python
"""Compare two hotspot job reports to see if the Best Stand Site moved.

Usage:
  python tools/compare_hotspot_jobs.py --job-a <id> --job-b <id>

Or point directly at report files:
  python tools/compare_hotspot_jobs.py --report-a data/hotspot_jobs/<id>/hotspot_report.json --report-b data/hotspot_jobs/<id>/hotspot_report.json

Outputs:
  - Distance (meters) between best sites
  - Whether it's within the clustering radius threshold
  - Support, strategy, and score deltas
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, Tuple


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_report(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def best_site(report: Dict[str, Any]) -> Dict[str, Any] | None:
    bs = report.get("best_stand_site")
    if isinstance(bs, dict) and bs.get("lat") is not None and bs.get("lon") is not None:
        return bs
    bs = report.get("baseline_stand")
    if isinstance(bs, dict) and bs.get("lat") is not None and bs.get("lon") is not None:
        return bs
    return None


def fmt(v: Any) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job-a", help="Job ID A (looks for data/hotspot_jobs/<id>/hotspot_report.json)")
    ap.add_argument("--job-b", help="Job ID B (looks for data/hotspot_jobs/<id>/hotspot_report.json)")
    ap.add_argument("--report-a", help="Path to report A")
    ap.add_argument("--report-b", help="Path to report B")
    ap.add_argument("--radius-m", type=float, default=75.0, help="Threshold in meters to treat as same area")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]

    def _path_from_job(j: str) -> Path:
        return root / "data" / "hotspot_jobs" / j / "hotspot_report.json"

    report_a_path = Path(args.report_a) if args.report_a else (_path_from_job(args.job_a) if args.job_a else None)
    report_b_path = Path(args.report_b) if args.report_b else (_path_from_job(args.job_b) if args.job_b else None)

    if not report_a_path or not report_b_path:
        raise SystemExit("Provide --job-a/--job-b or --report-a/--report-b")

    if not report_a_path.exists():
        raise SystemExit(f"Missing report A: {report_a_path}")
    if not report_b_path.exists():
        raise SystemExit(f"Missing report B: {report_b_path}")

    ra = load_report(report_a_path)
    rb = load_report(report_b_path)

    a = best_site(ra)
    b = best_site(rb)
    if not a or not b:
        raise SystemExit("One report is missing best_stand_site/baseline_stand")

    lat1, lon1 = float(a["lat"]), float(a["lon"])
    lat2, lon2 = float(b["lat"]), float(b["lon"])
    dist = haversine_m(lat1, lon1, lat2, lon2)

    eps_a = float((ra.get("inputs") or {}).get("epsilon_meters") or args.radius_m)
    eps_b = float((rb.get("inputs") or {}).get("epsilon_meters") or args.radius_m)
    thresh = min(eps_a, eps_b, float(args.radius_m))

    print("=== Best Stand Site Comparison ===")
    print(f"A: {ra.get('job_id')}  dt={((ra.get('inputs') or {}).get('date_time'))}")
    print(f"   lat/lon: {lat1:.6f}, {lon1:.6f}")
    print(f"   support: {fmt(a.get('supporting_predictions'))}  strategy: {fmt(a.get('strategy'))}")
    print(f"   score_200: {fmt(a.get('best_site_score_0_200'))}  stand_score_0_10: {fmt(a.get('stand_score_0_10'))}")
    print(f"B: {rb.get('job_id')}  dt={((rb.get('inputs') or {}).get('date_time'))}")
    print(f"   lat/lon: {lat2:.6f}, {lon2:.6f}")
    print(f"   support: {fmt(b.get('supporting_predictions'))}  strategy: {fmt(b.get('strategy'))}")
    print(f"   score_200: {fmt(b.get('best_site_score_0_200'))}  stand_score_0_10: {fmt(b.get('stand_score_0_10'))}")

    print("---")
    print(f"Distance: {dist:.1f} m")
    print(f"Same area (<= {thresh:.0f}m): {'YES' if dist <= thresh else 'NO'}")
    print(f"Support delta (B-A): {float(b.get('supporting_predictions', 0) or 0) - float(a.get('supporting_predictions', 0) or 0):+.0f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
