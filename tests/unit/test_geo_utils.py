"""Tests for backend.utils.geo shared geographic utilities."""

import pytest
from backend.utils.geo import (
    angular_diff,
    bearing_between,
    bearing_to_cardinal,
    haversine,
    point_in_polygon,
)


class TestHaversine:
    def test_same_point_returns_zero(self):
        assert haversine(44.0, -73.0, 44.0, -73.0) == 0.0

    def test_known_distance(self):
        # New York to Los Angeles ≈ 3,944 km
        dist = haversine(40.7128, -74.0060, 34.0522, -118.2437)
        assert 3_900_000 < dist < 4_000_000

    def test_short_distance_meters(self):
        # ~111m per 0.001 degree latitude at equator
        dist = haversine(0.0, 0.0, 0.001, 0.0)
        assert 100 < dist < 120

    def test_symmetric(self):
        d1 = haversine(44.0, -73.0, 45.0, -72.0)
        d2 = haversine(45.0, -72.0, 44.0, -73.0)
        assert abs(d1 - d2) < 0.01


class TestBearingBetween:
    def test_due_north(self):
        # Point 2 is directly north of point 1
        b = bearing_between(44.0, -73.0, 45.0, -73.0)
        assert abs(b - 0.0) < 1.0 or abs(b - 360.0) < 1.0

    def test_due_east(self):
        b = bearing_between(44.0, -73.0, 44.0, -72.0)
        assert abs(b - 90.0) < 5.0  # not perfectly 90 due to curvature

    def test_due_south(self):
        b = bearing_between(45.0, -73.0, 44.0, -73.0)
        assert abs(b - 180.0) < 1.0

    def test_returns_0_to_360(self):
        b = bearing_between(44.0, -73.0, 44.0, -74.0)  # westward
        assert 0 <= b < 360


class TestAngularDiff:
    def test_zero(self):
        assert angular_diff(90.0, 90.0) == 0.0

    def test_opposite(self):
        assert angular_diff(0.0, 180.0) == 180.0

    def test_wraps_around(self):
        assert angular_diff(350.0, 10.0) == 20.0

    def test_symmetric(self):
        assert angular_diff(30.0, 90.0) == angular_diff(90.0, 30.0)


class TestBearingToCardinal:
    @pytest.mark.parametrize(
        "bearing,expected",
        [
            (0.0, "N"),
            (45.0, "NE"),
            (90.0, "E"),
            (135.0, "SE"),
            (180.0, "S"),
            (225.0, "SW"),
            (270.0, "W"),
            (315.0, "NW"),
            (359.0, "N"),
            (22.0, "N"),
            (23.0, "NE"),
        ],
    )
    def test_cardinal_directions(self, bearing, expected):
        assert bearing_to_cardinal(bearing) == expected


class TestPointInPolygon:
    def test_inside_square(self):
        polygon = [(0, 0), (0, 10), (10, 10), (10, 0)]
        assert point_in_polygon(5, 5, polygon) is True

    def test_outside_square(self):
        polygon = [(0, 0), (0, 10), (10, 10), (10, 0)]
        assert point_in_polygon(15, 15, polygon) is False

    def test_triangle(self):
        polygon = [(0, 0), (10, 5), (0, 10)]
        assert point_in_polygon(3, 5, polygon) is True
        assert point_in_polygon(0, 15, polygon) is False
