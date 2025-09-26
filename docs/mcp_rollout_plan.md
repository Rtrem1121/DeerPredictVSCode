# MCP Rollout Plan – Priority Steps 1–8

| Step | MCP Server | Purpose | Key Deliverables | Status |
| --- | --- | --- | --- | --- |
| 1 | `open-meteo-mcp` | 72h hourly weather, wind, pressure | Configure MCP entry and confirm response format for future-date requests | ✅ Completed (2025-09-25) |
| 2 | `usgs-lidar-mcp` | High-resolution elevation, slope, aspect | a) Decide USGS / OpenTopography endpoint<br>b) Define MCP schema (input lat/lon, output slope/aspect)<br>c) Prototype handler returning slope/aspect JSON | ⏳ In Progress |
| 3 | `vermont-hunt-regs-mcp` | Live season dates, legal hours, antler rules | a) Source latest VT F&W regulations<br>b) Normalize to machine-friendly schema<br>c) Expose endpoints for season lookup by date | ⏳ In Progress |
| 4 | `trail-cam-ingest-mcp` | Upload trail-cam observations → heatmaps | a) Define payload (timestamp, stand id, behavior)<br>b) Choose storage (Redis/Postgres)<br>c) Return aggregated hit rates per corridor | ⏳ In Progress |
| 5 | `whitetail-observation-mcp` | Aggregated scrape/rub sightings | a) Catalog internal + user submitted sign data<br>b) Design scoring model for freshness<br>c) Serve nearest high-confidence sign points | ⏳ In Progress |
| 6 | `noaa-forecast-mcp` | Alternate wind/pressure forecasts & alerts | a) Pick NOAA API (NDFD / Gridpoints)<br>b) Align units/timezones with open-meteo<br>c) Emit alert stream for storms/pressure drops | ⏳ Queue |
| 7 | `nasa-goes-imagery-mcp` | Recent cloud/temperature imagery | a) Select imagery product (GOES East ABI)<br>b) Provide latest tile + 6h history<br>c) Attach confidence on snow/thermal inversions | ⏳ Queue |
| 8 | `usfs-forest-structure-mcp` | Vegetation density, recent cuts, mast | a) Pull FIA / LANDFIRE datasets<br>b) Map to bedding/feeding suitability metrics<br>c) Return vegetation and mast indicators | ⏳ Queue |

## Execution Notes

- **Step 1 complete:** `open-meteo-mcp` configured in `.continue/mcpServers/new-mcp-server.yaml`; next action is wiring predictions to call it for future-date weather.
- **Steps 2–5** are active build targets. Each needs:
  - Source selection & API credentials (where required)
  - MCP request/response contract drafted (JSON schema)
  - Backend integration task created once server delivers data
- **Steps 6–8** queued; they depend on weather + terrain foundation so we defer detailed work until earlier MCPs are delivering data reliably.

## Next Actions Summary

1. Draft technical spec for `usgs-lidar-mcp` (data source, rate limits, response schema).
2. Begin `vermont-hunt-regs-mcp` scraper prototype to ingest 2025 regulation PDF / RSS.
3. Outline data model for `trail-cam-ingest-mcp` (observation table, aggregation job).
4. Collect historical scrape/rub dataset to feed `whitetail-observation-mcp`.
5. Once steps 2–5 have working prototypes, schedule integrations into prediction pipeline.
