# Scouting Data Contract

This note captures the canonical schema and import expectations for
historical scouting data so we can safely ingest the 10-year GPX archive
without destabilising the existing backend.

## Canonical Observation Schema

All scouting observations are stored via the existing
`ScoutingObservation` pydantic model located in
`backend/scouting_models.py`. Key fields:

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | `str` | Optional unique identifier generated on insert |
| `lat` / `lon` | `float` | Required decimal degree coordinates |
| `observation_type` | `ObservationType` enum | Must map to one of the supported deer sign categories |
| `confidence` | `int (1-10)` | Defaults to 6 for imported records; refined later |
| `timestamp` | `datetime` | Always stored as timezone-aware UTC |
| `notes` | `str` | Free-form text combining waypoint name, description and metadata |
| `photo_urls` | `List[str]` | For historical imports we leave empty |
| `weather_conditions` | `Optional[str]` | Populated only when contemporaneous data exists |
| Type-specific details | Optional nested models (`ScrapeDetails`, etc.) | Pre-populated with defaults so downstream logic can branch safely |

The importer should only emit data that this schema will accept; validation
errors become test failures.

## GPX to Observation Mapping

We represent GPX waypoints with a lightweight dataclass
`WaypointRecord` (see `backend/scouting_import/contracts.py`). The core
mapping rules are:

- `lat`/`lon` come from waypoint attributes.
- `timestamp` uses the `<time>` element; timestamps are normalised to UTC.
- `notes` string concatenates `<name>`, `<desc>` and `<sym>` plus an
  elevation annotation when available.
- `observation_type` is inferred using keyword heuristics on the combined
  text fields:
  - Contains `scrape` → `Fresh Scrape`
  - Contains `rub` → `Rub Line`
  - Contains `bed`/`bedding` → `Bedding Area`
  - Contains `camera` → `Trail Camera Setup`
  - Contains `track`/`trail` → `Deer Tracks/Trail`
  - Contains feeding keywords → `Feeding Sign`
  - Contains `buck`/`doe`/`deer` → `Deer Sighting`
  - Fallback → `Other Sign`
- Type-specific nested detail models receive conservative default values
  so analytics logic can rely on their presence when needed.

These heuristics are intentionally simple for now; additional context
(e.g. seasonal cues, symbol mapping) can be introduced in later phases.

## Validation Strategy

Phase 1 focuses on contract validation, so we added
`tests/test_scouting_data_contract.py` to exercise:

1. Loading sample JSON observations and validating they can be parsed into
   `ScoutingObservation` instances.
2. Parsing GPX waypoints into `WaypointRecord` objects (covering elevation,
   timestamp and namespace handling).
3. Converting waypoints into canonical observation payloads and ensuring
   they pass model validation.

We store trimmed fixtures under `tests/fixtures/` to keep tests fast and
self-contained. Future phases can extend these fixtures to cover more edge
cases (duplicate IDs, missing timestamps, etc.).

## Next Steps

- **Phase 2**: Build the REST import pipeline that leverages these helper
  utilities and writes through `ScoutingDataManager` with deduplication.
- **Phase 3+**: Expand keyword inference with statistical models, add
  confidence calibration, and surface analytics in the frontend.

Keeping this contract documented ensures future upgrades remain safe and
backwards-compatible.
