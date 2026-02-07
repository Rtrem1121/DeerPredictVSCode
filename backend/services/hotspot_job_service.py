# Backward-compat shim - logic moved to backend.services.hotspot
from backend.services.hotspot.job_service import HotspotJob, HotspotJobService, get_hotspot_job_service  # noqa: F401
