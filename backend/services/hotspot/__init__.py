"""Hotspot property analysis package.

Re-exports the public API for backward compatibility with
``from backend.services.hotspot_job_service import get_hotspot_job_service``.
"""

from backend.services.hotspot.job_service import (  # noqa: F401
    HotspotJob,
    HotspotJobService,
    get_hotspot_job_service,
)

__all__ = ["HotspotJob", "HotspotJobService", "get_hotspot_job_service"]
