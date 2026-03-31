"""Milestone 1 — Data Foundation Validation Tests.

Covers:
  - Waypoint date parsing (Task 1.1)
  - GPX track import (Task 1.2)
  - Buck event schema (Task 1.3)
  - Evidence weighting model (Task 1.4)
  - Evidence cluster framework (Task 1.5)
  - Gold-test end-to-end scenario
"""

import math
import pytest
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────────────────
# Task 1.1: GPX date extraction from waypoint text
# ─────────────────────────────────────────────────────────────────────────

from backend.scouting_import.contracts import (
    parse_date_from_text,
    WaypointRecord,
    load_gpx_waypoints_from_bytes,
    load_gpx_tracks_from_bytes,
    canonical_observation_payload,
    TrackType,
)


class TestDateParsing:
    """Waypoint date extraction from OnX-style text."""

    @pytest.mark.parametrize("text,expected_year,expected_month,expected_day,expected_precision", [
        ("Fresh Beds 10/1/20", 2020, 10, 1, "day"),
        ("Deer Trail 09/13/25 11:52", 2025, 9, 13, "exact"),
        ("scrape 2017", 2017, 1, 1, "year"),
        ("Shot 2018 Buck here", 2018, 1, 1, "year"),
        ("Rub line October 15, 2025", 2025, 10, 15, "day"),
        ("camera 2025-09-20", 2025, 9, 20, "day"),
        ("Old stand Oct 2019", 2019, 10, 1, "month"),
        ("Fresh rub 11/18/25", 2025, 11, 18, "day"),
    ])
    def test_date_extraction_patterns(self, text, expected_year, expected_month, expected_day, expected_precision):
        dt, precision = parse_date_from_text(text)
        assert dt is not None, f"Failed to parse date from: {text}"
        assert dt.year == expected_year
        assert dt.month == expected_month
        assert dt.day == expected_day
        assert precision == expected_precision

    def test_no_date_returns_none(self):
        dt, precision = parse_date_from_text("Big oak tree")
        assert dt is None
        assert precision == "none"

    def test_empty_string(self):
        dt, precision = parse_date_from_text("")
        assert dt is None
        assert precision == "none"

    def test_time_element_takes_priority_in_waypoint(self):
        """<time> element should produce 'exact' precision and not need text parsing."""
        gpx = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="43.31" lon="-73.21">
    <time>2025-10-01T15:23:00Z</time>
    <name>scrape 2017</name>
  </wpt>
</gpx>"""
        wpts = load_gpx_waypoints_from_bytes(gpx)
        assert len(wpts) == 1
        # <time> wins over "2017" in the name
        assert wpts[0].time_utc.year == 2025
        assert wpts[0].date_precision == "exact"

    def test_text_date_fallback_when_no_time_element(self):
        gpx = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="43.31" lon="-73.21">
    <name>Fresh Beds 10/1/20</name>
  </wpt>
</gpx>"""
        wpts = load_gpx_waypoints_from_bytes(gpx)
        assert len(wpts) == 1
        assert wpts[0].time_utc is not None
        assert wpts[0].time_utc.year == 2020
        assert wpts[0].date_precision == "day"


class TestConfidenceByPrecision:
    """Undated and year-only waypoints get reduced confidence."""

    def test_undated_waypoint_low_confidence(self):
        gpx = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="43.31" lon="-73.21">
    <name>Big oak tree</name>
  </wpt>
</gpx>"""
        wpts = load_gpx_waypoints_from_bytes(gpx)
        payload = canonical_observation_payload(wpts[0])
        assert payload["confidence"] == 4  # undated

    def test_year_only_medium_confidence(self):
        gpx = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="43.31" lon="-73.21">
    <name>scrape 2017</name>
  </wpt>
</gpx>"""
        wpts = load_gpx_waypoints_from_bytes(gpx)
        payload = canonical_observation_payload(wpts[0])
        assert payload["confidence"] == 5  # year-only

    def test_exact_date_normal_confidence(self):
        gpx = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="43.31" lon="-73.21">
    <time>2025-10-01T15:23:00Z</time>
    <name>rub</name>
  </wpt>
</gpx>"""
        wpts = load_gpx_waypoints_from_bytes(gpx)
        payload = canonical_observation_payload(wpts[0])
        assert payload["confidence"] == 6  # exact/day date


# ─────────────────────────────────────────────────────────────────────────
# Task 1.2: GPX Track Import
# ─────────────────────────────────────────────────────────────────────────

class TestTrackImport:
    """GPX <trk> element parsing and classification."""

    SAMPLE_GPX = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="43.31" lon="-73.21"><name>rub</name></wpt>
  <trk>
    <name>Walk In Route</name>
    <trkseg>
      <trkpt lat="43.310" lon="-73.215"><ele>200</ele></trkpt>
      <trkpt lat="43.311" lon="-73.216"><ele>210</ele></trkpt>
      <trkpt lat="43.312" lon="-73.217"><ele>215</ele></trkpt>
    </trkseg>
  </trk>
  <trk>
    <name>Deer Trail Along Creek</name>
    <trkseg>
      <trkpt lat="43.313" lon="-73.215"></trkpt>
      <trkpt lat="43.314" lon="-73.216"></trkpt>
    </trkseg>
  </trk>
  <trk>
    <name>Scouting walk Nov 5</name>
    <trkseg>
      <trkpt lat="43.315" lon="-73.218"></trkpt>
    </trkseg>
  </trk>
</gpx>"""

    def test_tracks_parsed(self):
        tracks = load_gpx_tracks_from_bytes(self.SAMPLE_GPX)
        assert len(tracks) == 3

    def test_access_route_classified(self):
        tracks = load_gpx_tracks_from_bytes(self.SAMPLE_GPX)
        access = [t for t in tracks if t.track_type == TrackType.ACCESS]
        assert len(access) == 1
        assert access[0].is_access is True
        assert access[0].should_influence_deer_model is False

    def test_deer_route_classified(self):
        tracks = load_gpx_tracks_from_bytes(self.SAMPLE_GPX)
        deer = [t for t in tracks if t.track_type == TrackType.DEER_ROUTE_OBSERVATION]
        assert len(deer) == 1
        assert deer[0].should_influence_deer_model is True

    def test_scouting_walk_classified(self):
        tracks = load_gpx_tracks_from_bytes(self.SAMPLE_GPX)
        scout = [t for t in tracks if t.track_type == TrackType.SCOUTING_WALK]
        assert len(scout) == 1

    def test_waypoints_and_tracks_coexist(self):
        wpts = load_gpx_waypoints_from_bytes(self.SAMPLE_GPX)
        tracks = load_gpx_tracks_from_bytes(self.SAMPLE_GPX)
        assert len(wpts) == 1
        assert len(tracks) == 3

    def test_track_distance_computed(self):
        tracks = load_gpx_tracks_from_bytes(self.SAMPLE_GPX)
        walk_in = [t for t in tracks if t.name == "Walk In Route"][0]
        assert walk_in.total_distance_m > 0
        assert walk_in.total_distance_m < 1000  # ~275m for these coords


# ─────────────────────────────────────────────────────────────────────────
# Task 1.3: Buck Event Schema
# ─────────────────────────────────────────────────────────────────────────

from backend.models.buck_event import BuckEvent, BuckClass, EventSource, MovementType


class TestBuckEvent:
    """Individual mature-buck detection event model."""

    def test_basic_creation(self):
        ev = BuckEvent(
            lat=43.31255, lon=-73.21502,
            timestamp="2025-10-01T19:23:00Z",
            source="moultrie",
            buck_class="8-pointer",
        )
        assert ev.source == EventSource.MOULTRIE
        assert ev.buck_class == BuckClass.EIGHT_POINTER
        assert ev.timestamp.tzinfo is not None

    def test_daylight_auto_computed(self):
        # Oct 1 at 3:23 PM EDT → 19:23 UTC → daylight in Vermont
        ev = BuckEvent(
            lat=43.31255, lon=-73.21502,
            timestamp="2025-10-01T19:23:00Z",
        )
        assert ev.daylight is True

    def test_nighttime_detection(self):
        # Sep 20 9 PM EDT → 01:00 UTC next day → night in Vermont
        ev = BuckEvent(
            lat=43.31255, lon=-73.21502,
            timestamp="2025-09-21T01:00:00Z",
        )
        assert ev.daylight is False

    def test_is_mature_property(self):
        for bc in [BuckClass.EIGHT_POINTER, BuckClass.TEN_POINTER, BuckClass.UNKNOWN_MATURE]:
            ev = BuckEvent(lat=43.0, lon=-73.0, timestamp="2025-10-01T12:00:00Z", buck_class=bc)
            assert ev.is_mature is True
        for bc in [BuckClass.SPIKE, BuckClass.FOUR_POINTER, BuckClass.UNKNOWN]:
            ev = BuckEvent(lat=43.0, lon=-73.0, timestamp="2025-10-01T12:00:00Z", buck_class=bc)
            assert ev.is_mature is False

    def test_maturity_weight_target_repeated(self):
        ev = BuckEvent(
            lat=43.0, lon=-73.0,
            timestamp="2025-10-01T12:00:00Z",
            buck_class="8-pointer",
            target_buck=True,
            repeat_location=True,
        )
        # 1.2 × 1.25 × 1.15 = 1.725
        assert ev.maturity_weight == 1.725

    def test_maturity_weight_spike(self):
        ev = BuckEvent(
            lat=43.0, lon=-73.0,
            timestamp="2025-10-01T12:00:00Z",
            buck_class="spike",
        )
        assert ev.maturity_weight == 0.3

    def test_round_trip_serialisation(self):
        ev = BuckEvent(
            lat=43.31255, lon=-73.21502,
            timestamp="2025-10-01T19:23:00Z",
            source="moultrie",
            buck_class="8-pointer",
            buck_id="creek-8pt",
            target_buck=True,
            movement_type="crossing",
            repeat_location=True,
            confidence=9,
        )
        d = ev.to_dict()
        ev2 = BuckEvent.from_dict(d)
        assert ev2.lat == ev.lat
        assert ev2.buck_class == ev.buck_class
        assert ev2.target_buck is True
        assert ev2.event_id == ev.event_id


# ─────────────────────────────────────────────────────────────────────────
# Task 1.4: Evidence Weighting Model
# ─────────────────────────────────────────────────────────────────────────

from backend.models.evidence_weights import (
    compute_evidence_weight,
    recency_weight,
    source_quality_for_observation,
    maturity_multiplier,
    pattern_bonus,
    age_days_from_timestamp,
)
from backend.scouting_models import ObservationType


class TestRecencyWeight:
    def test_fresh_data(self):
        assert recency_weight(0) == 1.0
        assert recency_weight(14) == 1.0

    def test_moderate_age(self):
        assert recency_weight(30) == 0.80

    def test_old_data(self):
        assert recency_weight(200) == 0.20

    def test_archive(self):
        assert recency_weight(800) == 0.05


class TestSourceQuality:
    def test_target_buck_camera_highest(self):
        sq = source_quality_for_observation(ObservationType.TRAIL_CAMERA, is_target_buck=True)
        assert sq == 1.0

    def test_undated_caps_quality(self):
        sq = source_quality_for_observation(ObservationType.RUB_LINE, is_dated=False)
        assert sq == 0.30  # capped at undated_waypoint


class TestMaturityMultiplier:
    def test_target_repeated(self):
        assert maturity_multiplier(is_mature=True, is_target=True, is_repeated=True) == 1.50

    def test_generic_buck(self):
        assert maturity_multiplier() == 0.80


class TestCombinedWeight:
    def test_gold_test_cluster_very_high(self):
        """Creek crossing 8-pointer, target, repeated, daylight, fresh."""
        sq = source_quality_for_observation(ObservationType.TRAIL_CAMERA, is_target_buck=True)
        mm = maturity_multiplier(is_mature=True, is_target=True, is_repeated=True)
        w = compute_evidence_weight(sq, age_days=0, maturity_multiplier_val=mm,
                                    pattern_flags={"repeated": True, "daylight": True, "multi_evidence": True})
        assert w >= 0.9

    def test_2017_undated_scrape_very_low(self):
        sq = source_quality_for_observation(ObservationType.FRESH_SCRAPE, is_dated=False)
        w = compute_evidence_weight(sq, age_days=365 * 8)
        assert w < 0.10

    def test_2025_fresh_rub_moderate(self):
        sq = source_quality_for_observation(ObservationType.RUB_LINE, is_dated=True)
        w = compute_evidence_weight(sq, age_days=30, maturity_multiplier_val=1.2)
        assert 0.5 <= w <= 0.85


# ─────────────────────────────────────────────────────────────────────────
# Task 1.5: Evidence Cluster Framework
# ─────────────────────────────────────────────────────────────────────────

from backend.models.evidence_cluster import build_clusters, EvidenceCluster
from backend.scouting_models import ScoutingObservation


class TestEvidenceClustering:
    """Auto-clustering and cluster scoring."""

    @pytest.fixture
    def gold_test_data(self):
        """Gold-test cluster: creek crossing + 2 rubs + 8 camera events."""
        now = datetime(2025, 11, 25, 12, 0, tzinfo=timezone.utc)
        rub1 = ScoutingObservation(
            id="rub1", lat=43.31026, lon=-73.21541,
            observation_type=ObservationType.RUB_LINE,
            confidence=8, timestamp=datetime(2025, 10, 1, tzinfo=timezone.utc),
        )
        rub2 = ScoutingObservation(
            id="rub2", lat=43.31141, lon=-73.21282,
            observation_type=ObservationType.RUB_LINE,
            confidence=8, timestamp=datetime(2025, 10, 5, tzinfo=timezone.utc),
        )
        events_raw = [
            ("2025-09-20T21:00:00Z", "4-pointer", False),
            ("2025-09-27T11:46:00Z", "8-pointer", True),
            ("2025-10-01T15:23:00Z", "8-pointer", True),
            ("2025-10-03T07:38:00Z", "8-pointer", True),
            ("2025-10-09T15:31:00Z", "4-pointer", False),
            ("2025-11-05T08:13:00Z", "spike", False),
            ("2025-11-18T06:20:00Z", "8-pointer", True),
            ("2025-11-24T05:25:00Z", "spike", False),
        ]
        events = []
        for ts, bc, tgt in events_raw:
            events.append(BuckEvent(
                lat=43.31255, lon=-73.21502,
                timestamp=ts, source="moultrie", buck_class=bc,
                buck_id="creek-8pt" if tgt else None,
                target_buck=tgt, movement_type="crossing",
                repeat_location=True, confidence=9,
            ))
        return rub1, rub2, events, now

    def test_gold_cluster_forms(self, gold_test_data):
        rub1, rub2, events, now = gold_test_data
        clusters = build_clusters([rub1, rub2], events, now=now)
        assert len(clusters) >= 1

    def test_gold_cluster_includes_all_members(self, gold_test_data):
        rub1, rub2, events, now = gold_test_data
        clusters = build_clusters([rub1, rub2], events, now=now)
        c = clusters[0]
        total = len(c.observation_ids) + len(c.buck_event_ids)
        assert total == 10  # 2 rubs + 8 events

    def test_gold_cluster_has_both_evidence_types(self, gold_test_data):
        rub1, rub2, events, now = gold_test_data
        clusters = build_clusters([rub1, rub2], events, now=now)
        c = clusters[0]
        assert "Rub Line" in c.evidence_types
        assert "Trail Camera" in c.evidence_types

    def test_gold_cluster_early_season_and_rut_elevated(self, gold_test_data):
        rub1, rub2, events, now = gold_test_data
        clusters = build_clusters([rub1, rub2], events, now=now)
        c = clusters[0]
        assert c.seasonal_confidence.get("early_season", 0) > 0.5
        assert c.seasonal_confidence.get("rut", 0) > 0.5

    def test_gold_cluster_is_highest_weight(self, gold_test_data):
        """If we add a weak distant observation, the gold cluster still ranks first."""
        rub1, rub2, events, now = gold_test_data
        weak_obs = ScoutingObservation(
            id="weak1", lat=43.30, lon=-73.20,
            observation_type=ObservationType.OTHER_SIGN,
            confidence=3, timestamp=datetime(2018, 6, 1, tzinfo=timezone.utc),
        )
        weak_obs2 = ScoutingObservation(
            id="weak2", lat=43.301, lon=-73.201,
            observation_type=ObservationType.OTHER_SIGN,
            confidence=3, timestamp=datetime(2018, 7, 1, tzinfo=timezone.utc),
        )
        clusters = build_clusters([rub1, rub2, weak_obs, weak_obs2], events, now=now)
        # Gold cluster should be first (highest weight)
        assert clusters[0].combined_weight > clusters[-1].combined_weight

    def test_serialisation_round_trip(self, gold_test_data):
        rub1, rub2, events, now = gold_test_data
        clusters = build_clusters([rub1, rub2], events, now=now)
        c = clusters[0]
        d = c.to_dict()
        c2 = EvidenceCluster.from_dict(d)
        assert c2.cluster_id == c.cluster_id
        assert c2.combined_weight == c.combined_weight


# ─────────────────────────────────────────────────────────────────────────
# End-to-end: Full Gold Test Scenario
# ─────────────────────────────────────────────────────────────────────────

class TestGoldTestEndToEnd:
    """Load GPX + buck events → clusters form → weights match expectations."""

    def test_full_pipeline(self):
        now = datetime(2025, 11, 25, 12, 0, tzinfo=timezone.utc)

        # Simulate GPX import of rubs
        gpx = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="43.31026" lon="-73.21541">
    <name>Fresh rub 10/1/25</name>
  </wpt>
  <wpt lat="43.31141" lon="-73.21282">
    <name>Fresh rub 10/5/25</name>
  </wpt>
  <wpt lat="43.30" lon="-73.20">
    <name>old scrape 2017</name>
  </wpt>
</gpx>"""
        wpts = load_gpx_waypoints_from_bytes(gpx)
        assert len(wpts) == 3

        # Verify dates parsed
        assert wpts[0].time_utc.year == 2025
        assert wpts[2].time_utc.year == 2017
        assert wpts[2].date_precision == "year"

        # Convert to observations
        payloads = [canonical_observation_payload(w) for w in wpts]

        # 2025 rubs get confidence 6, 2017 gets 5
        assert payloads[0]["confidence"] == 6  # day precision
        assert payloads[2]["confidence"] == 5  # year precision

        # Create observations from payloads
        obs_list = []
        for i, p in enumerate(payloads):
            obs_list.append(ScoutingObservation(id=f"obs{i}", **p))

        # Create buck events
        events = []
        for ts, bc, tgt in [
            ("2025-09-27T11:46:00Z", "8-pointer", True),
            ("2025-10-01T19:23:00Z", "8-pointer", True),
            ("2025-10-03T11:38:00Z", "8-pointer", True),
        ]:
            events.append(BuckEvent(
                lat=43.31255, lon=-73.21502,
                timestamp=ts, source="moultrie", buck_class=bc,
                target_buck=tgt, movement_type="crossing",
                repeat_location=True, confidence=9,
            ))

        # Build clusters
        clusters = build_clusters(obs_list, events, now=now)

        # The 2025 rubs + events should cluster together
        main_cluster = clusters[0]
        assert len(main_cluster.observation_ids) + len(main_cluster.buck_event_ids) >= 4
        assert main_cluster.combined_weight > 2.0

        # The 2017 scrape should NOT be in the main cluster (too far away)
        old_obs_id = "obs2"
        assert old_obs_id not in main_cluster.observation_ids
