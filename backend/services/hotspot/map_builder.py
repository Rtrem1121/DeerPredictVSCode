"""Folium map rendering for hotspot analysis reports."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from backend.utils.geo import bearing_to_cardinal

try:
    import folium  # type: ignore
except Exception:  # pragma: no cover
    folium = None


def _degrees_to_compass(degrees: Any) -> Optional[str]:
    """Convert a numeric bearing to a 16-point compass label."""
    try:
        if degrees is None:
            return None
        d = float(degrees) % 360.0
        _COMPASS_16 = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
        ]
        return _COMPASS_16[int((d + 11.25) / 22.5) % 16]
    except Exception:
        return None


def _points_center(points: List[Tuple[float, float]]) -> Tuple[float, float]:
    if not points:
        return 44.0, -72.5
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


def build_map_html(
    corners: List[Tuple[float, float]],
    stand_points: List[Dict[str, Any]],
    clusters: List[Dict[str, Any]],
    baseline: Optional[Dict[str, Any]],
) -> str:
    """Render a folium-based HTML map showing stand points, clusters, and best site."""
    if folium is None:
        return "<html><body><h3>folium not available</h3></body></html>"

    center_lat, center_lon = _points_center(corners or [(p["lat"], p["lon"]) for p in stand_points])
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15)

    if corners and len(corners) >= 3:
        folium.Polygon(locations=[[lat, lon] for lat, lon in corners], color="#2563eb", weight=3, fill=False).add_to(m)

    for p in stand_points[:500]:
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=4,
            color="#64748b",
            fill=True,
            fill_opacity=0.6,
            tooltip=f"{p.get('strategy','stand')} @ ({float(p['lat']):.6f}, {float(p['lon']):.6f})",
            popup=(
                f"<b>Stand:</b> {p.get('strategy','stand')}<br/>"
                f"<b>Score:</b> {float(p.get('score',0.0) or 0.0):.1f}<br/>"
                f"<b>Lat/Lon:</b> {float(p['lat']):.6f}, {float(p['lon']):.6f}"
            ),
        ).add_to(m)

    for c in clusters[:10]:
        centroid = c.get("centroid") or {}
        c_lat = float(centroid.get("lat"))
        c_lon = float(centroid.get("lon"))
        med = c.get("medoid") or {}
        m_lat = float(med.get("lat")) if med.get("lat") is not None else None
        m_lon = float(med.get("lon")) if med.get("lon") is not None else None
        popup_lines = [
            f"<b>Cluster:</b> {c.get('cluster_id')}",
            f"<b>Size:</b> {c.get('size')}",
            f"<b>Avg score:</b> {float(c.get('avg_score',0.0) or 0.0):.1f}",
            f"<b>Centroid:</b> {c_lat:.6f}, {c_lon:.6f}",
        ]
        if m_lat is not None and m_lon is not None:
            popup_lines.append(f"<b>Medoid:</b> {m_lat:.6f}, {m_lon:.6f}")
        folium.CircleMarker(
            location=[c_lat, c_lon],
            radius=8,
            color="#f97316",
            fill=True,
            fill_opacity=0.8,
            tooltip=f"Cluster {c.get('cluster_id')} @ ({c_lat:.6f}, {c_lon:.6f})",
            popup="<br/>".join(popup_lines),
        ).add_to(m)

    if baseline:
        popup_lines_b: List[str] = []
        popup_lines_b.append(f"<b>Lat/Lon:</b> {float(baseline['lat']):.6f}, {float(baseline['lon']):.6f}")
        score_200 = baseline.get("best_site_score_0_200")
        if isinstance(score_200, (int, float)):
            popup_lines_b.append(f"<b>Composite score:</b> {float(score_200):.0f}/200")
        stand_score = baseline.get("stand_score_0_10")
        if isinstance(stand_score, (int, float)):
            popup_lines_b.append(f"<b>Stand score:</b> {float(stand_score):.1f}/10")
        popup_lines_b.append(f"<b>Cluster support:</b> {int(baseline.get('supporting_predictions', 0))}")
        avg_cluster = baseline.get("cluster_avg_score_0_10")
        if isinstance(avg_cluster, (int, float)):
            popup_lines_b.append(f"<b>Cluster avg:</b> {float(avg_cluster):.1f}/10")

        desc = baseline.get("description")
        if isinstance(desc, str) and desc.strip():
            popup_lines_b.append(f"<b>Why here:</b> {desc}")

        wind = baseline.get("wind_thermal")
        if isinstance(wind, dict):
            wd = wind.get("wind_direction")
            ws = wind.get("wind_speed")
            prot = wind.get("wind_protection")
            therm = wind.get("thermal_advantage")
            optimal = wind.get("optimal_wind_alignment")
            scent_dir = wind.get("scent_cone_direction")
            approach = wind.get("optimal_approach_bearing")
            if wd is not None and ws is not None:
                wd_compass = _degrees_to_compass(wd)
                wd_label = f"{wd_compass} ({float(wd):.0f}\u00b0)" if wd_compass else f"{float(wd):.0f}\u00b0"
                popup_lines_b.append(f"<b>Wind (at run time):</b> {wd_label} @ {float(ws):.1f} mph")
            if prot is not None:
                popup_lines_b.append(f"<b>Wind protection:</b> {prot}")
            if therm is not None:
                popup_lines_b.append(f"<b>Thermal advantage:</b> {therm}")
            if isinstance(optimal, bool):
                popup_lines_b.append(f"<b>Optimal wind alignment:</b> {'Yes' if optimal else 'No'}")
            if scent_dir is not None:
                scent_compass = _degrees_to_compass(scent_dir)
                scent_label = f"{scent_compass} ({float(scent_dir):.0f}\u00b0)" if scent_compass else f"{float(scent_dir):.0f}\u00b0"
                popup_lines_b.append(f"<b>Scent cone travels toward:</b> {scent_label}")
            if approach is not None:
                app_compass = _degrees_to_compass(approach)
                app_label = f"{app_compass} ({float(approach):.0f}\u00b0)" if app_compass else f"{float(approach):.0f}\u00b0"
                popup_lines_b.append(f"<b>Suggested approach bearing:</b> {app_label}")

        overall = baseline.get("wind_overall")
        if isinstance(overall, dict):
            prevailing = overall.get("prevailing_wind")
            effective = overall.get("effective_wind")
            rating = overall.get("hunting_rating")
            if isinstance(prevailing, str) and prevailing.strip():
                popup_lines_b.append(f"<b>Prevailing wind:</b> {prevailing}")
            if isinstance(effective, str) and effective.strip():
                popup_lines_b.append(f"<b>Effective wind (terrain/thermals):</b> {effective}")
            if rating is not None:
                popup_lines_b.append(f"<b>Wind hunting rating:</b> {rating}")

        ctx = baseline.get("context_summary")
        if isinstance(ctx, dict):
            situation = ctx.get("situation")
            guidance = ctx.get("primary_guidance")
            if isinstance(situation, str) and situation.strip():
                popup_lines_b.append(f"<b>Situation:</b> {situation}")
            if isinstance(guidance, str) and guidance.strip():
                popup_lines_b.append(f"<b>Guidance:</b> {guidance}")

        folium.Marker(
            location=[baseline["lat"], baseline["lon"]],
            tooltip=(
                f"Best Stand Site @ ({float(baseline['lat']):.6f}, {float(baseline['lon']):.6f})"
                + (f" | {float(score_200):.0f}/200" if isinstance(score_200, (int, float)) else "")
            ),
            popup="<br/>".join(popup_lines_b) or "Best Stand Site",
            icon=folium.Icon(color="red", icon="star"),
        ).add_to(m)

    return m.get_root().render()
