"""
Unit tests for LIDAR processor service.

Tests DEMFileManager, TerrainExtractor, and BatchLIDARProcessor classes.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from backend.services.lidar_processor import (
    DEMFileManager,
    TerrainExtractor,
    BatchLIDARProcessor,
    get_lidar_processor,
    RASTERIO_AVAILABLE
)


class TestDEMFileManager:
    """Tests for DEMFileManager"""
    
    def test_initialization_with_custom_dir(self):
        """Test initialization with custom data directory"""
        manager = DEMFileManager(data_dir="custom/path")
        assert manager.data_dir == "custom/path"
    
    def test_file_discovery_prioritizes_dem(self, tmp_path):
        """Test that DEM files are prioritized over hillshade"""
        # Create temp directory with test files
        (tmp_path / "tile_DEMHF.tif").touch()
        (tmp_path / "tile_HILSHD.tif").touch()
        
        manager = DEMFileManager(data_dir=str(tmp_path))
        
        # DEM should be listed first (dict preserves insertion order in Python 3.7+)
        file_list = list(manager.lidar_files.keys())
        assert "tile_DEMHF.tif" in file_list
        assert "tile_HILSHD.tif" in file_list
        assert file_list.index("tile_DEMHF.tif") < file_list.index("tile_HILSHD.tif")
    
    def test_no_files_found(self, tmp_path):
        """Test behavior when no TIF files found"""
        manager = DEMFileManager(data_dir=str(tmp_path))
        assert len(manager.lidar_files) == 0
    
    def test_only_tif_files_discovered(self, tmp_path):
        """Test that only TIF files are discovered"""
        (tmp_path / "tile.tif").touch()
        (tmp_path / "tile.tiff").touch()
        (tmp_path / "data.txt").touch()
        (tmp_path / "image.jpg").touch()
        
        manager = DEMFileManager(data_dir=str(tmp_path))
        assert len(manager.lidar_files) == 2
    
    @pytest.mark.skipif(not RASTERIO_AVAILABLE, reason="Rasterio not available")
    @patch('backend.services.lidar_processor.rasterio.open')
    def test_has_coverage_true(self, mock_open):
        """Test has_coverage returns True when point is in bounds"""
        # Mock rasterio dataset
        mock_src = Mock()
        mock_src.crs = 'EPSG:32145'
        mock_src.bounds = Mock(left=0, right=1000, bottom=0, top=1000)
        mock_open.return_value.__enter__.return_value = mock_src
        
        # Mock transform to return point in bounds
        with patch('backend.services.lidar_processor.transform') as mock_transform:
            mock_transform.return_value = ([500], [500])  # In bounds
            
            manager = DEMFileManager(data_dir="test")
            manager.lidar_files = {"test.tif": "test/test.tif"}
            
            assert manager.has_coverage(44.5, -72.7) is True
    
    @pytest.mark.skipif(not RASTERIO_AVAILABLE, reason="Rasterio not available")
    @patch('backend.services.lidar_processor.rasterio.open')
    def test_has_coverage_false(self, mock_open):
        """Test has_coverage returns False when point is out of bounds"""
        # Mock rasterio dataset
        mock_src = Mock()
        mock_src.crs = 'EPSG:32145'
        mock_src.bounds = Mock(left=0, right=1000, bottom=0, top=1000)
        mock_open.return_value.__enter__.return_value = mock_src
        
        # Mock transform to return point out of bounds
        with patch('backend.services.lidar_processor.transform') as mock_transform:
            mock_transform.return_value = ([2000], [2000])  # Out of bounds
            
            manager = DEMFileManager(data_dir="test")
            manager.lidar_files = {"test.tif": "test/test.tif"}
            
            assert manager.has_coverage(44.5, -72.7) is False
    
    def test_has_coverage_no_rasterio(self):
        """Test has_coverage returns False when rasterio unavailable"""
        if RASTERIO_AVAILABLE:
            pytest.skip("Rasterio is available")
        
        manager = DEMFileManager(data_dir="test")
        assert manager.has_coverage(44.5, -72.7) is False
    
    def test_get_files(self, tmp_path):
        """Test get_files returns discovered files"""
        (tmp_path / "tile1.tif").touch()
        (tmp_path / "tile2.tif").touch()
        
        manager = DEMFileManager(data_dir=str(tmp_path))
        files = manager.get_files()
        
        assert isinstance(files, dict)
        assert len(files) == 2


class TestTerrainExtractor:
    """Tests for TerrainExtractor"""
    
    def test_calculate_point_slope_flat(self):
        """Test slope calculation on flat terrain"""
        # Create flat elevation grid (all same elevation)
        elevation_grid = np.full((5, 5), 100.0)
        
        slope = TerrainExtractor._calculate_point_slope(
            elevation_grid, resolution_m=1.0, center_row=2, center_col=2
        )
        
        assert slope == pytest.approx(0.0, abs=0.1)
    
    def test_calculate_point_slope_45_degree(self):
        """Test slope calculation on 45-degree slope"""
        # Create elevation grid with 45° slope
        # For 45° slope: rise = run
        elevation_grid = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0]
        ])
        
        slope = TerrainExtractor._calculate_point_slope(
            elevation_grid, resolution_m=1.0, center_row=1, center_col=1
        )
        
        # Should be approximately 45 degrees
        assert slope == pytest.approx(45.0, abs=1.0)
    
    def test_calculate_point_slope_steep(self):
        """Test slope calculation on steep terrain"""
        # Create steep gradient
        elevation_grid = np.array([
            [0.0, 0.0, 0.0],
            [5.0, 5.0, 5.0],
            [10.0, 10.0, 10.0]
        ])
        
        slope = TerrainExtractor._calculate_point_slope(
            elevation_grid, resolution_m=1.0, center_row=1, center_col=1
        )
        
        # Should be steep (>45 degrees)
        assert slope > 45.0
        assert slope <= 90.0  # Clamped to maximum
    
    def test_calculate_point_aspect_north(self):
        """Test aspect calculation for north-facing slope"""
        # North-facing: lower elevation to the north (top)
        elevation_grid = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0]
        ])
        
        aspect = TerrainExtractor._calculate_point_aspect(
            elevation_grid, center_row=1, center_col=1
        )
        
        # North-facing should be around 180° (downslope to north)
        assert 135 < aspect < 225
    
    def test_calculate_point_aspect_south(self):
        """Test aspect calculation for south-facing slope"""
        # South-facing: higher elevation to the north (top)
        elevation_grid = np.array([
            [2.0, 2.0, 2.0],
            [1.0, 1.0, 1.0],
            [0.0, 0.0, 0.0]
        ])
        
        aspect = TerrainExtractor._calculate_point_aspect(
            elevation_grid, center_row=1, center_col=1
        )
        
        # South-facing should be around 0° (downslope to south)
        assert aspect < 45 or aspect > 315
    
    def test_calculate_point_aspect_east(self):
        """Test aspect calculation for east-facing slope"""
        # East-facing: lower elevation to the east (right)
        elevation_grid = np.array([
            [2.0, 1.0, 0.0],
            [2.0, 1.0, 0.0],
            [2.0, 1.0, 0.0]
        ])
        
        aspect = TerrainExtractor._calculate_point_aspect(
            elevation_grid, center_row=1, center_col=1
        )
        
        # East-facing should be around 270° (downslope to east)
        assert 225 < aspect < 315
    
    def test_calculate_point_aspect_west(self):
        """Test aspect calculation for west-facing slope"""
        # West-facing: lower elevation to the west (left)
        elevation_grid = np.array([
            [0.0, 1.0, 2.0],
            [0.0, 1.0, 2.0],
            [0.0, 1.0, 2.0]
        ])
        
        aspect = TerrainExtractor._calculate_point_aspect(
            elevation_grid, center_row=1, center_col=1
        )
        
        # West-facing should be around 90° (downslope to west)
        assert 45 < aspect < 135
    
    def test_calculate_point_aspect_flat(self):
        """Test aspect calculation on flat terrain (undefined)"""
        # Flat terrain should return 0 (undefined aspect)
        elevation_grid = np.full((3, 3), 100.0)
        
        aspect = TerrainExtractor._calculate_point_aspect(
            elevation_grid, center_row=1, center_col=1
        )
        
        assert aspect == 0.0
    
    def test_calculate_point_slope_edge_case(self):
        """Test slope calculation at grid edge"""
        elevation_grid = np.full((3, 3), 100.0)
        
        # Edge case: row=0 (too close to edge)
        slope = TerrainExtractor._calculate_point_slope(
            elevation_grid, resolution_m=1.0, center_row=0, center_col=1
        )
        assert slope == 0.0
    
    def test_calculate_point_aspect_edge_case(self):
        """Test aspect calculation at grid edge"""
        elevation_grid = np.full((3, 3), 100.0)
        
        # Edge case: col=2 (too close to edge)
        aspect = TerrainExtractor._calculate_point_aspect(
            elevation_grid, center_row=1, center_col=2
        )
        assert aspect == 0.0
    
    def test_calculate_slope_grid(self):
        """Test slope grid calculation"""
        # Create simple elevation grid with gradient
        elevation_grid = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0]
        ])
        
        slope_grid = TerrainExtractor.calculate_slope_grid(elevation_grid)
        
        assert slope_grid.shape == elevation_grid.shape
        assert np.all(slope_grid >= 0)
    
    @pytest.mark.skipif(not RASTERIO_AVAILABLE, reason="Rasterio not available")
    @patch('backend.services.lidar_processor.rasterio.open')
    @patch('backend.services.lidar_processor.transform')
    def test_extract_point_terrain_success(self, mock_transform, mock_open):
        """Test successful point terrain extraction"""
        # Mock rasterio dataset
        mock_src = Mock()
        mock_src.crs = 'EPSG:32145'
        mock_src.bounds = Mock(left=0, right=1000, bottom=0, top=1000)
        mock_src.res = (0.35, 0.35)
        mock_src.width = 1000
        mock_src.height = 1000
        mock_src.index.return_value = (500, 500)
        
        # Create test elevation grid
        elevation_grid = np.full((200, 200), 100.0)
        mock_src.read.return_value = elevation_grid
        
        mock_open.return_value.__enter__.return_value = mock_src
        mock_transform.return_value = ([500], [500])
        
        lidar_files = {"tile_DEMHF.tif": "test/tile_DEMHF.tif"}
        result = TerrainExtractor.extract_point_terrain(44.5, -72.7, lidar_files)
        
        assert result is not None
        assert result['coverage'] is True
        assert result['source'] == 'LIDAR_DEM'
        assert result['accurate_slopes'] is True
        assert 'slope' in result
        assert 'aspect' in result
        assert 'elevation' in result
    
    @pytest.mark.skipif(not RASTERIO_AVAILABLE, reason="Rasterio not available")
    def test_extract_point_terrain_no_coverage(self):
        """Test point terrain extraction with no coverage"""
        lidar_files = {}
        result = TerrainExtractor.extract_point_terrain(44.5, -72.7, lidar_files)
        assert result is None
    
    def test_extract_point_terrain_no_rasterio(self):
        """Test point terrain extraction when rasterio unavailable"""
        if RASTERIO_AVAILABLE:
            pytest.skip("Rasterio is available")
        
        result = TerrainExtractor.extract_point_terrain(
            44.5, -72.7, {"test.tif": "test/test.tif"}
        )
        assert result is None


class TestBatchLIDARProcessor:
    """Tests for BatchLIDARProcessor"""
    
    def test_batch_extract_empty_coordinates(self):
        """Test batch extraction with no coordinates"""
        manager = DEMFileManager(data_dir="test")
        extractor = TerrainExtractor()
        processor = BatchLIDARProcessor(manager, extractor)
        
        result = processor.batch_extract([])
        assert result == {}
    
    @patch.object(TerrainExtractor, 'extract_point_terrain')
    def test_batch_extract_success(self, mock_extract):
        """Test successful batch extraction"""
        # Mock terrain extraction
        mock_extract.return_value = {
            'slope': 15.0,
            'aspect': 180.0,
            'elevation': 500.0,
            'coverage': True
        }
        
        manager = DEMFileManager(data_dir="test")
        extractor = TerrainExtractor()
        processor = BatchLIDARProcessor(manager, extractor)
        
        coordinates = [(44.5, -72.7), (44.6, -72.8)]
        result = processor.batch_extract(coordinates)
        
        assert len(result) == 2
        assert "44.500000,-72.700000" in result
        assert "44.600000,-72.800000" in result
        assert result["44.500000,-72.700000"]['coverage'] is True
    
    @patch.object(TerrainExtractor, 'extract_point_terrain')
    def test_batch_extract_no_coverage(self, mock_extract):
        """Test batch extraction with no coverage"""
        # Mock terrain extraction returning None
        mock_extract.return_value = None
        
        manager = DEMFileManager(data_dir="test")
        extractor = TerrainExtractor()
        processor = BatchLIDARProcessor(manager, extractor)
        
        coordinates = [(44.5, -72.7)]
        result = processor.batch_extract(coordinates)
        
        assert len(result) == 1
        assert result["44.500000,-72.700000"]['coverage'] is False
    
    @patch.object(TerrainExtractor, 'extract_point_terrain')
    def test_batch_extract_mixed_coverage(self, mock_extract):
        """Test batch extraction with mixed coverage"""
        # Mock terrain extraction with alternating coverage
        def side_effect(*args):
            lat = args[0]
            if lat == 44.5:
                return {'slope': 15.0, 'coverage': True}
            return None
        
        mock_extract.side_effect = side_effect
        
        manager = DEMFileManager(data_dir="test")
        extractor = TerrainExtractor()
        processor = BatchLIDARProcessor(manager, extractor)
        
        coordinates = [(44.5, -72.7), (44.6, -72.8)]
        result = processor.batch_extract(coordinates)
        
        assert len(result) == 2
        assert result["44.500000,-72.700000"]['coverage'] is True
        assert result["44.600000,-72.800000"]['coverage'] is False


class TestGetLIDARProcessor:
    """Tests for singleton get_lidar_processor()"""
    
    def test_get_lidar_processor_returns_tuple(self):
        """Test get_lidar_processor returns tuple of three instances"""
        result = get_lidar_processor()
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], DEMFileManager)
        assert isinstance(result[1], TerrainExtractor)
        assert isinstance(result[2], BatchLIDARProcessor)
    
    def test_get_lidar_processor_singleton(self):
        """Test get_lidar_processor returns same instance"""
        result1 = get_lidar_processor()
        result2 = get_lidar_processor()
        
        # Should be same instances
        assert result1[0] is result2[0]
        assert result1[1] is result2[1]
        assert result1[2] is result2[2]
