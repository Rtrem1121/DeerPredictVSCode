#!/usr/bin/env python3
"""Quick backend prediction run for a Vermont location."""

import asyncio
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.prediction_service import get_prediction_service


def summarize_prediction(result: dict) -> dict:
    return {
        "timestamp": result.get("timestamp"),
        "confidence_score": result.get("confidence_score"),
        "hunt_window_predictions_count": len(result.get("hunt_window_predictions", [])),
        "hunt_window_preview": result.get("hunt_window_predictions", [])[:1],
        "stand_priority_overrides_keys": list(result.get("stand_priority_overrides", {}).keys())[:3],
        "first_stand": result.get("mature_buck_analysis", {}).get("stand_recommendations", [])[:1],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a backend prediction for a specific location.")
    parser.add_argument("lat", type=float, nargs="?", default=44.2601, help="Latitude (default: 44.2601 Montpelier)")
    parser.add_argument("lon", type=float, nargs="?", default=-72.5754, help="Longitude (default: -72.5754 Montpelier)")
    parser.add_argument("--time", type=int, default=17, help="Hour of day 0-23 (default: 17)")
    parser.add_argument("--season", default="fall", choices=["spring", "summer", "fall", "winter"], help="Season label")
    parser.add_argument("--pressure", default="medium", choices=["low", "medium", "high"], help="Hunting pressure level")
    parser.add_argument("--label", default="", help="Optional label to include in output")
    return parser.parse_args()


async def main(args: argparse.Namespace) -> None:
    service = get_prediction_service()
    result = await service.predict(
        lat=args.lat,
        lon=args.lon,
        time_of_day=args.time,
        season=args.season,
        hunting_pressure=args.pressure,
    )
    summary = summarize_prediction(result)
    header = f"Location: ({args.lat:.4f}, {args.lon:.4f})"
    if args.label:
        header += f" | {args.label}"
    print(header)
    print("=== Prediction Summary ===")
    print(json.dumps(summary, indent=2))

    print("\n=== Hunt Window Predictions ===")
    print(json.dumps(result.get("hunt_window_predictions", []), indent=2))


if __name__ == "__main__":
    arguments = parse_args()
    asyncio.run(main(arguments))
