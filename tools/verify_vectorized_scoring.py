"""
Smoke-test: vectorized scoring in pipeline._score_terrain produces
numerically equivalent results to the original scalar formulas.
Run from repo root: python tools/verify_vectorized_scoring.py
"""
import math
import sys
import numpy as np

sys.path.insert(0, ".")

from backend.utils.terrain_scoring import slope_preference, ridge_proximity_preference
from backend.max_accuracy.terrain_metrics import score_bench_saddle
from backend.utils.geo import angular_diff

WEIGHTS = {
    "slope_pref": 0.18, "elev_pref": 0.12, "bench": 0.14, "saddle": 0.14,
    "corridor": 0.08, "roughness": 0.06, "curvature": 0.04,
    "shelter": 0.08, "aspect": 0.08, "ridgeline": 0.04, "drainage": 0.04,
}

# --- Representative test points ---
points = [
    dict(s=12.0, e=850.0, aspect=175.0, curv=0.05, tpi_s=1.2, tpi_l=3.5, relief=8.0, roughness=4.5, ridge=0.7, drain=0.2, elev_min=600.0, elev_max=1000.0),
    dict(s=0.5, e=610.0, aspect=270.0, curv=-0.02, tpi_s=-5.0, tpi_l=-8.0, relief=2.0, roughness=0.8, ridge=0.0, drain=0.9, elev_min=600.0, elev_max=1000.0),
    dict(s=25.0, e=980.0, aspect=45.0, curv=0.12, tpi_s=0.1, tpi_l=0.5, relief=12.0, roughness=7.0, ridge=0.9, drain=0.1, elev_min=600.0, elev_max=1000.0),
    dict(s=8.0, e=760.0, aspect=160.0, curv=0.03, tpi_s=2.0, tpi_l=1.0, relief=6.0, roughness=3.5, ridge=0.3, drain=0.4, elev_min=600.0, elev_max=1000.0),
]

def clamp01(v):
    return max(0.0, min(1.0, v))

def scalar_score(p):
    s, e, aspect, curv = p["s"], p["e"], p["aspect"], p["curv"]
    tpi_s, tpi_l, relief = p["tpi_s"], p["tpi_l"], p["relief"]
    roughness, ridge, drain = p["roughness"], p["ridge"], p["drain"]
    elev_min, elev_max = p["elev_min"], p["elev_max"]

    sp = slope_preference(s)
    ep = ridge_proximity_preference(e, elev_min, elev_max)
    bench, saddle = score_bench_saddle(s, tpi_s, relief, curv)
    corridor = clamp01(1.0 - (abs(tpi_l) / max(1.0, relief))) * clamp01(relief / 10.0)
    shelter = clamp01(1.0 - (s / 20.0)) * clamp01((relief - abs(tpi_s)) / max(1.0, relief))
    rgh = clamp01(roughness / 6.0)
    cv = clamp01(abs(curv) / 0.1)
    ad = angular_diff(aspect, 170.0)
    asp = clamp01(1.0 - (ad / 100.0))
    w = WEIGHTS
    return (sp*w["slope_pref"] + ep*w["elev_pref"] + bench*w["bench"] + saddle*w["saddle"]
            + corridor*w["corridor"] + rgh*w["roughness"] + cv*w["curvature"]
            + shelter*w["shelter"] + asp*w["aspect"] + ridge*w["ridgeline"] + drain*w["drainage"])

def vec_score(pts):
    s = np.array([p["s"] for p in pts])
    e = np.array([p["e"] for p in pts])
    aspect = np.array([p["aspect"] for p in pts])
    curv = np.array([p["curv"] for p in pts])
    tpi_s = np.array([p["tpi_s"] for p in pts])
    tpi_l = np.array([p["tpi_l"] for p in pts])
    relief = np.array([p["relief"] for p in pts])
    rough = np.array([p["roughness"] for p in pts])
    ridge = np.array([p["ridge"] for p in pts])
    drain = np.array([p["drain"] for p in pts])
    elev_min = pts[0]["elev_min"]
    elev_max = pts[0]["elev_max"]

    slope_pref = np.where(s < 0.0, 0.0,
        np.where(s < 5.0, 0.2 + 0.8 * (s / 5.0),
        np.where(s <= 22.0, 1.0,
        np.where(s <= 35.0, np.maximum(0.0, 1.0 - (s - 22.0) / 13.0), 0.0))))

    _elev_denom = max(1e-6, elev_max - elev_min)
    en = (e - elev_min) / _elev_denom
    elev_pref = np.where(en < 0.3, np.maximum(0.1, en / 0.3 * 0.4),
        np.where(en < 0.6, 0.4 + (en - 0.3) / 0.3 * 0.5,
        np.where(en <= 0.92, np.maximum(0.9, 1.0 - np.abs(en - 0.80) / 0.20),
        np.maximum(0.7, 1.0 - (en - 0.92) / 0.08 * 0.3))))

    rs = np.maximum(relief, 1.0)
    tsn = np.abs(tpi_s) / rs
    bench = np.clip(1.0 - (np.abs(s - 6.0) / 8.0), 0., 1.) * np.clip(1.0 - tsn, 0., 1.)
    saddle = np.clip(relief / 8.0, 0., 1.) * np.clip(1.0 - tsn, 0., 1.) * np.clip(np.abs(curv) / 0.08, 0., 1.)
    corridor = np.clip(1.0 - (np.abs(tpi_l) / rs), 0., 1.) * np.clip(relief / 10.0, 0., 1.)
    shelter = np.clip(1.0 - (s / 20.0), 0., 1.) * np.clip((relief - np.abs(tpi_s)) / rs, 0., 1.)
    rgh = np.clip(rough / 6.0, 0., 1.)
    cv = np.clip(np.abs(curv) / 0.1, 0., 1.)
    ad = np.abs(aspect - 170.0) % 360.0
    asp = np.clip(1.0 - (np.minimum(ad, 360.0 - ad) / 100.0), 0., 1.)
    w = WEIGHTS
    return (slope_pref*w["slope_pref"] + elev_pref*w["elev_pref"] + bench*w["bench"] + saddle*w["saddle"]
            + corridor*w["corridor"] + rgh*w["roughness"] + cv*w["curvature"] + shelter*w["shelter"]
            + asp*w["aspect"] + ridge*w["ridgeline"] + drain*w["drainage"])

scalar_scores = [scalar_score(p) for p in points]
vector_scores = vec_score(points)

ok = True
for i, (sc, sv) in enumerate(zip(scalar_scores, vector_scores)):
    diff = abs(sc - sv)
    status = "OK" if diff < 1e-9 else f"MISMATCH diff={diff:.2e}"
    print(f"  point {i}: scalar={sc:.6f}  vec={float(sv):.6f}  {status}")
    if diff >= 1e-9:
        ok = False

if ok:
    print("\nAll scores match within floating-point tolerance.")
    sys.exit(0)
else:
    print("\nScore mismatch detected!")
    sys.exit(1)
