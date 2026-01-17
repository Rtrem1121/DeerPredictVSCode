#!/usr/bin/env python
"""Run two hotspot jobs around sunrise (e.g., -30m and +30m).

- Reads property corners and default params from an existing hotspot_report.json.
- Computes sunrise for the property's centroid (America/New_York by default).
- Submits two jobs to the backend: sunrise-offset and sunrise+offset.

Usage (PowerShell):
  python tools/run_hotspot_sunrise_bracket.py --report data/hotspot_jobs/<job_id>/hotspot_report.json --date 2025-10-15 --offset-min 30

Requires:
  - Backend running on http://localhost:8000
  - Python 3.9+ (uses zoneinfo)

This intentionally uses only the Python standard library (no astral dependency).
"""

from __future__ import annotations

import argparse
import json
import math
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

try:
    from zoneinfo import ZoneInfo
except Exception as e:  # pragma: no cover
    raise SystemExit("Python 3.9+ required (zoneinfo missing)") from e


ZENITH_DEG = 90.833  # official sunrise/sunset (includes atmospheric refraction)


@dataclass(frozen=True)
class SunTimes:
    sunrise_local: datetime
    sunset_local: datetime


def _normalize_deg(x: float) -> float:
    x = x % 360.0
    return x + 360.0 if x < 0 else x


def _normalize_hours(h: float) -> float:
    h = h % 24.0
    return h + 24.0 if h < 0 else h


def _deg_to_rad(d: float) -> float:
    return d * math.pi / 180.0


def _rad_to_deg(r: float) -> float:
    return r * 180.0 / math.pi


def _noaa_sunrise_sunset_utc(d: date, lat: float, lon: float) -> Tuple[datetime, datetime]:
    """Compute sunrise/sunset in UTC for the given date/lat/lon.

    Algorithm: NOAA Solar Calculator (approximate but good for scheduling runs).
    Returns naive UTC datetimes with tzinfo=UTC.
    """

    n = d.timetuple().tm_yday
    lng_hour = lon / 15.0

    def _calc(is_sunrise: bool) -> datetime:
        # 1) approximate time
        t = n + ((6.0 - lng_hour) / 24.0) if is_sunrise else n + ((18.0 - lng_hour) / 24.0)

        # 2) sun's mean anomaly
        m = (0.9856 * t) - 3.289

        # 3) sun's true longitude
        l = m + (1.916 * math.sin(_deg_to_rad(m))) + (0.020 * math.sin(_deg_to_rad(2 * m))) + 282.634
        l = _normalize_deg(l)

        # 4) right ascension
        ra = _rad_to_deg(math.atan(0.91764 * math.tan(_deg_to_rad(l))))
        ra = _normalize_deg(ra)

        # 5) RA quadrant adjustment
        l_quadrant = (math.floor(l / 90.0)) * 90.0
        ra_quadrant = (math.floor(ra / 90.0)) * 90.0
        ra = ra + (l_quadrant - ra_quadrant)
        ra = ra / 15.0

        # 6) declination
        sin_dec = 0.39782 * math.sin(_deg_to_rad(l))
        cos_dec = math.cos(math.asin(sin_dec))

        # 7) local hour angle
        cos_h = (
            math.cos(_deg_to_rad(ZENITH_DEG)) - (sin_dec * math.sin(_deg_to_rad(lat)))
        ) / (cos_dec * math.cos(_deg_to_rad(lat)))

        # edge cases: polar day/night
        if cos_h > 1.0:
            raise ValueError("Sun never rises on this date at this location")
        if cos_h < -1.0:
            raise ValueError("Sun never sets on this date at this location")

        h = 360.0 - _rad_to_deg(math.acos(cos_h)) if is_sunrise else _rad_to_deg(math.acos(cos_h))
        h = h / 15.0

        # 8) local mean time
        t_local = h + ra - (0.06571 * t) - 6.622

        # 9) convert to UTC
        ut = t_local - lng_hour
        ut = _normalize_hours(ut)

        # Create a UTC datetime relative to the requested date.
        # ut is hours after 00:00 UTC of the same date (usually), but can roll.
        dt0 = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        dt = dt0 + timedelta(hours=ut)

        # If ut wrapped (e.g., > 23:59 local), NOAA normalization hides date rollover.
        # We keep dt within +/- 1 day by comparing to noon UTC.
        noon = dt0 + timedelta(hours=12)
        if dt - noon > timedelta(hours=18):
            dt -= timedelta(days=1)
        elif noon - dt > timedelta(hours=18):
            dt += timedelta(days=1)

        return dt

    sunrise_utc = _calc(True)
    sunset_utc = _calc(False)
    return sunrise_utc, sunset_utc


def compute_sun_times_local(d: date, lat: float, lon: float, tz_name: str) -> SunTimes:
    tz = ZoneInfo(tz_name)
    sr_utc, ss_utc = _noaa_sunrise_sunset_utc(d, lat, lon)
    return SunTimes(sunrise_local=sr_utc.astimezone(tz), sunset_local=ss_utc.astimezone(tz))


def _centroid(corners: List[Dict[str, Any]]) -> Tuple[float, float]:
    lats = [float(c["lat"]) for c in corners]
    lons = [float(c["lon"]) for c in corners]
    return (sum(lats) / len(lats), sum(lons) / len(lons))


def _http_json(method: str, url: str, body: Dict[str, Any] | None = None) -> Dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        try:
            msg = e.read().decode("utf-8")
        except Exception:
            msg = str(e)
        raise RuntimeError(f"HTTP {e.code} from {url}: {msg}") from e


def _to_backend_iso(dt_local: datetime) -> str:
    # Backend parser accepts ISO with offset; keep offset.
    # Example: 2025-10-15T06:30:00-04:00
    return dt_local.replace(microsecond=0).isoformat()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True, help="Path to hotspot_report.json to reuse corners/params")
    ap.add_argument("--date", required=False, help="YYYY-MM-DD (defaults to report inputs.date_time date)")
    ap.add_argument("--offset-min", type=int, default=30, help="Minutes before/after sunrise")
    ap.add_argument("--tz", default="America/New_York")
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--poll", action="store_true", help="Poll until jobs complete")
    args = ap.parse_args()

    report_obj = json.loads(open(args.report, "r", encoding="utf-8").read())
    inputs = report_obj.get("inputs") or {}
    corners = inputs.get("corners")
    if not isinstance(corners, list) or len(corners) < 3:
        raise SystemExit("Report missing inputs.corners")

    # Choose date
    if args.date:
        y, m, d = (int(x) for x in args.date.split("-"))
        run_date = date(y, m, d)
    else:
        dt_str = str(inputs.get("date_time") or "")
        if not dt_str:
            raise SystemExit("Provide --date (report has no inputs.date_time)")
        run_date = datetime.fromisoformat(dt_str.replace("Z", "+00:00")).date()

    lat_c, lon_c = _centroid(corners)
    sun = compute_sun_times_local(run_date, lat_c, lon_c, args.tz)

    before = sun.sunrise_local - timedelta(minutes=args.offset_min)
    after = sun.sunrise_local + timedelta(minutes=args.offset_min)

    # Build payload from report inputs (reuse same job params)
    def _payload(dt: datetime) -> Dict[str, Any]:
        return {
            "corners": corners,
            "mode": inputs.get("mode", "lidar_first"),
            "num_sample_points": inputs.get("num_sample_points", 25),
            "lidar_grid_points": inputs.get("lidar_grid_points", 100000),
            "lidar_top_k": inputs.get("lidar_top_k", 20),
            "lidar_sample_radius_m": inputs.get("lidar_sample_radius_m", 30),
            "epsilon_meters": inputs.get("epsilon_meters", 75.0),
            "min_samples": inputs.get("min_samples", 2),
            "date_time": _to_backend_iso(dt),
            "season": inputs.get("season", "fall"),
            "hunting_pressure": inputs.get("hunting_pressure", "high"),
        }

    print(f"Property centroid: {lat_c:.6f}, {lon_c:.6f} ({args.tz})")
    print(f"Sunrise local: {sun.sunrise_local.isoformat()}")
    print(f"Submitting jobs at {before.isoformat()} and {after.isoformat()}")

    run_url = args.base_url.rstrip("/") + "/property-hotspots/run"
    status_url = args.base_url.rstrip("/") + "/property-hotspots/status/{}"

    res1 = _http_json("POST", run_url, _payload(before))
    res2 = _http_json("POST", run_url, _payload(after))

    if not res1.get("success") or not res2.get("success"):
        raise SystemExit(f"Submission failed: {res1} {res2}")

    id1 = res1.get("job_id")
    id2 = res2.get("job_id")

    print(f"Job (sunrise -{args.offset_min}m): {id1}")
    print(f"Job (sunrise +{args.offset_min}m): {id2}")

    if args.poll:
        def _poll_one(job_id: str) -> None:
            while True:
                s = _http_json("GET", status_url.format(job_id))
                job = s.get("job") or {}
                print(f"[{job_id}] {job.get('status')} {job.get('completed')}/{job.get('total')} {job.get('message')}")
                if job.get("status") in {"completed", "failed"}:
                    return
                time.sleep(5)

        _poll_one(str(id1))
        _poll_one(str(id2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
