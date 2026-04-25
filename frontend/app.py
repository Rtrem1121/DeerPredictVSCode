import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import json
import os
import hashlib
import math
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from dotenv import load_dotenv
from map_config import MAP_SOURCES
from enhanced_data_validation import (
    create_enhanced_data_traceability_display,
)

# Load environment variables
load_dotenv()

# Configure logging for enhanced data traceability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

COMPASS_DIRECTIONS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
]


def degrees_to_compass(degrees):
    """Convert degrees to a compass string."""
    try:
        if degrees is None:
            return "Unknown"
        deg = float(degrees) % 360
        return COMPASS_DIRECTIONS[int((deg + 11.25) / 22.5) % 16]
    except (TypeError, ValueError):
        return "Unknown"


# --- Password Protection ---
def check_password():
    """Returns True if the user entered the correct password."""
    configured_password = os.getenv("APP_PASSWORD")

    if not configured_password:
        st.error("APP_PASSWORD is not configured. Set APP_PASSWORD in the environment to enable access.")
        return False
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # Check if password key exists before accessing it
        if "password" in st.session_state:
            if hashlib.sha256(st.session_state["password"].encode()).hexdigest() == hashlib.sha256(configured_password.encode()).hexdigest():
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Don't store password
            else:
                st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.markdown("# 🦌 Professional Deer Hunting Intelligence")
        st.markdown("### 🔐 Secure Access Required")
        st.markdown("*89.1% confidence predictions • Vermont legal hours • Real-time scouting data*")
        st.markdown("---")
        st.text_input(
            "Enter Access Password:", 
            type="password", 
            on_change=password_entered, 
            key="password",
            help="Contact the administrator for access credentials"
        )
        st.markdown("---")
        st.markdown("*🏔️ Vermont Deer Movement Predictor with Enhanced Intelligence*")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error
        st.markdown("# 🦌 Professional Deer Hunting Intelligence")
        st.markdown("### 🔐 Secure Access Required")
        st.markdown("*89.1% confidence predictions • Vermont legal hours • Real-time scouting data*")
        st.markdown("---")
        st.text_input(
            "Enter Access Password:", 
            type="password", 
            on_change=password_entered, 
            key="password",
            help="Contact the administrator for access credentials"
        )
        st.error("🚫 Access denied. Please check your password and try again.")
        st.markdown("---")
        st.markdown("*🏔️ Vermont Deer Movement Predictor with Enhanced Intelligence*")
        return False
    else:
        # Password correct
        return True

# --- Backend Configuration ---
BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')

# --- Map Configuration ---
# Filter enabled map sources
MAP_CONFIGS = {
    name: config for name, config in MAP_SOURCES.items() 
    if config.get("enabled", True)
}

def create_map(location, zoom_start, map_type):
    """Create a Folium map with the specified map type"""
    config = MAP_CONFIGS.get(map_type, MAP_CONFIGS["Street Map"])
    
    if config["tiles"]:
        return folium.Map(
            location=location,
            zoom_start=zoom_start,
            tiles=config["tiles"],
            attr=config["attr"]
        )
    else:
        return folium.Map(location=location, zoom_start=zoom_start)

# --- Scouting Functions ---
@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_observation_types_cached(base_url: str):
    """Cacheable helper so we don't hammer /scouting/types."""
    response = requests.get(f"{base_url}/scouting/types", timeout=10)
    response.raise_for_status()
    return response.json().get('observation_types', [])


def get_observation_types():
    """Get available scouting observation types from backend with hourly refresh."""
    try:
        return _fetch_observation_types_cached(BACKEND_URL)
    except Exception as e:
        st.error(f"Failed to load observation types: {e}")
        return []

def add_scouting_observation(observation_data):
    """Add a new scouting observation"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/scouting/add_observation",
            json=observation_data,
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to add observation: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error adding observation: {e}")
        return None

def get_scouting_observations(lat, lon, radius_miles=2):
    """Get scouting observations near a location"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/scouting/observations",
            params={
                'lat': lat,
                'lon': lon,
                'radius_miles': radius_miles
            }
        )
        if response.status_code == 200:
            return response.json().get('observations', [])
    except Exception as e:
        st.error(f"Failed to load observations: {e}")
    return []

def get_scouting_analytics(lat, lon, radius_miles=5):
    """Get scouting analytics for an area"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/scouting/analytics",
            params={
                'lat': lat,
                'lon': lon,
                'radius_miles': radius_miles
            }
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Failed to load analytics: {e}")
    return {}

# --- App Configuration ---
st.set_page_config(
    page_title="🏔️ Vermont Deer Movement Predictor",
    page_icon="🦌",
    layout="wide"
)

# Add custom CSS for Vermont-themed styling
st.markdown("""
<style>
/* ── Base ── */
.stAlert > div { padding: 0.5rem 1rem; }
.stExpander > div:first-child { background-color: #f8fafc; }
.observation-marker {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 0.5rem;
    padding: 0.5rem;
    margin: 0.5rem 0;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
[data-testid="stMetricLabel"] {
    font-size: 0.82em !important;
    color: #64748b !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
[data-testid="stMetricValue"] {
    font-size: 1.3em !important;
    font-weight: 700 !important;
    color: #1e293b !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 2px solid #e2e8f0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 8px 20px;
    font-weight: 600;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    border-radius: 8px;
}

/* ── Divider ── */
hr { border-color: #e2e8f0 !important; }

/* ── Subheader spacing ── */
h3 { margin-top: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)

# --- Main App ---
# Check password protection first
if not check_password():
    st.stop()

st.title("🏔️ Vermont Deer Movement Predictor")
st.markdown("*LiDAR-powered terrain analysis for mature buck stand selection*")

# Create main navigation tabs
tab_hotspots, tab_scout, tab_analytics = st.tabs([
    "🎯 Max Accuracy Analysis",
    "🔍 Scouting Data",
    "📊 Analytics",
])


def _parse_corners_text(text: str) -> list[dict[str, float]]:
    corners: list[dict[str, float]] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        # allow "NW 43.31, -73.21" or "43.31,-73.21"
        parts = line.replace("\t", " ").replace(";", ",").split(",")
        if len(parts) < 2:
            # try split by whitespace
            bits = [b for b in line.split(" ") if b]
            if len(bits) >= 2:
                parts = [bits[-2], bits[-1]]
            else:
                continue

        try:
            lat = float(str(parts[0]).split()[-1])
            lon = float(str(parts[1]).split()[0])
        except Exception:
            continue

        corners.append({"lat": lat, "lon": lon})
    return corners


def _corners_centroid(corners: list[dict[str, float]]) -> tuple[float, float] | None:
    if not corners:
        return None
    lats = [c.get("lat") for c in corners if isinstance(c, dict) and isinstance(c.get("lat"), (int, float))]
    lons = [c.get("lon") for c in corners if isinstance(c, dict) and isinstance(c.get("lon"), (int, float))]
    if not lats or not lons:
        return None
    return (sum(lats) / len(lats), sum(lons) / len(lons))


def _noaa_sun_event_utc(date_local, lat: float, lon: float, *, is_sunrise: bool) -> datetime | None:
    """Approx sunrise/sunset time in UTC using NOAA algorithm.

    Good enough for scheduling +/- 30 minutes. Returns None if the event
    doesn't occur (e.g., polar regions).
    """

    # https://gml.noaa.gov/grad/solcalc/solareqns.PDF (classic approximate method)
    zenith = 90.833  # official
    n = int(date_local.timetuple().tm_yday)
    lng_hour = float(lon) / 15.0
    base_hour = 6.0 if is_sunrise else 18.0
    t = n + ((base_hour - lng_hour) / 24.0)

    m = (0.9856 * t) - 3.289
    l = m + (1.916 * math.sin(math.radians(m))) + (0.020 * math.sin(math.radians(2 * m))) + 282.634
    l = l % 360.0

    ra = math.degrees(math.atan(0.91764 * math.tan(math.radians(l))))
    ra = ra % 360.0
    l_quadrant = (math.floor(l / 90.0)) * 90.0
    ra_quadrant = (math.floor(ra / 90.0)) * 90.0
    ra = ra + (l_quadrant - ra_quadrant)
    ra_hours = ra / 15.0

    sin_dec = 0.39782 * math.sin(math.radians(l))
    cos_dec = math.cos(math.asin(sin_dec))

    cos_h = (
        math.cos(math.radians(zenith)) - (sin_dec * math.sin(math.radians(lat)))
    ) / (cos_dec * math.cos(math.radians(lat)))

    if cos_h > 1.0 or cos_h < -1.0:
        return None

    if is_sunrise:
        h = 360.0 - math.degrees(math.acos(cos_h))
    else:
        h = math.degrees(math.acos(cos_h))

    h_hours = h / 15.0

    t_local = h_hours + ra_hours - (0.06571 * t) - 6.622
    ut = (t_local - lng_hour) % 24.0

    # Build via timedelta so seconds/minutes carry correctly (the manual
    # decomposition pinned second to 59 on overflow, drifting up to 1
    # minute earlier than reality).
    base = datetime(
        date_local.year, date_local.month, date_local.day, tzinfo=timezone.utc
    )
    return base + timedelta(seconds=round(ut * 3600.0))


def _noaa_sunrise_utc(date_local, lat: float, lon: float) -> datetime | None:
    return _noaa_sun_event_utc(date_local, lat, lon, is_sunrise=True)


def _noaa_sunset_utc(date_local, lat: float, lon: float) -> datetime | None:
    return _noaa_sun_event_utc(date_local, lat, lon, is_sunrise=False)


def _dt_to_iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

# Initialize session state for map data
if 'hunt_location' not in st.session_state:
    st.session_state.hunt_location = [44.26639, -72.58133]  # Vermont center
if 'map_zoom' not in st.session_state:
    st.session_state.map_zoom = 12

# ==========================================
# TAB 1: MAX ACCURACY ANALYSIS
# ==========================================
with tab_hotspots:
    st.header("🎯 Max Accuracy Stand Analysis")
    st.caption(
        "Dense LiDAR terrain scan with strict mature buck bedding criteria, "
        "quality-weighted proximity scoring, and quadrant diversity."
    )

    st.subheader("Run Analysis")
    ma_settings_path = os.path.join("data", "max_accuracy_ui.json")
    if not st.session_state.get("ma_settings_loaded"):
        try:
            if os.path.exists(ma_settings_path):
                with open(ma_settings_path, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                if isinstance(stored, dict):
                    for key, value in stored.items():
                        st.session_state.setdefault(key, value)
        except Exception:
            pass
        st.session_state["ma_settings_loaded"] = True
    max_accuracy_config: dict[str, object] = {}
    with st.expander("Max Accuracy settings", expanded=False):
            col_ma_a, col_ma_b, col_ma_c = st.columns(3)
            with col_ma_a:
                grid_spacing_m = st.number_input(
                    "Grid spacing (m)",
                    min_value=5,
                    max_value=100,
                    value=st.session_state.get("ma_grid_spacing_m", 20),
                    step=5,
                    help="Distance between LiDAR sample points. Smaller = more detail, slower.",
                    key="ma_grid_spacing_m",
                )
                max_candidates = st.number_input(
                    "Max candidates",
                    min_value=500,
                    max_value=20000,
                    value=st.session_state.get("ma_max_candidates", 20000),
                    step=500,
                    help="How many top terrain points are kept before final ranking.",
                    key="ma_max_candidates",
                )
            with col_ma_b:
                gee_sample_k = st.number_input(
                    "GEE sample K",
                    min_value=0,
                    max_value=2000,
                    value=st.session_state.get("ma_gee_sample_k", 100),
                    step=50,
                    help="How many candidates get canopy/NDVI enrichment. Higher = better but slower.",
                    key="ma_gee_sample_k",
                )
                behavior_weight = st.slider(
                    "Behavior weight",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.get("ma_behavior_weight", 0.50),
                    step=0.05,
                    help="Blend between terrain and behavior scores (0=terrain only, 1=behavior only).",
                    key="ma_behavior_weight",
                )
            with col_ma_c:
                tpi_small_m = st.number_input(
                    "TPI small window (m)",
                    min_value=20,
                    max_value=200,
                    value=st.session_state.get("ma_tpi_small_m", 60),
                    step=10,
                    help="Small-scale terrain context for benches/saddles.",
                    key="ma_tpi_small_m",
                )
                tpi_large_m = st.number_input(
                    "TPI large window (m)",
                    min_value=60,
                    max_value=600,
                    value=st.session_state.get("ma_tpi_large_m", 200),
                    step=20,
                    help="Large-scale terrain context for corridors/ridges.",
                    key="ma_tpi_large_m",
                )

            col_ma_d, col_ma_e, col_ma_f = st.columns(3)
            with col_ma_d:
                top_k_stands = st.number_input(
                    "Top K stands",
                    min_value=5,
                    max_value=100,
                    value=st.session_state.get("ma_top_k_stands", 20),
                    step=5,
                    help="Number of stand recommendations returned.",
                    key="ma_top_k_stands",
                )
            with col_ma_e:
                wind_offset_m = st.number_input(
                    "Wind offset (m)",
                    min_value=10,
                    max_value=250,
                    value=int(round(float(st.session_state.get("ma_wind_offset_m", 60.0)))),
                    step=10,
                    help="Distance to offset a stand downwind for scent control.",
                    key="ma_wind_offset_m",
                )
            with col_ma_f:
                min_per_quadrant = st.number_input(
                    "Min per quadrant",
                    min_value=0,
                    max_value=20,
                    value=st.session_state.get("ma_min_per_quadrant", 1),
                    step=1,
                    help="Ensures spatial diversity across the property.",
                    key="ma_min_per_quadrant",
                )

            st.markdown(
                """
**Settings legend**
- **Grid spacing:** Smaller = more detail, slower.
- **Max candidates:** Size of the candidate pool before final ranking.
- **GEE sample K:** How many candidates get canopy/NDVI enrichment.
- **Behavior weight:** Blend terrain vs behavior score.
- **TPI windows:** Terrain context at small/large scales.
- **Top K stands:** Number of recommendations returned.
- **Wind offset:** Stand offset distance for wind/scent.
- **Min per quadrant:** Enforces spatial diversity.
"""
            )

            max_accuracy_config = {
                "grid_spacing_m": int(grid_spacing_m),
                "max_candidates": int(max_candidates),
                "top_k_stands": int(top_k_stands),
                "gee_sample_k": int(gee_sample_k),
                "wind_offset_m": float(wind_offset_m),
                "behavior_weight": float(behavior_weight),
                "tpi_small_m": int(tpi_small_m),
                "tpi_large_m": int(tpi_large_m),
                "min_per_quadrant": int(min_per_quadrant),
            }
            try:
                os.makedirs(os.path.dirname(ma_settings_path), exist_ok=True)
                with open(ma_settings_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "ma_grid_spacing_m": int(grid_spacing_m),
                            "ma_max_candidates": int(max_candidates),
                            "ma_gee_sample_k": int(gee_sample_k),
                            "ma_behavior_weight": float(behavior_weight),
                            "ma_tpi_small_m": int(tpi_small_m),
                            "ma_tpi_large_m": int(tpi_large_m),
                            "ma_top_k_stands": int(top_k_stands),
                            "ma_wind_offset_m": float(wind_offset_m),
                            "ma_min_per_quadrant": int(min_per_quadrant),
                        },
                        f,
                        indent=2,
                    )
            except Exception:
                pass
    default_corners = "\n".join(
        [
            "NW 43.31925, -73.23064",
            "NE 43.32165, -73.20444",
            "SE 43.29906, -73.21121",
            "SW 43.30036, -73.24005",
        ]
    )
    corners_text = st.text_area(
        "Property corners (one per line)",
        value=st.session_state.get("hotspot_corners_text", default_corners),
        height=120,
        help="Format examples: 'NW 43.31, -73.21' or '43.31, -73.21'",
    )
    st.session_state["hotspot_corners_text"] = corners_text

    dt_mode = st.radio(
        "Time",
        ["Manual (ISO UTC)", "Sunrise bracket (±30 min)", "Sunset bracket (±30 min)"],
        index=0,
        horizontal=True,
        help="Bracket mode submits two jobs around sunrise/sunset for the property centroid.",
    )

    dt = st.text_input("ISO datetime (UTC)", value="2025-10-15T10:30:00Z", disabled=(dt_mode != "Manual (ISO UTC)"))

    sunrise_date = None
    if dt_mode != "Manual (ISO UTC)":
        sunrise_date = st.date_input("Date (local)")
    pressure = st.selectbox("Hunting pressure", ["low", "medium", "high"], index=2)

    if st.button("Run property hotspot analysis", type="primary"):
        corners = _parse_corners_text(corners_text)
        if len(corners) < 3:
            st.error("Please provide at least 3 corners (lat/lon).")
        else:
            try:
                payload = {
                    "corners": corners,
                    "season": "fall",
                    "hunting_pressure": pressure,
                    "config": max_accuracy_config,
                }

                if dt_mode in {"Sunrise bracket (±30 min)", "Sunset bracket (±30 min)"}:
                    centroid = _corners_centroid(corners)
                    if not centroid:
                        st.error("Could not compute property centroid from corners.")
                        payload = None
                    else:
                        lat_c, lon_c = centroid
                        is_sunrise = dt_mode.startswith("Sunrise")
                        event_utc = _noaa_sunrise_utc(sunrise_date, lat_c, lon_c) if is_sunrise else _noaa_sunset_utc(sunrise_date, lat_c, lon_c)
                        if not event_utc:
                            st.error("Sunrise/sunset could not be computed for this date/location.")
                            payload = None
                        else:
                            payload["date_time"] = _dt_to_iso_z(event_utc)
                else:
                    payload["date_time"] = dt

                if payload:
                    with st.spinner("Running Max Accuracy analysis..."):
                        resp = requests.post(f"{BACKEND_URL}/property-hotspots/max-accuracy/run", json=payload, timeout=300)
                        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    if resp.status_code == 200 and data.get("success") and data.get("job_id"):
                        job_id = data["job_id"]
                        st.session_state["max_accuracy_job_id"] = job_id
                        st.session_state["max_accuracy_auto_loaded"] = False
                        # Auto-poll until report is ready
                        status_msg = st.empty()
                        progress_bar = st.progress(0)
                        max_poll = 120  # up to 10 minutes (120 × 5s)
                        loaded = False
                        for i in range(max_poll):
                            status_msg.info(f"⏳ Waiting for report... ({(i + 1) * 5}s)")
                            progress_bar.progress(min(0.95, (i + 1) / max_poll))
                            time.sleep(5)
                            try:
                                rpt = requests.get(f"{BACKEND_URL}/property-hotspots/max-accuracy/report/{job_id}", timeout=30)
                                rpt_data = rpt.json() if rpt.headers.get("content-type", "").startswith("application/json") else {}
                                if rpt.status_code == 200 and rpt_data.get("success") and rpt_data.get("report"):
                                    st.session_state["max_accuracy_report"] = rpt_data["report"]
                                    st.session_state["max_accuracy_auto_loaded"] = True
                                    progress_bar.progress(1.0)
                                    status_msg.success("✅ Max Accuracy report loaded!")
                                    loaded = True
                                    time.sleep(1)
                                    st.rerun()
                                    break
                            except Exception:
                                pass
                        if not loaded:
                            progress_bar.progress(1.0)
                            status_msg.warning("Report is still processing. Use the refresh button below.")
                    else:
                        st.error(f"Max Accuracy failed: {data.get('error') or resp.text}")
            except Exception as e:
                st.error(f"Could not start job: {e}")

    max_accuracy_report = st.session_state.get("max_accuracy_report")
    max_accuracy_job_id = st.session_state.get("max_accuracy_job_id")
    if max_accuracy_job_id and not isinstance(max_accuracy_report, dict) and not st.session_state.get("max_accuracy_auto_loaded"):
        try:
            resp = requests.get(f"{BACKEND_URL}/property-hotspots/max-accuracy/report/{max_accuracy_job_id}", timeout=30)
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            if resp.status_code == 200 and data.get("success") and data.get("report"):
                st.session_state["max_accuracy_report"] = data["report"]
                max_accuracy_report = data["report"]
                st.session_state["max_accuracy_auto_loaded"] = True
        except Exception:
            pass
    if st.session_state.get("max_accuracy_job_id"):
        if not isinstance(max_accuracy_report, dict):
            if st.button("🔄 Refresh report"):
                job_id = st.session_state.get("max_accuracy_job_id")
                try:
                    resp = requests.get(f"{BACKEND_URL}/property-hotspots/max-accuracy/report/{job_id}", timeout=30)
                    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    if resp.status_code == 200 and data.get("success") and data.get("report"):
                        st.session_state["max_accuracy_report"] = data["report"]
                        max_accuracy_report = data["report"]
                        st.success("Report loaded.")
                    else:
                        st.warning("Report not ready yet.")
                except Exception as e:
                    st.error(f"Could not load report: {e}")
    with st.expander("Load max-accuracy report by job id", expanded=False):
        if max_accuracy_job_id:
            st.caption(f"Last max-accuracy job id: {max_accuracy_job_id}")
        load_job_id = st.text_input(
            "Max-accuracy job id",
            value=max_accuracy_job_id or "",
            placeholder="Paste job id",
            key="ma_load_job_id",
        )
        if st.button("Load max-accuracy report"):
            if not load_job_id.strip():
                st.warning("Enter a job id.")
            else:
                try:
                    resp = requests.get(f"{BACKEND_URL}/property-hotspots/max-accuracy/report/{load_job_id.strip()}", timeout=30)
                    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    if resp.status_code == 200 and data.get("success") and data.get("report"):
                        st.session_state["max_accuracy_report"] = data["report"]
                        st.success("Loaded max-accuracy report.")
                        max_accuracy_report = data["report"]
                    else:
                        st.error(f"Could not load report: {data.get('error') or resp.text}")
                except Exception as e:
                    st.error(f"Could not load report: {e}")
    if isinstance(max_accuracy_report, dict):
        stand_recs = max_accuracy_report.get("stand_recommendations")
        bedding_zones = max_accuracy_report.get("bedding_zones", [])
        report_inputs = max_accuracy_report.get("inputs") or {}

        # ── Helper: terrain feature badges ──────────────────────────
        def _terrain_badges(rec: dict) -> str:
            """Return HTML badges for dominant terrain features."""
            badges = []
            badge_style = (
                "display:inline-block;padding:2px 8px;border-radius:12px;"
                "font-size:0.78em;font-weight:600;margin-right:4px;margin-bottom:2px;"
            )
            checks = [
                ("bench_score", 0.65, "Bench", "#2563eb", "#dbeafe"),
                ("saddle_score", 0.65, "Saddle", "#7c3aed", "#ede9fe"),
                ("corridor_score", 0.60, "Corridor", "#0891b2", "#cffafe"),
                ("shelter_score", 0.55, "Shelter", "#16a34a", "#dcfce7"),
                ("ridgeline_score", 0.40, "Ridgeline", "#b45309", "#fef3c7"),
                ("drainage_score", 0.40, "Drainage", "#0d9488", "#ccfbf1"),
            ]
            for key, thresh, label, fg, bg in checks:
                val = rec.get(key)
                if isinstance(val, (int, float)) and float(val) >= thresh:
                    badges.append(
                        f'<span style="{badge_style}color:{fg};background:{bg}">'
                        f'{label} {float(val):.0%}</span>'
                    )
            return "".join(badges) if badges else ""

        # ── Helper: score bar ───────────────────────────────────────
        def _score_bar(value: float, max_val: float = 1.0, color: str = "#2563eb") -> str:
            pct = min(100, max(0, value / max_val * 100))
            return (
                f'<div style="background:#e5e7eb;border-radius:6px;height:10px;width:100%">'
                f'<div style="background:{color};border-radius:6px;height:10px;width:{pct:.0f}%"></div>'
                f'</div>'
            )

        # ── Rut Phase / Season Banner ───────────────────────────────
        rut_phase = report_inputs.get("rut_phase", "")
        eff_season = report_inputs.get("effective_season", report_inputs.get("season", ""))
        date_time_str = report_inputs.get("date_time", "")
        hunting_pressure = report_inputs.get("hunting_pressure", "")

        phase_labels = {
            "pre_rut": ("🦌 Pre-Rut", "Scrape checking, short cruising loops", "#f59e0b"),
            "seeking": ("🦌 Seeking Phase", "Bucks ranging widely, checking doe groups", "#ef4444"),
            "peak_rut": ("🔥 Peak Rut", "All-day chasing and breeding — hunt all day", "#dc2626"),
            "post_rut": ("🦌 Post-Rut", "Recovery period, secondary breeding possible", "#8b5cf6"),
            "late_season": ("❄️ Late Season", "Food-focused, short movements", "#3b82f6"),
            "early_season": ("🌿 Early Season", "Pattern feeding, bed-to-feed transitions", "#22c55e"),
        }
        phase_info = phase_labels.get(rut_phase, ("🎯 Active", "", "#6b7280"))

        st.markdown(
            f'<div style="background:linear-gradient(135deg,{phase_info[2]}15,{phase_info[2]}08);'
            f'border-left:4px solid {phase_info[2]};border-radius:8px;padding:12px 16px;margin-bottom:16px">'
            f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">'
            f'<span style="font-size:1.3em;font-weight:700">{phase_info[0]}</span>'
            f'<span style="color:#6b7280;font-size:0.9em">{phase_info[1]}</span>'
            + (f'<span style="margin-left:auto;color:#6b7280;font-size:0.85em">{date_time_str[:16] if date_time_str else ""}</span>' if date_time_str else '')
            + f'</div></div>',
            unsafe_allow_html=True,
        )

        if not (isinstance(stand_recs, list) and stand_recs):
            st.json(max_accuracy_report)
        else:
            # ── Top Stand Hero Card ─────────────────────────────────
            top_rec = stand_recs[0]
            top_score = top_rec.get("final_score", top_rec.get("combined_score", top_rec.get("score", 0)))
            top_score = float(top_score) if isinstance(top_score, (int, float)) else 0
            top_terrain = float(top_rec.get("terrain_norm", 0))
            top_behavior = float(top_rec.get("behavior_score", 0))
            top_lat = top_rec.get("lat")
            top_lon = top_rec.get("lon")

            st.markdown("### 🏆 #1 Recommended Stand")

            # ── Metric Row ──────────────────────────────────────────
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Final Score", f"{top_score:.3f}")
            m2.metric("Terrain", f"{top_terrain:.0%}")
            m3.metric("Behavior", f"{top_behavior:.0%}")
            slope_v = top_rec.get("slope_deg")
            m4.metric("Slope", f"{float(slope_v):.0f}°" if isinstance(slope_v, (int, float)) else "—")
            elev_v = top_rec.get("elevation_m")
            m5.metric("Elevation", f"{float(elev_v):.0f}m" if isinstance(elev_v, (int, float)) else "—")

            # ── Feature Badges + Canopy ─────────────────────────────
            badges_html = _terrain_badges(top_rec)
            canopy_v = top_rec.get("gee_canopy")
            ndvi_v = top_rec.get("gee_ndvi")
            canopy_str = ""
            if isinstance(canopy_v, (int, float)):
                canopy_str += f'<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:0.78em;font-weight:600;color:#15803d;background:#dcfce7;margin-right:4px">🌲 Canopy {float(canopy_v):.0f}%</span>'
            if isinstance(ndvi_v, (int, float)):
                canopy_str += f'<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:0.78em;font-weight:600;color:#15803d;background:#dcfce7;margin-right:4px">NDVI {float(ndvi_v):.2f}</span>'
            if badges_html or canopy_str:
                st.markdown(badges_html + canopy_str, unsafe_allow_html=True)

            # ── "Why this stand" narrative ───────────────────────────
            top_why = top_rec.get("why")
            if top_why:
                st.markdown(
                    f'<div style="background:#fef3c7;border-left:4px solid #f59e0b;border-radius:8px;'
                    f'padding:10px 14px;margin:8px 0;font-size:0.92em;line-height:1.5">'
                    f'<b>💡 Why this stand:</b> {top_why}</div>',
                    unsafe_allow_html=True,
                )

            # ── Bedding Card ─────────────────────────────────────────
            nearest_bed = top_rec.get("nearest_bedding")
            bed_prox = top_rec.get("bedding_proximity_score")
            if isinstance(nearest_bed, dict):
                bd = nearest_bed.get("distance_m", "?")
                bb = nearest_bed.get("bearing_deg", "?")
                compass = ""
                if isinstance(bb, (int, float)):
                    compass = degrees_to_compass(float(bb))
                bed_qual = nearest_bed.get("bedding_quality")
                qual_str = f" · Quality: {float(bed_qual):.0%}" if isinstance(bed_qual, (int, float)) else ""
                bed_lat = nearest_bed.get("lat")
                bed_lon = nearest_bed.get("lon")
                bed_coord_str = f'<div style="color:#6b7280;font-size:0.82em;margin-top:2px">📍 Bedding: {float(bed_lat):.6f}, {float(bed_lon):.6f}</div>' if isinstance(bed_lat, (int, float)) and isinstance(bed_lon, (int, float)) else ''
                st.markdown(
                    f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:12px">'
                    f'<div style="font-weight:600;margin-bottom:4px">🛏️ Nearest Bedding</div>'
                    f'<div style="font-size:1.4em;font-weight:700;color:#16a34a">{bd}m {compass}</div>'
                    f'<div style="color:#6b7280;font-size:0.85em">Bearing: {bb}°{qual_str}'
                    + (f' · Proximity: {float(bed_prox):.2f}' if isinstance(bed_prox, (int, float)) else '')
                    + f'</div>{bed_coord_str}</div>',
                    unsafe_allow_html=True,
                )
                bedding_zones = max_accuracy_report.get("bedding_zones", [])
                if isinstance(bedding_zones, list) and bedding_zones:
                    st.caption(f"🛏️ {len(bedding_zones)} bedding zones identified on property")
            elif isinstance(max_accuracy_report.get("bedding_zones"), list) and max_accuracy_report.get("bedding_zones"):
                st.info(f"🛏️ {len(max_accuracy_report['bedding_zones'])} bedding zones identified on property")

            # ── Coordinates ─────────────────────────────────────────
            if top_lat is not None and top_lon is not None:
                st.caption(f"📍 {float(top_lat):.6f}, {float(top_lon):.6f}")

            st.divider()

            # ── Stand Comparison Table ──────────────────────────────
            st.markdown("### 📊 Stand Comparison")
            num_stands = min(len(stand_recs), 10)

            # Build comparison as columns
            header_cols = st.columns([0.4, 1, 1, 1, 1, 1, 1.2, 1])
            header_labels = ["Rank", "Score", "Terrain", "Behavior", "Slope", "Elev", "Features", "Bed Dist"]
            for col, label in zip(header_cols, header_labels):
                col.markdown(f"**{label}**")

            for i, rec in enumerate(stand_recs[:num_stands]):
                cols = st.columns([0.4, 1, 1, 1, 1, 1, 1.2, 1])
                sc = rec.get("final_score", rec.get("combined_score", rec.get("score", 0)))
                sc = float(sc) if isinstance(sc, (int, float)) else 0
                tr = float(rec.get("terrain_norm", 0))
                bh = float(rec.get("behavior_score", 0))
                sl = rec.get("slope_deg")
                el = rec.get("elevation_m")
                nb = rec.get("nearest_bedding")
                bd = f'{nb["distance_m"]}m' if isinstance(nb, dict) and nb.get("distance_m") else "—"

                rank_style = "font-weight:700;" + ("color:#dc2626;" if i == 0 else "color:#6b7280;")
                cols[0].markdown(f'<span style="{rank_style}">#{i+1}</span>', unsafe_allow_html=True)
                cols[1].markdown(f"{sc:.3f}")
                cols[2].markdown(_score_bar(tr, 1.0, "#2563eb") + f'<span style="font-size:0.8em">{tr:.0%}</span>', unsafe_allow_html=True)
                cols[3].markdown(_score_bar(bh, 1.0, "#7c3aed") + f'<span style="font-size:0.8em">{bh:.0%}</span>', unsafe_allow_html=True)
                cols[4].markdown(f"{float(sl):.0f}°" if isinstance(sl, (int, float)) else "—")
                cols[5].markdown(f"{float(el):.0f}m" if isinstance(el, (int, float)) else "—")
                cols[6].markdown(_terrain_badges(rec) or "—", unsafe_allow_html=True)
                cols[7].markdown(bd)

            # ── Stand Detail Inspector ──────────────────────────────
            st.divider()
            st.markdown("### 🔍 Stand Detail Inspector")
            options = []
            for idx, rec in enumerate(stand_recs, start=1):
                sc = rec.get("final_score", rec.get("combined_score", rec.get("score")))
                sc_str = f"score {float(sc):.3f}" if isinstance(sc, (int, float)) else ""
                nb = rec.get("nearest_bedding")
                bd_str = f"bed:{nb['distance_m']}m" if isinstance(nb, dict) and nb.get("distance_m") else ""
                badges = []
                for key, thresh, label in [("bench_score", 0.65, "bench"), ("saddle_score", 0.65, "saddle"),
                                            ("corridor_score", 0.60, "corridor"), ("ridgeline_score", 0.40, "ridge"),
                                            ("drainage_score", 0.40, "drainage")]:
                    v = rec.get(key)
                    if isinstance(v, (int, float)) and float(v) >= thresh:
                        badges.append(label)
                feature_str = "+".join(badges) if badges else ""
                parts = [f"#{idx}", sc_str, feature_str, bd_str]
                options.append(" · ".join(p for p in parts if p))

            selected_idx = st.selectbox(
                "Select a stand to inspect",
                options=list(range(len(options))),
                format_func=lambda i: options[i],
                key="ma_selected_stand",
            )
            sel_rec = stand_recs[int(selected_idx)]

            # ── "Why this stand" for selected ───────────────────────
            sel_why = sel_rec.get("why")
            if sel_why:
                st.markdown(
                    f'<div style="background:#fef3c7;border-left:4px solid #f59e0b;border-radius:8px;'
                    f'padding:10px 14px;margin:8px 0;font-size:0.92em;line-height:1.5">'
                    f'<b>💡 Why this stand:</b> {sel_why}</div>',
                    unsafe_allow_html=True,
                )

            # ── Detail Cards ────────────────────────────────────────
            d1, d2, d3 = st.columns(3)
            with d1:
                st.markdown("**Terrain Scores**")
                for label, key in [("Bench", "bench_score"), ("Saddle", "saddle_score"),
                                    ("Corridor", "corridor_score"), ("Shelter", "shelter_score"),
                                    ("Aspect", "aspect_score"), ("Ridgeline", "ridgeline_score"),
                                    ("Drainage", "drainage_score")]:
                    v = sel_rec.get(key)
                    if isinstance(v, (int, float)):
                        st.markdown(f"{label}: {_score_bar(float(v))} <span style='font-size:0.85em'>{float(v):.2f}</span>", unsafe_allow_html=True)
            with d2:
                st.markdown("**Terrain Metrics**")
                for label, key, fmt, suffix in [("Slope", "slope_deg", ".1f", "°"), ("Elevation", "elevation_m", ".0f", " m"),
                                         ("TPI (small)", "tpi_small", ".2f", ""), ("TPI (large)", "tpi_large", ".2f", ""),
                                         ("Relief", "relief_small", ".1f", ""), ("Curvature", "curvature", ".3f", ""),
                                         ("Roughness", "roughness", ".1f", "")]:
                    v = sel_rec.get(key)
                    if isinstance(v, (int, float)):
                        st.markdown(f"**{label}:** {float(v):{fmt}}{suffix}")
            with d3:
                st.markdown("**Scoring Breakdown**")
                for label, key in [("Final Score", "final_score"), ("Combined", "combined_score"),
                                    ("Terrain Norm", "terrain_norm"), ("Behavior", "behavior_score"),
                                    ("Bedding Proximity", "bedding_proximity_score"),
                                    ("Corridor Proximity", "corridor_proximity_score")]:
                    v = sel_rec.get(key)
                    if isinstance(v, (int, float)):
                        st.markdown(f"**{label}:** {float(v):.3f}")
                canopy_v = sel_rec.get("gee_canopy")
                ndvi_v = sel_rec.get("gee_ndvi")
                if isinstance(canopy_v, (int, float)):
                    st.markdown(f"**Canopy:** {float(canopy_v):.0f}%")
                if isinstance(ndvi_v, (int, float)):
                    st.markdown(f"**NDVI:** {float(ndvi_v):.2f}")
                quadrant = sel_rec.get("quadrant")
                if quadrant:
                    st.markdown(f"**Quadrant:** {quadrant}")

            # Bedding detail for selected stand
            sel_nb = sel_rec.get("nearest_bedding")
            if isinstance(sel_nb, dict):
                bd = sel_nb.get("distance_m", "?")
                bb = sel_nb.get("bearing_deg")
                compass = degrees_to_compass(float(bb)) if isinstance(bb, (int, float)) else ""
                bed_qual = sel_nb.get("bedding_quality")
                qual_str = f" · Quality: {float(bed_qual):.0%}" if isinstance(bed_qual, (int, float)) else ""
                bed_lat = sel_nb.get("lat")
                bed_lon = sel_nb.get("lon")
                bed_coord_str = f'<br><span style="font-size:0.82em;color:#6b7280">📍 Bedding: {float(bed_lat):.6f}, {float(bed_lon):.6f}</span>' if isinstance(bed_lat, (int, float)) and isinstance(bed_lon, (int, float)) else ''
                st.markdown(
                    f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:10px">'
                    f'<b>🛏️ Nearest Bedding:</b> {bd}m {compass}'
                    f'<br><span style="font-size:0.85em;color:#6b7280">Bearing: {bb}°{qual_str}</span>'
                    f'{bed_coord_str}'
                    f'</div>', unsafe_allow_html=True,
                )

            sel_lat = sel_rec.get("lat")
            sel_lon = sel_rec.get("lon")
            if sel_lat is not None and sel_lon is not None:
                st.caption(f"📍 {float(sel_lat):.6f}, {float(sel_lon):.6f}")

            # ── Map ─────────────────────────────────────────────────
            st.divider()
            st.markdown("### 🗺️ Max Accuracy Map")

            show_bedding_zones = st.checkbox("Show bedding zones", value=True, key="ma_show_bedding")

            try:
                lat_center = sum(float(s.get("lat", 0.0)) for s in stand_recs) / max(1, len(stand_recs))
                lon_center = sum(float(s.get("lon", 0.0)) for s in stand_recs) / max(1, len(stand_recs))
                max_map = folium.Map(location=[lat_center, lon_center], zoom_start=16, tiles="OpenStreetMap")
                bounds_lats = [float(s.get("lat", 0.0)) for s in stand_recs if s.get("lat") is not None]
                bounds_lons = [float(s.get("lon", 0.0)) for s in stand_recs if s.get("lon") is not None]

                # Property boundary
                corners = report_inputs.get("corners")
                if isinstance(corners, list) and corners:
                    poly_points = [(c.get("lat"), c.get("lon")) for c in corners if c.get("lat") is not None and c.get("lon") is not None]
                    if poly_points:
                        folium.Polygon(locations=poly_points, color="#3b82f6", weight=2, fill=True, fill_color="#3b82f6", fill_opacity=0.04, tooltip="Property boundary").add_to(max_map)
                        bounds_lats.extend([p[0] for p in poly_points])
                        bounds_lons.extend([p[1] for p in poly_points])

                # Bedding zones with feature groups
                if show_bedding_zones and isinstance(bedding_zones, list):
                    bedding_fg = folium.FeatureGroup(name="🛏️ Bedding Zones")
                    sorted_bedding = sorted(bedding_zones, key=lambda b: b.get('bedding_quality', b.get('criteria_met', 0)), reverse=True)

                    for idx, bz in enumerate(sorted_bedding[:8]):
                        bz_lat, bz_lon = bz.get("lat"), bz.get("lon")
                        if bz_lat is None or bz_lon is None:
                            continue
                        shelter = float(bz.get("shelter_score", 0))
                        bench = float(bz.get("bench_score", 0))
                        slope = bz.get("slope_deg")
                        aspect = bz.get("aspect_deg")
                        elev = bz.get("elevation_m")
                        roughness = bz.get("roughness", 0)
                        quality = bz.get("bedding_quality", 0)
                        ridge = bz.get("ridgeline_score", 0)
                        popup_html = (
                            f'<div style="min-width:180px">'
                            f'<b>🛏️ Prime Bedding #{idx+1}</b><br>'
                            f'<b>Quality:</b> {float(quality):.0%}<br>'
                            f'<b>Bench:</b> {bench:.0%} · <b>Shelter:</b> {shelter:.0%}<br>'
                            + (f'<b>Slope:</b> {float(slope):.1f}° ' if isinstance(slope, (int, float)) else '')
                            + (f'<b>Elev:</b> {float(elev):.0f}m<br>' if isinstance(elev, (int, float)) else '')
                            + f'<b>Roughness:</b> {float(roughness):.1f}'
                            + (f' · <b>Ridge:</b> {float(ridge):.0%}' if isinstance(ridge, (int, float)) and float(ridge) > 0.1 else '')
                            + f'<br><span style="color:#6b7280;font-size:0.85em">📍 {float(bz_lat):.6f}, {float(bz_lon):.6f}</span>'
                            + f'<br></div>'
                        )
                        folium.CircleMarker(
                            [bz_lat, bz_lon], radius=12,
                            color="#15803d", fill=True, fill_color="#22c55e", fill_opacity=0.65, weight=2,
                            popup=folium.Popup(popup_html, max_width=220),
                            tooltip=f"🛏️ Bedding #{idx+1} · Quality: {float(quality):.0%} · {float(bz_lat):.6f}, {float(bz_lon):.6f}",
                        ).add_to(bedding_fg)

                    for bz in sorted_bedding[8:60]:
                        bz_lat, bz_lon = bz.get("lat"), bz.get("lon")
                        if bz_lat is None or bz_lon is None:
                            continue
                        quality = bz.get("bedding_quality", 0)
                        folium.CircleMarker(
                            [bz_lat, bz_lon], radius=5,
                            color="#f97316", fill=True, fill_color="#fb923c", fill_opacity=0.4, weight=1,
                            tooltip=f"🛏️ Bedding · Quality: {float(quality):.0%} · {float(bz_lat):.6f}, {float(bz_lon):.6f}",
                        ).add_to(bedding_fg)

                    bedding_fg.add_to(max_map)

                # ── Movement Corridors (M2) ──────────────────────────
                corridor_data = max_accuracy_report.get("corridors")
                show_corridors = st.checkbox("Show movement corridors", value=True, key="ma_show_corridors") if corridor_data else False
                if show_corridors and isinstance(corridor_data, dict):
                    corridor_fg = folium.FeatureGroup(name="🦌 Movement Corridors")
                    polylines = corridor_data.get("polylines", [])
                    num_paths = len(polylines)
                    for idx, pl in enumerate(polylines):
                        if not pl or len(pl) < 2:
                            continue
                        # Color gradient: primary corridors are darker
                        opacity = max(0.4, 0.85 - idx * 0.03)
                        weight = max(2, 5 - idx * 0.2)
                        folium.PolyLine(
                            pl, color="#dc2626", weight=weight, opacity=opacity,
                            dash_array="6 4",
                            tooltip=f"🦌 Corridor #{idx + 1} of {num_paths}",
                        ).add_to(corridor_fg)
                    # Corridor nodes
                    corridor_nodes = corridor_data.get("nodes", [])
                    for cn in corridor_nodes:
                        cn_lat, cn_lon = cn.get("lat"), cn.get("lon")
                        cn_kind = cn.get("kind", "")
                        cn_name = cn.get("name", "")
                        if cn_lat is None or cn_lon is None:
                            continue
                        if cn_kind == "evidence":
                            folium.CircleMarker(
                                [cn_lat, cn_lon], radius=8,
                                color="#b91c1c", fill=True, fill_color="#ef4444", fill_opacity=0.7, weight=2,
                                tooltip=f"📌 Evidence: {cn_name}",
                            ).add_to(corridor_fg)
                    corridor_fg.add_to(max_map)

                    # Corridor summary banner
                    coverage = corridor_data.get("corridor_coverage_pct", 0)
                    n_paths = corridor_data.get("num_paths", 0)
                    n_nodes = corridor_data.get("num_nodes", 0)
                    st.markdown(
                        f'<div style="background:linear-gradient(135deg,#dc262615,#dc262608);'
                        f'border-left:4px solid #dc2626;border-radius:8px;padding:10px 14px;margin:8px 0">'
                        f'<span style="font-weight:700">🦌 Movement Corridors</span> · '
                        f'{n_paths} paths · {n_nodes} nodes · {coverage:.1f}% corridor coverage'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                # Stand markers — color-coded by rank
                stands_fg = folium.FeatureGroup(name="🎯 Stand Sites")
                stand_colors = ["red", "blue", "purple", "darkred", "orange", "darkblue", "cadetblue", "darkgreen", "gray", "lightred"]
                stand_icons = ["star", "certificate", "bookmark", "flag", "map-pin", "map-pin", "map-pin", "map-pin", "map-pin", "map-pin"]

                for idx, rec in enumerate(stand_recs[:10]):
                    lat, lon = rec.get("lat"), rec.get("lon")
                    if lat is None or lon is None:
                        continue
                    sc = rec.get("final_score", rec.get("combined_score", rec.get("score", 0)))
                    sc = float(sc) if isinstance(sc, (int, float)) else 0
                    tr = float(rec.get("terrain_norm", 0))
                    bh = float(rec.get("behavior_score", 0))
                    nb = rec.get("nearest_bedding")
                    huntable = rec.get("huntable_winds", [])

                    # Rich popup
                    popup_parts = [
                        f'<div style="min-width:220px;font-family:sans-serif">',
                        f'<div style="font-size:1.1em;font-weight:700;margin-bottom:6px">🎯 Stand #{idx+1}</div>',
                        f'<b>Score:</b> {sc:.3f} (Terrain: {tr:.0%} · Behavior: {bh:.0%})<br>',
                    ]
                    slope_v = rec.get("slope_deg")
                    elev_v = rec.get("elevation_m")
                    if isinstance(slope_v, (int, float)):
                        popup_parts.append(f'<b>Slope:</b> {float(slope_v):.1f}° ')
                    if isinstance(elev_v, (int, float)):
                        popup_parts.append(f'<b>Elev:</b> {float(elev_v):.0f}m<br>')
                    # Terrain features
                    feat_badges = _terrain_badges(rec)
                    if feat_badges:
                        popup_parts.append(f'<div style="margin:4px 0">{feat_badges}</div>')
                    # Canopy
                    canopy_v = rec.get("gee_canopy")
                    if isinstance(canopy_v, (int, float)):
                        popup_parts.append(f'<b>🌲 Canopy:</b> {float(canopy_v):.0f}%<br>')
                    # Bedding
                    if isinstance(nb, dict) and nb.get("distance_m"):
                        bd_compass = degrees_to_compass(float(nb["bearing_deg"])) if isinstance(nb.get("bearing_deg"), (int, float)) else ""
                        popup_parts.append(f'<b>🛏️ Bedding:</b> {nb["distance_m"]}m {bd_compass}<br>')
                        if isinstance(nb.get("lat"), (int, float)) and isinstance(nb.get("lon"), (int, float)):
                            popup_parts.append(f'<span style="font-size:0.8em;color:#6b7280">📍 Bed: {float(nb["lat"]):.6f}, {float(nb["lon"]):.6f}</span><br>')
                    popup_parts.append(f'<div style="color:#9ca3af;font-size:0.8em;margin-top:4px">{float(lat):.6f}, {float(lon):.6f}</div>')
                    popup_parts.append('</div>')

                    color = stand_colors[idx] if idx < len(stand_colors) else "gray"
                    icon = stand_icons[idx] if idx < len(stand_icons) else "map-pin"

                    folium.Marker(
                        [lat, lon],
                        popup=folium.Popup("".join(popup_parts), max_width=300),
                        tooltip=f"#{idx+1} · {sc:.3f}",
                        icon=folium.Icon(color=color, icon=icon, prefix="fa"),
                    ).add_to(stands_fg)

                    # Line from stand to nearest bedding
                    if isinstance(nb, dict) and nb.get("lat") and nb.get("lon"):
                        folium.PolyLine(
                            [[lat, lon], [nb["lat"], nb["lon"]]],
                            color="#f97316", weight=3, dash_array="8 5", opacity=0.85,
                            tooltip=f"To bedding: {nb.get('distance_m', '?')}m · {float(nb['lat']):.6f}, {float(nb['lon']):.6f}",
                        ).add_to(stands_fg)

                stands_fg.add_to(max_map)

                # Layer control
                folium.LayerControl(collapsed=False).add_to(max_map)

                # Legend
                legend_html = (
                    '<div style="position:fixed;bottom:30px;left:10px;z-index:1000;background:white;'
                    'padding:10px 14px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,.2);font-size:0.82em;line-height:1.5">'
                    '<b>Legend</b><br>'
                    '⭐ <span style="color:#dc2626">#1 Stand</span><br>'
                    '🏷️ <span style="color:#3b82f6">#2 Stand</span><br>'
                    '📌 <span style="color:#7c3aed">#3+ Stands</span><br>'
                    '🟢 Prime Bedding<br>'
                    '🟠 Secondary Bedding<br>'
                    '<span style="color:#dc2626">━━</span> Movement Corridor<br>'
                    '--- Stand→Bed link'
                    '</div>'
                )
                max_map.get_root().html.add_child(folium.Element(legend_html))

                if bounds_lats and bounds_lons:
                    max_map.fit_bounds([[min(bounds_lats), min(bounds_lons)], [max(bounds_lats), max(bounds_lons)]])
                st_folium(
                    max_map,
                    key="max_accuracy_map",
                    height=600,
                    width=None,
                    returned_objects=[],
                )

            except Exception as e:
                st.warning(f"Could not render max-accuracy map: {e}")

            # ── Bedding Zone Summary ────────────────────────────────
            if isinstance(bedding_zones, list) and bedding_zones:
                with st.expander(f"🛏️ Bedding Zones ({len(bedding_zones)} identified)", expanded=False):
                    sorted_bz = sorted(bedding_zones, key=lambda b: b.get("bedding_quality", b.get("criteria_met", 0)), reverse=True)
                    for i, bz in enumerate(sorted_bz[:20]):
                        quality = float(bz.get("bedding_quality", 0))
                        shelter = float(bz.get("shelter_score", 0))
                        bench = float(bz.get("bench_score", 0))
                        elev = bz.get("elevation_m", 0)
                        slope = bz.get("slope_deg", 0)
                        roughness = float(bz.get("roughness", 0))
                        bz_lat = bz.get("lat", 0)
                        bz_lon = bz.get("lon", 0)
                        st.markdown(
                            f"**#{i+1}** Quality: {quality:.0%} · Bench: {bench:.0%} · Shelter: {shelter:.0%} · "
                            f"Slope: {float(slope):.1f}° · Rough: {roughness:.1f} · Elev: {float(elev):.0f}m · "
                            f"📍 {float(bz_lat):.5f}, {float(bz_lon):.5f}"
                        )

            # ── Raw Data Expander ───────────────────────────────────
            with st.expander("📋 Full Report (raw JSON)", expanded=False):
                st.json(max_accuracy_report)

# ==========================================
# TAB 2: SCOUTING DATA
# ==========================================
with tab_scout:
    st.header("🔍 Real-Time Scouting Data Entry")
    
    # Get observation types from backend
    observation_types = get_observation_types()
    
    if not observation_types:
        st.error("Unable to load observation types. Please check backend connection.")
    else:
        # Create two modes: map entry and manual entry
        entry_mode = st.radio("📝 Entry Mode", ["🗺️ Map-Based Entry", "✍️ Manual Entry"], horizontal=True)
        
        if entry_mode == "🗺️ Map-Based Entry":
            st.markdown("### 🗺️ Click on the map to add scouting observations")
            
            # Map for scouting entry - using same map type as hunting predictions
            map_type_for_scout = getattr(st.session_state, 'map_type', 'Topographic (USGS)')  # Fallback to USGS Topo if not set
            scout_map = create_map(st.session_state.hunt_location, st.session_state.map_zoom, map_type_for_scout)
            
            # Load and display existing observations
            existing_obs = get_scouting_observations(
                st.session_state.hunt_location[0],
                st.session_state.hunt_location[1],
                radius_miles=2,
            )
            
            # Add existing observation markers
            for obs in existing_obs:
                color_map = {
                    "Fresh Scrape": "red",
                    "Rub Line": "orange", 
                    "Bedding Area": "green",
                    "Trail Camera": "blue",
                    "Trail Camera Setup": "blue",
                    "Deer Tracks/Trail": "purple",
                    "Feeding Sign": "lightgreen",
                    "Scat/Droppings": "brown",
                    "Other Sign": "gray"
                }
                
                color = color_map.get(obs.get('observation_type'), 'gray')
                
                folium.Marker(
                    [obs['lat'], obs['lon']],
                    popup=f"{obs['observation_type']}<br>Confidence: {obs['confidence']}/10<br>{obs.get('notes', '')[:50]}...",
                    icon=folium.Icon(color=color, icon='eye')
                ).add_to(scout_map)
            
            # Display scouting map
            scout_map_data = st_folium(scout_map, key="scout_map", width=700, height=500)
            
            # Handle map clicks for new observations
            if scout_map_data['last_clicked']:
                clicked_lat = scout_map_data['last_clicked']['lat']
                clicked_lng = scout_map_data['last_clicked']['lng']
                
                st.success(f"📍 **Selected Location:** {clicked_lat:.6f}, {clicked_lng:.6f}")
                
                # Observation entry form
                with st.form("scouting_observation_form"):
                    st.markdown("### 📝 New Observation Details")
                    
                    # Observation type
                    obs_type_names = [ot['type'] for ot in observation_types]
                    selected_obs_type = st.selectbox("🔍 Observation Type", obs_type_names, key="form_obs_type")
                    
                    # Find selected observation type data
                    selected_type_data = next((ot for ot in observation_types if ot['type'] == selected_obs_type), {})
                    selected_enum = selected_type_data.get('enum_name', '')
                    
                    # Confidence rating
                    confidence = st.slider("📊 Confidence Level", 1, 10, 7, 
                                         help="How certain are you about this observation?",
                                         key="form_confidence")
                    
                    # Notes
                    notes = st.text_area("📝 Notes", placeholder="Describe what you observed...", key="form_notes")
                    
                    # Type-specific details
                    details = {}
                    
                    if selected_enum == "FRESH_SCRAPE":
                        st.markdown("#### 🦌 Scrape Details")
                        details = {
                            "size": st.selectbox("Size", ["Small", "Medium", "Large", "Huge"], key="scrape_size"),
                            "freshness": st.selectbox("Freshness", ["Old", "Recent", "Fresh", "Very Fresh"], key="scrape_freshness"),
                            "licking_branch": st.checkbox("Active licking branch present", key="scrape_licking"),
                            "multiple_scrapes": st.checkbox("Multiple scrapes in area", key="scrape_multiple")
                        }
                    
                    elif selected_enum == "RUB_LINE":
                        st.markdown("#### 🌳 Rub Details")
                        details = {
                            "tree_diameter_inches": st.number_input("Tree Diameter (inches)", 1, 36, 6, key="rub_diameter"),
                            "rub_height_inches": st.number_input("Rub Height (inches)", 12, 72, 36, key="rub_height"),
                            "direction": st.selectbox("Primary Direction", 
                                                    ["North", "South", "East", "West", "Northeast", "Northwest", "Southeast", "Southwest", "Multiple"],
                                                    key="rub_direction"),
                            "tree_species": st.text_input("Tree Species (optional)", key="rub_species"),
                            "multiple_rubs": st.checkbox("Multiple rubs in line", key="rub_multiple")
                        }
                    
                    elif selected_enum == "BEDDING_AREA":
                        st.markdown("#### 🛏️ Bedding Details")
                        details = {
                            "number_of_beds": st.number_input("Number of Beds", 1, 20, 1, key="bed_number"),
                            "bed_size": st.selectbox("Bed Size", ["Small (Doe/Fawn)", "Medium (Young Buck)", "Large (Mature Buck)", "Multiple Sizes"], key="bed_size"),
                            "cover_type": st.selectbox("Cover Type", ["Thick Brush", "Conifer Stand", "Creek Bottom", "Ridge Top", "Field Edge"], key="bed_cover"),
                            "thermal_advantage": st.checkbox("Good thermal cover", key="bed_thermal")
                        }
                    
                    elif selected_enum == "TRAIL_CAMERA":
                        st.markdown("#### 📸 Camera Details")
                        cam_col1, cam_col2 = st.columns(2)
                        with cam_col1:
                            camera_brand = st.text_input("Camera Brand/Model (optional)", key="map_camera_brand")
                            camera_direction = st.selectbox(
                                "Camera Facing",
                                [
                                    "North", "South", "East", "West",
                                    "Northeast", "Northwest", "Southeast", "Southwest"
                                ],
                                key="map_camera_direction"
                            )
                            trail_width_feet = st.number_input("Trail Width (feet)", min_value=1, max_value=30, value=3, key="map_camera_trail_width")
                        with cam_col2:
                            include_setup_date = st.checkbox("Include camera setup date", value=True, key="map_camera_use_setup_date")
                            setup_date_value = None
                            if include_setup_date:
                                setup_date_value = st.date_input(
                                    "Camera Setup Date",
                                    value=datetime.now().date(),
                                    key="map_camera_setup_date"
                                )
                            setup_height_feet = st.number_input("Camera Height (feet)", min_value=1, max_value=20, value=8, key="map_camera_height")
                            detection_zone = st.selectbox(
                                "Detection Zone",
                                ["Narrow Trail", "Wide Trail", "Intersection", "Food Plot Edge", "Mineral Site", "Mock Scrape"],
                                key="map_camera_detection_zone"
                            )
                        peak_activity = st.text_input("Peak Activity Window (optional)", key="map_camera_peak_activity")
                        mature_buck_seen = st.checkbox("Captured a mature buck here recently?", key="map_camera_mature_flag")
                        mature_sighting_iso = None
                        mature_notes = None
                        if mature_buck_seen:
                            sight_col1, sight_col2 = st.columns(2)
                            with sight_col1:
                                sighting_date = st.date_input(
                                    "Mature Buck Capture Date",
                                    value=datetime.now().date(),
                                    key="map_camera_sighting_date"
                                )
                            with sight_col2:
                                default_time = datetime.now().replace(second=0, microsecond=0).time()
                                sighting_time = st.time_input(
                                    "Capture Time",
                                    value=default_time,
                                    key="map_camera_sighting_time"
                                )
                            mature_notes = st.text_area(
                                "Mature Buck Notes (optional)",
                                placeholder="Antler size, direction of travel, behavior...",
                                key="map_camera_sighting_notes"
                            )
                            mature_sighting_iso = datetime.combine(sighting_date, sighting_time).isoformat()

                        details = {
                            "camera_brand": camera_brand or None,
                            "camera_direction": camera_direction or None,
                            "trail_width_feet": float(trail_width_feet) if trail_width_feet else None,
                            "setup_height_feet": float(setup_height_feet) if setup_height_feet else None,
                            "detection_zone": detection_zone or None,
                            "peak_activity_time": peak_activity or None,
                            "mature_buck_seen": mature_buck_seen,
                            "mature_buck_seen_at": mature_sighting_iso,
                            "mature_buck_notes": mature_notes or None
                        }
                        if include_setup_date and setup_date_value:
                            details["setup_date"] = datetime.combine(setup_date_value, datetime.min.time()).isoformat()

                    elif selected_enum == "DEER_TRACKS":
                        st.markdown("#### 🐾 Track Details")
                        details = {
                            "track_size": st.selectbox("Track Size", ["Small (Doe/Fawn)", "Medium (Young Buck)", "Large (Mature Buck)", "Multiple Sizes"], key="track_size"),
                            "trail_width_inches": st.number_input("Trail Width (inches)", 6, 24, 12, key="track_width"),
                            "usage_level": st.selectbox("Usage Level", ["Light", "Moderate", "Heavy", "Highway"], key="track_usage"),
                            "direction": st.selectbox("Primary Direction", 
                                                    ["North", "South", "East", "West", "Northeast", "Northwest", "Southeast", "Southwest", "Multiple"],
                                                    key="track_direction")
                        }
                    
                    # Submit button
                    submitted = st.form_submit_button("✅ Add Observation", type="primary")
                    
                    if submitted:
                        # Prepare observation data
                        observation_data = {
                            "lat": clicked_lat,
                            "lon": clicked_lng,
                            "observation_type": selected_obs_type,
                            "confidence": confidence,
                            "notes": notes
                        }
                        
                        # Add type-specific details
                        if selected_enum == "FRESH_SCRAPE":
                            observation_data["scrape_details"] = details
                        elif selected_enum == "RUB_LINE":
                            observation_data["rub_details"] = details
                        elif selected_enum == "BEDDING_AREA":
                            observation_data["bedding_details"] = details
                        elif selected_enum == "TRAIL_CAMERA":
                            observation_data["camera_details"] = details
                        elif selected_enum == "DEER_TRACKS":
                            observation_data["tracks_details"] = details
                        
                        # Submit to backend
                        result = add_scouting_observation(observation_data)
                        
                        if result:
                            st.success(f"✅ **Observation Added Successfully!**")
                            st.info(f"**ID:** {result.get('observation_id')}")
                            st.info(f"**Confidence Boost:** +{result.get('confidence_boost', 0):.1f}")
                            st.balloons()
                            
                            # Clear the form by rerunning
                            st.rerun()
        
        else:
            # Manual entry mode
            st.markdown("### ✍️ Manual Coordinate Entry")
            
            with st.form("manual_observation_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    manual_lat = st.number_input("Latitude", value=st.session_state.hunt_location[0], format="%.6f")
                    manual_lon = st.number_input("Longitude", value=st.session_state.hunt_location[1], format="%.6f")
                
                with col2:
                    obs_type_names = [ot['type'] for ot in observation_types]
                    selected_obs_type = st.selectbox("🔍 Observation Type", obs_type_names)
                    confidence = st.slider("📊 Confidence Level", 1, 10, 7)
                    selected_type_data = next((ot for ot in observation_types if ot['type'] == selected_obs_type), {})
                    selected_enum = selected_type_data.get('enum_name', '')
                
                notes = st.text_area("📝 Notes", placeholder="Describe what you observed...")

                camera_details_manual: Dict[str, Any] = {}
                if selected_enum == "TRAIL_CAMERA":
                    st.markdown("#### 📸 Camera Details")
                    manual_cam_col1, manual_cam_col2 = st.columns(2)
                    with manual_cam_col1:
                        manual_camera_brand = st.text_input("Camera Brand/Model (optional)", key="manual_camera_brand")
                        manual_camera_direction = st.selectbox(
                            "Camera Facing",
                            [
                                "North", "South", "East", "West",
                                "Northeast", "Northwest", "Southeast", "Southwest"
                            ],
                            key="manual_camera_direction"
                        )
                    with manual_cam_col2:
                        manual_include_setup = st.checkbox("Include camera setup date", value=True, key="manual_camera_use_setup")
                        manual_setup_date = None
                        if manual_include_setup:
                            manual_setup_date = st.date_input(
                                "Camera Setup Date",
                                value=datetime.now().date(),
                                key="manual_camera_setup_date"
                            )
                    manual_peak_activity = st.text_input("Peak Activity Window (optional)", key="manual_camera_peak_activity")
                    manual_trail_width = st.number_input("Trail Width (feet)", min_value=1, max_value=30, value=3, key="manual_camera_trail_width")
                    manual_setup_height = st.number_input("Camera Height (feet)", min_value=1, max_value=20, value=8, key="manual_camera_height")
                    manual_detection_zone = st.selectbox(
                        "Detection Zone",
                        ["Narrow Trail", "Wide Trail", "Intersection", "Food Plot Edge", "Mineral Site", "Mock Scrape"],
                        key="manual_camera_detection_zone"
                    )
                    manual_mature_buck_seen = st.checkbox("Captured a mature buck here recently?", key="manual_camera_mature_flag")
                    manual_mature_iso = None
                    manual_mature_notes = None
                    if manual_mature_buck_seen:
                        manual_sighting_col1, manual_sighting_col2 = st.columns(2)
                        with manual_sighting_col1:
                            manual_sighting_date = st.date_input(
                                "Mature Buck Capture Date",
                                value=datetime.now().date(),
                                key="manual_camera_sighting_date"
                            )
                        with manual_sighting_col2:
                            manual_default_time = datetime.now().replace(second=0, microsecond=0).time()
                            manual_sighting_time = st.time_input(
                                "Capture Time",
                                value=manual_default_time,
                                key="manual_camera_sighting_time"
                            )
                        manual_mature_notes = st.text_area(
                            "Mature Buck Notes (optional)",
                            placeholder="Antler size, behavior, direction...",
                            key="manual_camera_sighting_notes"
                        )
                        manual_mature_iso = datetime.combine(manual_sighting_date, manual_sighting_time).isoformat()

                    camera_details_manual = {
                        "camera_brand": manual_camera_brand or None,
                        "camera_direction": manual_camera_direction or None,
                        "peak_activity_time": manual_peak_activity or None,
                        "trail_width_feet": float(manual_trail_width) if manual_trail_width else None,
                        "setup_height_feet": float(manual_setup_height) if manual_setup_height else None,
                        "detection_zone": manual_detection_zone or None,
                        "mature_buck_seen": manual_mature_buck_seen,
                        "mature_buck_seen_at": manual_mature_iso,
                        "mature_buck_notes": manual_mature_notes or None
                    }
                    if manual_include_setup and manual_setup_date:
                        camera_details_manual["setup_date"] = datetime.combine(manual_setup_date, datetime.min.time()).isoformat()
                
                submitted = st.form_submit_button("✅ Add Observation", type="primary")
                
                if submitted:
                    observation_data = {
                        "lat": manual_lat,
                        "lon": manual_lon,
                        "observation_type": selected_obs_type,
                        "confidence": confidence,
                        "notes": notes
                    }

                    if camera_details_manual:
                        observation_data["camera_details"] = camera_details_manual
                    
                    result = add_scouting_observation(observation_data)
                    
                    if result:
                        st.success(f"✅ **Observation Added Successfully!**")
                        st.info(f"**ID:** {result.get('observation_id')}")

# ==========================================
# TAB 3: ANALYTICS
# ==========================================
with tab_analytics:
    st.header("📊 Scouting Analytics")
    
    # Analytics area selection
    st.markdown("### 📍 Analysis Area")
    
    col1, col2 = st.columns(2)
    with col1:
        analysis_lat = st.number_input("Center Latitude", value=st.session_state.hunt_location[0], format="%.6f")
        analysis_lon = st.number_input("Center Longitude", value=st.session_state.hunt_location[1], format="%.6f")
    
    with col2:
        analysis_radius = st.slider("Analysis Radius (miles)", 1, 10, 5)
    
    if st.button("🔍 Generate Analytics", type="primary"):
        with st.spinner("📊 Analyzing scouting data..."):
            analytics = get_scouting_analytics(analysis_lat, analysis_lon, analysis_radius)
            
            if analytics:
                # Basic stats
                basic_stats = analytics.get('basic_analytics', {})
                
                st.markdown("## 📈 **Area Overview**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_obs = basic_stats.get('total_observations', 0)
                    st.metric("📝 Total Observations", total_obs)
                
                with col2:
                    avg_confidence = basic_stats.get('average_confidence', 0)
                    st.metric("📊 Average Confidence", f"{avg_confidence:.1f}/10")
                
                with col3:
                    obs_by_type = basic_stats.get('observations_by_type', {})
                    most_common = max(obs_by_type.items(), key=lambda x: x[1]) if obs_by_type else ("None", 0)
                    st.metric("🔍 Most Common", most_common[0])
                
                with col4:
                    mature_indicators = basic_stats.get('mature_buck_indicators', 0)
                    st.metric("🦌 Mature Buck Signs", mature_indicators)
                
                # Observation breakdown
                if obs_by_type:
                    st.markdown("## 📋 **Observation Breakdown**")
                    
                    for obs_type, count in obs_by_type.items():
                        percentage = (count / total_obs * 100) if total_obs > 0 else 0
                        st.markdown(f"**{obs_type}:** {count} observations ({percentage:.1f}%)")
                
                # Hotspots
                hotspots = analytics.get('hotspots', [])
                if hotspots:
                    st.markdown("## 🔥 **Activity Hotspots**")
                    
                    for i, hotspot in enumerate(hotspots, 1):
                        with st.expander(f"🎯 Hotspot #{i} - {hotspot.get('observation_count', 0)} observations"):
                            st.markdown(f"**📍 Center:** {hotspot.get('center_lat', 0):.6f}, {hotspot.get('center_lon', 0):.6f}")
                            st.markdown(f"**📊 Confidence Score:** {hotspot.get('avg_confidence', 0):.1f}/10")
                            st.markdown(f"**🔍 Dominant Type:** {hotspot.get('dominant_type', 'Mixed')}")
                
                # Recent activity
                recent_obs = analytics.get('recent_observations', [])
                if recent_obs:
                    st.markdown("## ⏰ **Recent Activity**")
                    
                    for obs in recent_obs[:5]:  # Show last 5
                        with st.container():
                            st.markdown(f"""
                            <div class="observation-marker">
                            <strong>{obs.get('observation_type', 'Unknown')}</strong> - 
                            Confidence: {obs.get('confidence', 0)}/10<br>
                            <small>{obs.get('notes', 'No notes')[:100]}...</small>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("No scouting data found in this area. Start adding observations!")

# Add footer
st.markdown("---")
st.markdown("🦌 **Vermont Deer Movement Predictor** | Enhanced with Real-Time Scouting Data | Vermont Legal Hunting Hours Compliant")

# Add enhanced data traceability display to sidebar
create_enhanced_data_traceability_display()
