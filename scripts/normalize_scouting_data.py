#!/usr/bin/env python3
"""Normalize legacy scouting observation records.

- Converts legacy observation_type strings (e.g. "Trail Camera Setup") to the
  current enum values.
- Coerces timestamps to timezone-aware UTC ISO strings.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable

LEGACY_OBSERVATION_TYPE_MAP = {
    "Trail Camera Setup": "Trail Camera",
}


def _normalize_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        timestamp = value
    elif isinstance(value, str):
        # Support legacy Z suffix
        sanitized = value.replace("Z", "+00:00")
        try:
            timestamp = datetime.fromisoformat(sanitized)
        except ValueError as exc:
            raise ValueError(f"Unable to parse timestamp '{value}'") from exc
    else:
        raise ValueError(f"Unsupported timestamp value: {value!r}")

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    else:
        timestamp = timestamp.astimezone(timezone.utc)
    return timestamp.isoformat()


def _normalize_observation(obs: Dict[str, Any]) -> Dict[str, Any]:
    updated = dict(obs)

    legacy_type = updated.get("observation_type")
    if isinstance(legacy_type, str):
        updated["observation_type"] = LEGACY_OBSERVATION_TYPE_MAP.get(
            legacy_type, legacy_type
        )

    timestamp_value = updated.get("timestamp")
    if timestamp_value is not None:
        updated["timestamp"] = _normalize_timestamp(timestamp_value)

    return updated


def normalize_file(path: Path) -> None:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    observations: Iterable[Dict[str, Any]] = payload.get("observations", [])
    payload["observations"] = [_normalize_observation(obs) for obs in observations]

    backup_path = path.with_suffix(path.suffix + ".backup")
    path.replace(backup_path)

    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print(f"Normalized observations written to {path}")
    print(f"Original file backed up at {backup_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "data_file",
        type=Path,
        nargs="?",
        default=Path("data/scouting_observations.json"),
        help="Path to scouting observations JSON file",
    )
    args = parser.parse_args()

    normalize_file(args.data_file)


if __name__ == "__main__":
    main()
