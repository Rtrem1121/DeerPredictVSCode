import json
import math
from typing import Any, Dict, List

import requests

API_URL = "http://localhost:8000/predict"
REQUEST_TIMEOUT = 180

LOCATIONS = [
    {
        "name": "Northern Vermont - Newport",
        "lat": 44.9368,
        "lon": -72.2109,
        "season": "early",
        "description": "Northern tier agricultural mix"
    },
    {
        "name": "Central Vermont - Montpelier",
        "lat": 44.2601,
        "lon": -72.5754,
        "season": "pre-rut",
        "description": "Capital region hardwood ridge"
    },
    {
        "name": "Southern Vermont - Bennington",
        "lat": 42.8781,
        "lon": -73.1968,
        "season": "rut",
        "description": "Southern valleys and foothills"
    },
]


def format_coord(value: float) -> str:
    return f"{value:.6f}"


def summarize_stands(stands: List[Dict[str, Any]]) -> List[str]:
    summary = []
    for stand in stands:
        coords = stand.get("coordinates", {})
        lat = coords.get("lat")
        lon = coords.get("lon")
        summary.append(
            " | ".join(
                [
                    stand.get("stand_id", "unknown"),
                    stand.get("type", ""),
                    f"lat={format_coord(lat)}" if lat is not None else "lat=?",
                    f"lon={format_coord(lon)}" if lon is not None else "lon=?",
                ]
            )
        )
    return summary


def summarize_geojson(features: List[Dict[str, Any]]) -> List[str]:
    summary = []
    for idx, feature in enumerate(features):
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) >= 2:
            lon, lat = coords[0], coords[1]
            summary.append(f"#{idx}: lat={format_coord(lat)}, lon={format_coord(lon)}")
    return summary


def main() -> None:
    baseline_coordinates = None

    for location in LOCATIONS:
        payload = {
            "lat": location["lat"],
            "lon": location["lon"],
            "date_time": "2025-09-28T07:00:00-04:00",
            "season": location["season"],
            "hunting_pressure": "medium",
        }

        print("\n=== Running prediction for:")
        print(f"Location: {location['name']} ({location['lat']}, {location['lon']})")
        print(f"Context: {location['description']}")

        response = requests.post(API_URL, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        raw_result = response.json()
        data = raw_result.get("data", raw_result)

        hunt_coords = data.get("coordinates", {})
        print("Requested map center:", hunt_coords)

        stands = data.get("mature_buck_analysis", {}).get("stand_recommendations", [])
        stand_summary = summarize_stands(stands)

        print("Stand recommendations:")
        if stand_summary:
            for line in stand_summary:
                print("  -", line)
        else:
            print("  (no stands returned)")

        bedding_features = data.get("bedding_zones", {}).get("features", [])
        feeding_features = data.get("feeding_areas", {}).get("features", [])

        if bedding_features:
            print("Bedding zone markers:")
            for line in summarize_geojson(bedding_features):
                print("  -", line)

        if feeding_features:
            print("Feeding area markers:")
            for line in summarize_geojson(feeding_features):
                print("  -", line)

        marker_coords = [
            (stand.get("coordinates", {}).get("lat"), stand.get("coordinates", {}).get("lon"))
            for stand in stands
        ]

        if baseline_coordinates is None:
            baseline_coordinates = marker_coords
        else:
            identical = marker_coords == baseline_coordinates
            print(f"Matches baseline stand coordinates: {identical}")


if __name__ == "__main__":
    main()
