#!/usr/bin/env python3
"""
Property Hotspot Analyzer
Phase 1: Use LIDAR terrain analysis to identify promising areas
Phase 2: Run API predictions only on the best LIDAR-identified locations
Phase 3: Find hotspots where predictions converge

This two-phase approach is much more efficient than running predictions everywhere.
"""

import requests
import json
import numpy as np
import math
from shapely.geometry import Point, Polygon
from sklearn.cluster import DBSCAN
from datetime import datetime
import time
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import folium
from pathlib import Path
import sys
import os

# Add project root and backend to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

try:
    from backend.services.lidar_processor import DEMFileManager, TerrainExtractor
    LIDAR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  LIDAR not available: {e}")
    LIDAR_AVAILABLE = False

# Import Google Earth Engine for land cover filtering
try:
    import ee
    # Initialize GEE with project
    try:
        # Try to use existing backend initialization
        from gee_docker_setup import GEESetup
        gee_setup = GEESetup()
        if gee_setup.initialize():
            GEE_AVAILABLE = True
            print("✅ Google Earth Engine initialized via backend")
        else:
            GEE_AVAILABLE = False
            print("⚠️  GEE backend initialization failed - will skip land cover filtering")
    except Exception as init_error:
        # Fallback: skip GEE if it fails
        print(f"⚠️  GEE initialization failed: {init_error}")
        print("⚠️  Will skip land cover filtering (all points will be analyzed)")
        GEE_AVAILABLE = False
except ImportError:
    print("⚠️  Google Earth Engine not installed - will skip land cover filtering")
    GEE_AVAILABLE = False

# Property boundaries
PROPERTY_CORNERS = {
    'NW': (44.35061, -72.92899),
    'NE': (44.34347, -72.90646),
    'SE': (44.3302, -72.91153),
    'SW': (44.33597, -72.93736)
}

# API Configuration
BACKEND_URL = "http://localhost:8000"
PREDICTION_ENDPOINT = f"{BACKEND_URL}/predict"

class PropertyHotspotAnalyzer:
    def __init__(self, corners: Dict[str, Tuple[float, float]]):
        """Initialize with property corner coordinates."""
        self.corners = corners
        # Create polygon from corners (NW -> NE -> SE -> SW -> NW)
        # Shapely expects (lon, lat) order!
        corner_order = ['NW', 'NE', 'SE', 'SW']
        polygon_coords = [(corners[c][1], corners[c][0]) for c in corner_order]  # (lon, lat)
        self.property_polygon = Polygon(polygon_coords)
        
        self.grid_points = []
        self.lidar_analysis = []
        self.candidate_points = []
        self.predictions = []
        self.all_stands = []
        self.hotspots = []
        self.buck_bed = None
        
        # Initialize LIDAR if available
        if LIDAR_AVAILABLE:
            self.dem_manager = DEMFileManager()
            self.terrain_extractor = TerrainExtractor()
            print("✅ LIDAR system initialized")
        else:
            print("⚠️  LIDAR unavailable - will use API only")
            self.dem_manager = None
            self.terrain_extractor = None
        
    def generate_grid(self, num_points: int = 30, buffer_meters: float = 0) -> List[Tuple[float, float]]:
        """Generate a grid of points within the property boundary.
        
        Args:
            num_points: Number of points to generate
            buffer_meters: DEPRECATED - not used, kept for compatibility
        """
        print(f"\n🗺️  Generating {num_points} prediction points within property...")
        
        # Get bounding box
        lats = [c[0] for c in self.corners.values()]
        lons = [c[1] for c in self.corners.values()]
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # Generate grid - use at least 5x5 to get interior points
        grid_size = max(5, int(np.sqrt(num_points * 2)))
        lat_points = np.linspace(min_lat, max_lat, grid_size)
        lon_points = np.linspace(min_lon, max_lon, grid_size)
        
        # Filter points inside polygon (NO BUFFER - we'll filter stands later)
        valid_points = []
        for lat in lat_points:
            for lon in lon_points:
                point = Point(lon, lat)
                if self.property_polygon.contains(point):
                    valid_points.append((lat, lon))
        
        # Trim to desired number
        if len(valid_points) > num_points:
            # Sample evenly
            indices = np.linspace(0, len(valid_points)-1, num_points, dtype=int)
            valid_points = [valid_points[i] for i in indices]
        
        self.grid_points = valid_points
        print(f"✅ Generated {len(self.grid_points)} valid points inside property")
        return self.grid_points
    
    def is_inside_property(self, lat: float, lon: float) -> bool:
        """Check if point is inside property boundary."""
        point = Point(lon, lat)
        return self.property_polygon.contains(point)
    
    def get_land_cover(self, lat: float, lon: float) -> Dict:
        """Get land cover classification from GEE NLCD with retry logic.
        
        Returns:
            dict with 'class_id', 'class_name', 'is_forest' fields
        """
        if not GEE_AVAILABLE:
            return {'class_id': -1, 'class_name': 'unknown', 'is_forest': True}  # Default to forest if GEE unavailable
        
        # Retry up to 3 times with increasing delays
        for attempt in range(3):
            try:
                point = ee.Geometry.Point([lon, lat])
                
                # Use NLCD 2021 (National Land Cover Database)
                nlcd = ee.Image('USGS/NLCD_RELEASES/2021_REL/NLCD/2021')
                landcover = nlcd.select('landcover')
                
                # Sample land cover at point (with 60m buffer for better sampling)
                buffer = point.buffer(60)
                lc_sample = landcover.reduceRegion(
                    reducer=ee.Reducer.mode(),
                    geometry=buffer,
                    scale=30,
                    maxPixels=1e6
                ).getInfo()
                
                class_id = lc_sample.get('landcover', -1)
                
                # NLCD class definitions
                nlcd_classes = {
                    11: 'Open Water',
                    21: 'Developed Open Space',
                    22: 'Developed Low Intensity',
                    23: 'Developed Medium Intensity',
                    24: 'Developed High Intensity',
                    31: 'Barren Land',
                    41: 'Deciduous Forest',
                    42: 'Evergreen Forest',
                    43: 'Mixed Forest',
                    52: 'Shrub/Scrub',
                    71: 'Grassland/Herbaceous',
                    81: 'Pasture/Hay',
                    82: 'Cultivated Crops',
                    90: 'Woody Wetlands',
                    95: 'Emergent Herbaceous Wetlands'
                }
                
                class_name = nlcd_classes.get(class_id, f'Unknown ({class_id})')
                
                # Forest classes: 41 (Deciduous), 42 (Evergreen), 43 (Mixed)
                # Also include 52 (Shrub) and 90 (Woody Wetlands) as viable hunting areas
                is_forest = class_id in [41, 42, 43, 52, 90]
                
                return {
                    'class_id': class_id,
                    'class_name': class_name,
                    'is_forest': is_forest
                }
                
            except KeyboardInterrupt:
                raise  # Don't retry on manual interruption
            except Exception as e:
                if attempt < 2:  # Try again
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
                    continue
                else:  # Final attempt failed
                    print(f"  ⚠️  GEE land cover query failed after 3 attempts for ({lat:.6f}, {lon:.6f}): {e}")
                    return {'class_id': -1, 'class_name': 'error', 'is_forest': True}  # Default to forest on error
    
    def score_grid_with_lidar(self) -> List[Dict]:
        """Score all grid points using LIDAR terrain analysis.
        
        Returns list of scored points with terrain features.
        Scoring uses PEAK RUT strategies for mature buck behavior:
        - Travel corridors (40%): Saddles, gentle slopes, doe movement routes
        - Rut interception (35%): Terrain funnels, buck cruising zones (PEAK)
        - Bedding proximity (20%): Near doe bedding, not buck bedding
        - Feeding areas (5%): Minimal - bucks don't eat during peak rut
        """
        if not LIDAR_AVAILABLE or not self.dem_manager:
            print("⚠️  LIDAR not available - skipping terrain scoring")
            return []
        
        print(f"\n🏔️  Analyzing terrain for {len(self.grid_points)} points using LIDAR...")
        
        # Get LIDAR files
        lidar_files = self.dem_manager.lidar_files
        if not lidar_files:
            print("⚠️  No LIDAR files found")
            return []
        
        print(f"✅ Found {len(lidar_files)} LIDAR DEM files")
        
        scored_points = []
        
        # First pass: collect all terrain data (NO land cover filtering yet - too slow)
        all_terrain = []
        
        print(f"  📊 Extracting terrain data from LIDAR...")
        
        for i, (lat, lon) in enumerate(self.grid_points, 1):
            if i % 100 == 0:
                print(f"    [{i}/{len(self.grid_points)}] terrain points extracted")
            
            try:
                terrain = self.terrain_extractor.extract_point_terrain(
                    lat=lat, lon=lon, lidar_files=lidar_files, sample_radius_m=30
                )
                if terrain and terrain.get('coverage', 0) > 0:
                    all_terrain.append({
                        'lat': lat, 'lon': lon,
                        'slope': terrain.get('slope', 0),
                        'aspect': terrain.get('aspect', 0),
                        'elevation': terrain.get('elevation', 0),
                        'resolution': terrain.get('resolution_m', 0)
                    })
            except:
                continue
        
        if not all_terrain:
            print("⚠️  No terrain data extracted")
            return []
        
        # Calculate elevation statistics for relative scoring
        elevations = [t['elevation'] for t in all_terrain]
        min_elev = min(elevations)
        max_elev = max(elevations)
        elev_range = max_elev - min_elev if max_elev > min_elev else 1
        
        print(f"   Elevation range: {min_elev:.1f}m - {max_elev:.1f}m (Δ{elev_range:.1f}m)")
        
        # Second pass: score each point with multiple strategies
        for i, t in enumerate(all_terrain, 1):
            slope = t['slope']
            aspect = t['aspect']
            elevation = t['elevation']
            
            # Normalize elevation (0-1)
            elev_normalized = (elevation - min_elev) / elev_range if elev_range > 0 else 0.5
            
            # STRATEGY 1: Bedding Score (max 20 points) - Near doe bedding
            bedding_score = 0
            # Slope preference for bedding (10-30°)
            if 10 <= slope <= 30:
                bedding_score += 7
            elif 5 <= slope < 10 or 30 < slope <= 40:
                bedding_score += 5
            elif slope > 0:
                bedding_score += 2
            # South-facing thermal advantage (135-225°)
            if 135 <= aspect <= 225:
                bedding_score += 6
            elif 90 <= aspect < 135 or 225 < aspect <= 270:
                bedding_score += 4
            # Higher elevation for security
            bedding_score += elev_normalized * 3
            
            # STRATEGY 2: Travel Corridor Score (max 40 points) - PRIMARY RUT FOCUS
            travel_score = 0
            
            # Terrain Feature Detection
            is_saddle = (0.35 <= elev_normalized <= 0.65 and slope <= 8)  # Low point between peaks
            is_bench = (5 <= slope <= 10 and 0.3 <= elev_normalized <= 0.7)  # Flat area on slope (Tightened to 10 deg)
            is_funnel = (10 <= slope <= 25)  # Terrain that narrows travel
            is_ridge = (elev_normalized >= 0.7 and slope <= 12)  # High flat area
            
            # Gentle slopes for easy travel (0-15°)
            if slope <= 5:
                travel_score += 16
            elif 5 < slope <= 15:
                travel_score += 13
            elif 15 < slope <= 25:
                travel_score += 7
            
            # Terrain features bonus
            if is_saddle:
                travel_score += 15  # Saddles are prime travel corridors (Increased)
            elif is_bench:
                travel_score += 12   # Benches are easy walking routes (Increased)
            elif is_ridge:
                travel_score += 6   # Ridges for buck cruising
            else:
                # Mid-elevation general bonus
                mid_elevation_bonus = 1 - abs(elev_normalized - 0.5) * 2
                travel_score += mid_elevation_bonus * 4
            
            # Moderate slope transitions (not flat, not steep)
            if 3 <= slope <= 12:
                travel_score += 10
            
            # STRATEGY 3: Feeding Area Score (max 5 points) - Does feed here
            feeding_score = 0
            # Flat to gentle terrain (0-8°) - minimal importance during peak rut
            if slope <= 8:
                feeding_score += 3
            elif 8 < slope <= 15:
                feeding_score += 1
            # Lower elevation (valleys, flats)
            feeding_score += (1 - elev_normalized) * 2
            
            # STRATEGY 4: Rut Interception Score (max 35 points) - PEAK RUT BUCK CRUISING
            rut_score = 0
            
            # Leeward Ridge Cruising (East/South slopes near top)
            # Prevailing wind is West/NW, so bucks cruise East/SE side
            if elev_normalized >= 0.6 and (90 <= aspect <= 180):
                rut_score += 15
                
            # Moderate elevation (where bucks cruise below doe bedding)
            if 0.3 <= elev_normalized <= 0.7:
                rut_score += 18  # Increased - prime cruising elevation
            # Terrain that creates funnels (moderate slope changes)
            if is_funnel:  # Use detected funnel feature
                rut_score += 17  # Increased - funnels force buck travel
            elif 5 <= slope <= 20:
                rut_score += 12
            
            # TOTAL SCORE (max 100)
            total_score = bedding_score + travel_score + feeding_score + rut_score
            
            scored_points.append({
                'lat': t['lat'],
                'lon': t['lon'],
                'score': total_score,
                'bedding_score': bedding_score,
                'travel_score': travel_score,
                'feeding_score': feeding_score,
                'rut_score': rut_score,
                'slope': slope,
                'aspect': aspect,
                'elevation': elevation,
                'resolution': t['resolution']
            })
            
            if (i % 1000) == 0:
                print(f"  [{i}/{len(all_terrain)}] Scored: slope={slope:.1f}°, aspect={aspect:.0f}°, elev={elevation:.1f}m → {total_score:.0f}/100 "
                      f"(B:{bedding_score:.0f} T:{travel_score:.0f} F:{feeding_score:.0f} R:{rut_score:.0f})")
        
        # Sort by total score descending
        scored_points.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n✅ LIDAR analysis complete: {len(scored_points)} points scored")
        if scored_points:
            top = scored_points[0]
            print(f"   Top score: {top['score']:.0f}/100 (Bedding:{top['bedding_score']:.0f}, Travel:{top['travel_score']:.0f}, Feed:{top['feeding_score']:.0f}, Rut:{top['rut_score']:.0f})")
            top5_avg = np.mean([p['score'] for p in scored_points[:5]])
            print(f"   Top 5 avg: {top5_avg:.0f}/100")
        
        self.lidar_analysis = scored_points
        return scored_points
    
    def run_prediction(self, lat: float, lon: float, 
                      hunt_date: str = None, 
                      hunt_time: str = "morning") -> Dict:
        """Run prediction for a single point."""
        if hunt_date is None:
            hunt_date = datetime.now().strftime("%Y-%m-%d")
        
        # Convert hunt_time to datetime format expected by API
        period_times = {
            "morning": "06:00:00",
            "midday": "12:00:00",
            "evening": "18:00:00"
        }
        time_str = period_times.get(hunt_time, "06:00:00")
        
        payload = {
            "lat": lat,
            "lon": lon,
            "date_time": f"{hunt_date}T{time_str}",
            "hunt_period": hunt_time,
            "season": "rut",
            "fast_mode": True
        }
        
        try:
            response = requests.post(PREDICTION_ENDPOINT, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error for point ({lat:.5f}, {lon:.5f}): {e}")
            return None
    
    def run_batch_predictions(self, delay: float = 1.0) -> List[Dict]:
        """Run predictions for all grid points."""
        print(f"\n🔄 Running predictions for {len(self.grid_points)} points...")
        print(f"⏱️  Estimated time: ~{len(self.grid_points) * (delay + 60) / 60:.1f} minutes (60s per prediction + {delay}s delay)")
        
        results = []
        for i, (lat, lon) in enumerate(self.grid_points, 1):
            print(f"\n[{i}/{len(self.grid_points)}] Predicting for ({lat:.5f}, {lon:.5f})...", flush=True)
            start_time = time.time()
            
            result = self.run_prediction(lat, lon)
            elapsed = time.time() - start_time
            
            if result:
                results.append({
                    'source_point': (lat, lon),
                    'prediction': result
                })
                print(f"✅ Success - {elapsed:.1f}s")
            else:
                print(f"❌ Failed - {elapsed:.1f}s")
            
            # Rate limiting
            if i < len(self.grid_points):
                time.sleep(delay)
        
        self.predictions = results
        print(f"\n✅ Completed {len(results)}/{len(self.grid_points)} successful predictions")
        return results
    
    def extract_all_stands(self) -> List[Dict]:
        """Extract all predicted stand locations from all predictions."""
        print(f"\n📍 Extracting stand locations from predictions...")
        
        all_stands: List[Dict] = []
        for pred in self.predictions:
            source = pred['source_point']
            prediction_data = pred['prediction']
            
            # Handle API response wrapper (response has 'success', 'data', 'error' structure)
            if 'data' in prediction_data:
                prediction_data = prediction_data['data']
            
            # Extract optimized points (stand sites)
            opt_points = prediction_data.get('optimized_points', {})
            stand_sites = opt_points.get('stand_sites', []) if isinstance(opt_points, dict) else []
            for i, stand in enumerate(stand_sites, 1):
                stand_lat = stand.get('lat')
                stand_lon = stand.get('lon')
                if stand_lat is None or stand_lon is None:
                    continue

                all_stands.append({
                    'stand_num': i,
                    'lat': float(stand_lat),
                    'lon': float(stand_lon),
                    'score': float(stand.get('score', 0) or 0),
                    'strategy': stand.get('strategy', 'Unknown'),
                    'source_point': source,
                    'inside_property': self.is_inside_property(float(stand_lat), float(stand_lon)),
                    'source': 'optimized_points'
                })

            # ALSO ingest mature_buck_analysis stand recommendations if present (some runs may omit optimized_points)
            # These are kept separate via 'source' and can be used in fallbacks.
            mba = prediction_data.get('mature_buck_analysis', {})
            stand_recs = mba.get('stand_recommendations', []) if isinstance(mba, dict) else []
            for i, rec in enumerate(stand_recs, 1):
                coords = rec.get('coordinates', {}) if isinstance(rec, dict) else {}
                stand_lat = coords.get('lat')
                stand_lon = coords.get('lon')
                if stand_lat is None or stand_lon is None:
                    continue

                all_stands.append({
                    'stand_num': i,
                    'lat': float(stand_lat),
                    'lon': float(stand_lon),
                    # Normalize any confidence-like value onto the same 0-10 band used elsewhere
                    'score': float(rec.get('confidence', 0) or 0) / 10.0,
                    'strategy': rec.get('type', rec.get('strategy', 'Stand Recommendation')),
                    'source_point': source,
                    'inside_property': self.is_inside_property(float(stand_lat), float(stand_lon)),
                    'source': 'mature_buck_analysis'
                })
        
        self.all_stands = all_stands
        inside_count = sum(1 for s in all_stands if s['inside_property'])
        print(f"✅ Extracted {len(all_stands)} total stand predictions")
        print(f"   📍 {inside_count} inside property, {len(all_stands) - inside_count} outside")
        
        return all_stands

    def _cluster_points_haversine(self, points: List[Dict], epsilon_meters: float, min_samples: int) -> Tuple[np.ndarray, np.ndarray]:
        """Cluster lat/lon points using haversine distance (meters-correct).

        Returns:
            coords_deg: Nx2 array in degrees
            labels: DBSCAN cluster labels
        """
        if not points:
            return np.empty((0, 2)), np.array([])

        coords_deg = np.array([[p['lat'], p['lon']] for p in points], dtype=float)
        coords_rad = np.radians(coords_deg)
        eps_rad = float(epsilon_meters) / 6371000.0  # Earth radius (m)

        clustering = DBSCAN(eps=eps_rad, min_samples=min_samples, metric='haversine')
        labels = clustering.fit_predict(coords_rad)
        return coords_deg, labels
    
    def find_clusters(self, epsilon_meters: float = 50, min_samples: int = 3) -> List[Dict]:
        """Find clusters of predicted stands using DBSCAN."""
        print(f"\n🎯 Finding hotspots (clusters within {epsilon_meters}m, min {min_samples} predictions)...")
        
        if not self.all_stands:
            print("❌ No stands to cluster")
            return []
        
        # Run DBSCAN clustering in meters-correct space
        coords, labels = self._cluster_points_haversine(self.all_stands, epsilon_meters, min_samples)
        
        # Group stands by cluster
        clusters = {}
        for idx, label in enumerate(labels):
            if label == -1:  # Noise point
                continue
            
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(self.all_stands[idx])
        
        print(f"✅ Found {len(clusters)} hotspot clusters")
        
        # Calculate cluster statistics
        hotspots = []
        for cluster_id, stands in clusters.items():
            # Calculate center
            center_lat = np.mean([s['lat'] for s in stands])
            center_lon = np.mean([s['lon'] for s in stands])
            
            # Check if center is inside property
            inside = self.is_inside_property(center_lat, center_lon)
            
            hotspot = {
                'cluster_id': cluster_id,
                'center_lat': center_lat,
                'center_lon': center_lon,
                'num_predictions': len(stands),
                'avg_score': float(np.mean([float(s.get('score', 0) or 0) for s in stands])) if stands else 0.0,
                'strategies': list({s.get('strategy', 'Unknown') for s in stands}),
                'inside_property': inside,
                'stands': stands
            }
            hotspots.append(hotspot)
        
        self.hotspots = hotspots
        return hotspots

    def get_baseline_stand(self, epsilon_meters: float = 60, min_samples: int = 3) -> Dict:
        """Return the single most conservative, consensus-based stand location.

        Heuristic (simple + robust):
        - Prefer stands inside property.
        - Prefer the densest consensus cluster (most predictions within epsilon).
        - Choose the medoid (closest-to-centroid) within that cluster.
        - Fallback to top-scoring inside-property stand if no cluster forms.
        """
        inside = [s for s in self.all_stands if s.get('inside_property')]
        if not inside:
            return {}

        coords, labels = self._cluster_points_haversine(inside, epsilon_meters, min_samples)

        # Build clusters
        clusters: Dict[int, List[int]] = {}
        for idx, label in enumerate(labels):
            if label == -1:
                continue
            clusters.setdefault(int(label), []).append(idx)

        # No consensus cluster: pick the highest score inside property
        if not clusters:
            best = max(inside, key=lambda s: float(s.get('score', 0) or 0))
            return {
                'lat': best['lat'],
                'lon': best['lon'],
                'reason': 'No consensus cluster formed; selected highest-scoring inside-property stand.',
                'supporting_predictions': 1,
                'sources': sorted({best.get('source', 'unknown')}),
            }

        # Pick densest cluster; tie-break by mean score
        best_cluster_id = None
        best_cluster_key = None
        for cluster_id, idxs in clusters.items():
            scores = [float(inside[i].get('score', 0) or 0) for i in idxs]
            key = (len(idxs), float(np.mean(scores) if scores else 0.0))
            if best_cluster_key is None or key > best_cluster_key:
                best_cluster_key = key
                best_cluster_id = cluster_id

        idxs = clusters[best_cluster_id]
        cluster_coords = coords[idxs]
        centroid = np.mean(cluster_coords, axis=0)
        # Medoid = point with minimum distance to centroid (in meters)
        best_i = None
        best_dist = None
        for i in idxs:
            d = self.calculate_distance(inside[i]['lat'], inside[i]['lon'], float(centroid[0]), float(centroid[1]))
            if best_dist is None or d < best_dist:
                best_dist = d
                best_i = i

        chosen = inside[best_i]
        sources = sorted({inside[i].get('source', 'unknown') for i in idxs})
        return {
            'lat': chosen['lat'],
            'lon': chosen['lon'],
            'reason': f"Selected medoid of densest consensus cluster (n={len(idxs)} within {epsilon_meters}m).",
            'supporting_predictions': len(idxs),
            'sources': sources,
        }
    
    def get_best_time(self, strategies: List[str]) -> str:
        """Determine best time to hunt based on strategies."""
        strategies_lower = [s.lower() for s in strategies]
        
        is_bedding = any('bedding' in s for s in strategies_lower)
        is_feeding = any('feeding' in s for s in strategies_lower)
        is_rut = any('rut' in s or 'travel' in s or 'corridor' in s for s in strategies_lower)
        
        if is_rut:
            return "All Day"
        elif is_bedding and is_feeding:
            return "All Day"
        elif is_bedding:
            return "Morning (AM)"
        elif is_feeding:
            return "Evening (PM)"
        else:
            return "Morning/Evening"

    def get_best_wind(self, aspect: float) -> str:
        """Determine best wind direction based on slope aspect.
        General rule: Hunt crosswinds relative to slope direction.
        """
        if aspect is None:
            return "Variable"
            
        # Aspect is direction slope faces (0=N, 90=E, 180=S, 270=W)
        # We want wind blowing ACROSS the slope, not up (thermal) or down (swirling)
        
        if 315 <= aspect or aspect < 45:  # North facing
            return "West or East"
        elif 45 <= aspect < 135:  # East facing
            return "North or South"
        elif 135 <= aspect < 225:  # South facing
            return "West or East"
        elif 225 <= aspect < 315:  # West facing
            return "North or South"
        return "Variable"

    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """Calculate bearing between two points."""
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        d_lon = lon2 - lon1
        
        x = math.sin(d_lon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(d_lon))
        
        initial_bearing = math.atan2(x, y)
        
        # Convert to degrees
        initial_bearing = math.degrees(initial_bearing)
        
        # Normalize to 0-360
        bearing = (initial_bearing + 360) % 360
        return bearing

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in meters."""
        R = 6371000  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c

    def identify_buck_bedroom(self, top_hotspots: List[Dict] = None):
        """
        Identify the single best mature buck bedding site by reverse-engineering 
        from the identified Rut Hotspots.
        
        Logic:
        1. Find 'Rut Center' (centroid of top hotspots).
        2. Find a secure ridge (High/Steep/Leeward) that overlooks this center.
        3. Ideal distance: 200-600m (Satellite Ridge).
        """
        if not self.lidar_analysis:
            return

        print(f"\n👑 Reverse-Engineering Mature Buck Bedding (The 'Rut Command Center')...")
        
        if not top_hotspots:
            print("   ⚠️ No hotspots provided for reverse analysis. Using terrain-only mode.")
            return

        # 1. Calculate Rut Center
        lats = [h.get('center_lat', h.get('lat')) for h in top_hotspots]
        lons = [h.get('center_lon', h.get('lon')) for h in top_hotspots]
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)
        
        print(f"   📍 Rut Activity Center: ({center_lat:.6f}, {center_lon:.6f})")
        print(f"      (Calculated from centroid of Top {len(top_hotspots)} Hotspots)")

        # Get elevation stats for property
        elevations = [p['elevation'] for p in self.lidar_analysis]
        max_elev = max(elevations)
        min_elev = min(elevations)
        elev_range = max_elev - min_elev
        
        # Threshold for "High Ground" (Top 30% - slightly expanded search)
        high_ground_threshold = min_elev + (elev_range * 0.70)
        
        candidates = []
        
        for p in self.lidar_analysis:
            # 1. Security Filter (The "Shield")
            # Must be high ground
            if p['elevation'] < high_ground_threshold:
                continue
            
            # Must be steep enough (12-35 degrees)
            if not (12 <= p['slope'] <= 35):
                continue
                
            # Must be Leeward (East/South-East/South) for West Wind
            # 45 (NE) to 200 (SSW)
            if not (45 <= p['aspect'] <= 200):
                continue
            
            # 2. Proximity Filter (The "Commute")
            # Calculate distance to Rut Center
            # Approx distance in meters (1 deg lat ~ 111km)
            d_lat = (p['lat'] - center_lat) * 111000
            d_lon = (p['lon'] - center_lon) * 111000 * np.cos(np.radians(center_lat))
            dist_meters = np.sqrt(d_lat**2 + d_lon**2)
            
            # Ideal: 200m - 600m (Staging distance)
            if dist_meters < 150: continue # Too close to the party
            if dist_meters > 800: continue # Too far to commute
            
            # 3. Scoring
            score = 0
            
            # Security Score (50%)
            elev_score = ((p['elevation'] - min_elev) / elev_range) * 25
            slope_score = (1 - abs(p['slope'] - 20)/20) * 25 # Peak at 20 deg
            security_score = elev_score + slope_score
            
            # Strategic Score (50%)
            # Distance: Peak at 350m
            dist_score = (1 - abs(dist_meters - 350)/450) * 30
            
            # Aspect Bonus (SE is best for morning thermal + leeward)
            aspect_diff = abs(p['aspect'] - 135)
            if aspect_diff > 180: aspect_diff = 360 - aspect_diff
            aspect_score = ((180 - aspect_diff) / 180) * 20
            
            total_score = security_score + dist_score + aspect_score
            
            candidates.append({
                'point': p,
                'score': total_score,
                'dist': dist_meters,
                'security': security_score,
                'strategic': dist_score + aspect_score
            })
            
        if not candidates:
            print("   ⚠️ No perfect 'Hub' bedding sites found. Buck may be bedding off-property or in non-ideal terrain.")
            self.buck_bed = None
            return

        # Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        best = candidates[0]
        p = best['point']
        
        self.buck_bed = {
            'lat': p['lat'], 
            'lon': p['lon'], 
            'elevation': p['elevation'],
            'score': best['score']
        }
        
        print(f"\n   ✅ TARGET ACQUIRED: The 'General's Quarters'")
        print(f"      Location: ({p['lat']:.6f}, {p['lon']:.6f})")
        print(f"      Distance to Rut Center: {best['dist']:.0f}m (Perfect Staging Distance)")
        print(f"      Elevation: {p['elevation']:.1f}m (Overwatch Position)")
        print(f"      Slope: {p['slope']:.1f}° | Aspect: {p['aspect']:.0f}°")
        print(f"      Tactical Score: {best['score']:.1f}/100")
        print(f"      Analysis: This bed allows him to scent-check the hotspot cluster from {best['dist']:.0f}m away")
        print(f"                while remaining virtually invisible on high, steep, leeward terrain.")

    def rank_hotspots(self) -> List[Dict]:
        """Rank hotspots by quality and return top 5 inside property."""
        print(f"\n🏆 Ranking hotspots...")
        
        # Filter to only hotspots inside property
        valid_hotspots = [h for h in self.hotspots if h['inside_property']]
        
        print(f"   📍 {len(valid_hotspots)} hotspots inside property boundary")
        
        # FALLBACK: If no clusters, use top individual stands
        if len(valid_hotspots) == 0:
            print(f"\n⚠️  No clusters found - showing top 5 individual stands instead")
            inside_stands = [s for s in self.all_stands if s['inside_property']]
            
            if len(inside_stands) == 0:
                print(f"   ❌ No stands inside property!")
                return []
            
            # Sort by score
            top_stands = sorted(inside_stands, key=lambda s: s['score'], reverse=True)[:5]
            
            print(f"\n✅ Top 5 Stand Locations (all inside property):")
            for i, stand in enumerate(top_stands, 1):
                print(f"\n   #{i} - ({stand['lat']:.6f}, {stand['lon']:.6f})")
                print(f"      Score: {stand['score']:.1f}/10")
                print(f"      Strategy: {stand['strategy']}")
                print(f"      Stand #{stand['stand_num']} from prediction at ({stand['source_point'][0]:.6f}, {stand['source_point'][1]:.6f})")
            
            # Convert to hotspot format for compatibility
            top_5 = []
            for stand in top_stands:
                # Get LIDAR score for this stand's source point
                source_lat, source_lon = stand['source_point']
                matching = [p for p in self.lidar_analysis 
                           if abs(p['lat'] - source_lat) < 0.0001 and abs(p['lon'] - source_lon) < 0.0001]
                terrain_quality = matching[0]['score'] if matching else 50
                aspect = matching[0]['aspect'] if matching else None
                
                strategies = [stand['strategy']]
                best_time = self.get_best_time(strategies)
                best_wind = self.get_best_wind(aspect)
                
                top_5.append({
                    'center_lat': stand['lat'],
                    'center_lon': stand['lon'],
                    'num_predictions': 1,
                    'avg_score': stand['score'],
                    'strategies': strategies,
                    'inside_property': True,
                    'total_score': terrain_quality + (stand['score'] * 5),  # Terrain + API confidence
                    'terrain_quality': terrain_quality,
                    'stands': [stand],
                    'best_time': best_time,
                    'best_wind': best_wind
                })
            return top_5
        
        # Score each hotspot using LIDAR terrain quality
        for hotspot in valid_hotspots:
            # NEW SCORING: Based on actual terrain quality, not just cluster size
            # 1. Get LIDAR scores for stands in this hotspot
            # 2. Weight by prediction confidence (API scores)
            # 3. Diversity bonus (multiple strategies = more versatile)
            
            # Extract LIDAR scores from source points
            lidar_scores = []
            aspects = []
            for stand in hotspot['stands']:
                source_lat, source_lon = stand['source_point']
                # Find matching LIDAR analysis
                matching = [p for p in self.lidar_analysis 
                           if abs(p['lat'] - source_lat) < 0.0001 and abs(p['lon'] - source_lon) < 0.0001]
                if matching:
                    lidar_scores.append(matching[0]['score'])
                    aspects.append(matching[0]['aspect'])
            
            # Average LIDAR terrain score (0-100)
            terrain_quality = np.mean(lidar_scores) if lidar_scores else 50
            
            # Calculate circular mean for aspect
            if aspects:
                # Convert to radians
                rads = np.radians(aspects)
                # Average the sin and cos components
                avg_sin = np.mean(np.sin(rads))
                avg_cos = np.mean(np.cos(rads))
                # Convert back to degrees
                avg_aspect = np.degrees(np.arctan2(avg_sin, avg_cos))
                if avg_aspect < 0:
                    avg_aspect += 360
            else:
                avg_aspect = None
            
            # Prediction confidence from API (0-10 scale)
            api_confidence = hotspot['avg_score']
            
            # Cluster density (more predictions = higher confidence)
            density_bonus = min(hotspot['num_predictions'] * 3, 15)  # Cap at 15
            
            # Strategy diversity (multiple approaches = more versatile location)
            diversity_bonus = min(len(hotspot['strategies']) * 2, 10)  # Cap at 10
            
            # TOTAL: Terrain (0-100) + API confidence (0-50) + density (0-15) + diversity (0-10)
            # Max possible: 175 points
            hotspot['total_score'] = terrain_quality + (api_confidence * 5) + density_bonus + diversity_bonus
            hotspot['terrain_quality'] = terrain_quality
            hotspot['lidar_scores'] = lidar_scores
            
            # Add Best Time and Wind
            hotspot['best_time'] = self.get_best_time(hotspot['strategies'])
            hotspot['best_wind'] = self.get_best_wind(avg_aspect)
        
        # Sort by score
        ranked = sorted(valid_hotspots, key=lambda h: h['total_score'], reverse=True)
        
        # Return top 10
        top_10 = ranked[:10]
        
        # Identify Buck Bedroom
        self.identify_buck_bedroom(top_hotspots=top_10)
        
        print(f"\n✅ Top 10 Hotspots (all inside property):")
        for i, hotspot in enumerate(top_10, 1):
            is_primary = (i == 1) # Assume #1 is primary
            
            if is_primary:
                print(f"\n   🏆 PRIMARY HOTSPOT")
                print(f"   #{i} - ({hotspot['center_lat']:.6f}, {hotspot['center_lon']:.6f})")
            else:
                print(f"\n   #{i} - ({hotspot['center_lat']:.6f}, {hotspot['center_lon']:.6f})")
                
            print(f"      Score: {hotspot['total_score']:.1f} | Predictions: {hotspot['num_predictions']} | Confidence: {hotspot['avg_score']:.1f}/10")
            print(f"      Strategy: {', '.join(hotspot['strategies'])}")
            print(f"      Best Time: {hotspot['best_time']}")
            
            # Wind analysis based on buck travel from bed
            if self.buck_bed:
                dist = self.calculate_distance(self.buck_bed['lat'], self.buck_bed['lon'], hotspot['center_lat'], hotspot['center_lon'])
                bearing = self.calculate_bearing(self.buck_bed['lat'], self.buck_bed['lon'], hotspot['center_lat'], hotspot['center_lon'])
                yards = dist * 1.09361
                
                # Determine cardinal direction buck travels FROM bed TO hotspot
                dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
                ix = round(bearing / 45) % 8
                buck_travel_dir = dirs[ix]
                
                # Buck approaches FROM the opposite direction
                approach_bearing = (bearing + 180) % 360
                approach_ix = round(approach_bearing / 45) % 8
                buck_approaches_from = dirs[approach_ix]
                
                def get_cardinal(deg):
                    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
                    ix = round(deg / 45) % 8
                    return dirs[ix]
                
                # Calculate GOOD winds (blow scent AWAY from buck's approach)
                # Good winds are roughly perpendicular to his approach, blowing away from it
                good_wind_1 = (bearing + 90) % 360  # Crosswind option 1
                good_wind_2 = (bearing - 90) % 360  # Crosswind option 2
                # Also good: winds blowing same direction buck travels (behind him)
                good_wind_3 = bearing  # Blows where he's going, not where he's coming from
                
                good_winds = [get_cardinal(good_wind_1), get_cardinal(good_wind_2)]
                
                # Calculate BAD winds (blow scent TOWARD buck's approach path)
                bad_wind = (bearing + 180) % 360  # Blows toward where buck comes from
                bad_wind_dir = get_cardinal(bad_wind)
                # Adjacent bad winds
                bad_wind_adj1 = get_cardinal((bad_wind + 45) % 360)
                bad_wind_adj2 = get_cardinal((bad_wind - 45) % 360)
                
                print(f"      ─────────────────────────────────────────")
                print(f"      🦌 BUCK COMMUTE: {yards:.0f} yds from bed")
                print(f"         He travels {buck_travel_dir} from bed → approaches from {buck_approaches_from}")
                print(f"      🌬️  WIND STRATEGY:")
                print(f"         ✅ HUNT ON: {good_winds[0]} or {good_winds[1]} wind")
                print(f"            (Your scent blows away from his approach)")
                print(f"         ❌ AVOID:   {bad_wind_dir} wind")
                print(f"            (Your scent blows toward his approach path)")
        
        return top_10
    
    def find_nearby_clusters(self, max_distance_meters: float = 100) -> list:
        """Find clusters that are outside property but within specified distance of boundary."""
        outside_clusters = [h for h in self.hotspots if not h['inside_property']]
        
        if not outside_clusters:
            return []
        
        nearby = []
        for cluster in outside_clusters:
            # Calculate distance from cluster center to property boundary
            cluster_point = Point(cluster['center_lon'], cluster['center_lat'])
            distance = self.property_polygon.exterior.distance(cluster_point)
            
            # Convert to meters (rough approximation: 1 degree ≈ 111km)
            distance_meters = distance * 111000
            
            if distance_meters <= max_distance_meters:
                cluster['distance_to_boundary'] = distance_meters
                nearby.append(cluster)
        
        # Sort by distance (closest first)
        nearby.sort(key=lambda c: c['distance_to_boundary'])
        
        return nearby
    
    def get_quadrant(self, lat: float, lon: float) -> str:
        """Determine which quadrant (NW, NE, SW, SE) a point falls into."""
        center_lat = np.mean([c[0] for c in self.corners.values()])
        center_lon = np.mean([c[1] for c in self.corners.values()])
        
        is_north = lat >= center_lat
        is_east = lon >= center_lon
        
        if is_north and is_east: return 'NE'
        if is_north and not is_east: return 'NW'
        if not is_north and is_east: return 'SE'
        return 'SW'

    def select_diverse_candidates(self, sites: List[Dict], total: int = 20, min_per_quad: int = 2) -> List[Dict]:
        """Select top sites but ensure geographic diversity across quadrants."""
        print(f"\n⚖️  Selecting {total} candidates with diversity check (min {min_per_quad} per quadrant)...")
        
        quadrants = {'NE': [], 'NW': [], 'SE': [], 'SW': []}
        for site in sites:
            q = self.get_quadrant(site['lat'], site['lon'])
            quadrants[q].append(site)
            
        selected = []
        # Force min_per_quad
        for q, q_sites in quadrants.items():
            # Sort by score
            q_sites.sort(key=lambda x: x['score'], reverse=True)
            # Take top N
            taking = q_sites[:min_per_quad]
            selected.extend(taking)
            print(f"   - {q}: Selected {len(taking)} forced candidates (Best: {taking[0]['score']:.1f})" if taking else f"   - {q}: No sites available!")
            
        # Fill rest with best remaining
        current_ids = {id(s) for s in selected}
        remaining = [s for s in sites if id(s) not in current_ids]
        remaining.sort(key=lambda x: x['score'], reverse=True)
        
        needed = total - len(selected)
        if needed > 0:
            filled = remaining[:needed]
            selected.extend(filled)
            print(f"   - Filled remaining {len(filled)} slots with highest scoring sites")
            
        return selected

    def print_balanced_summary(self):
        """Print Top 5 Global + Best of Other Quadrants."""
        print(f"\n" + "="*70)
        print("🏆 BALANCED HOTSPOT REPORT")
        print("="*70)
        
        # 1. Get Global Top 5
        # We need to re-rank all hotspots/stands first to be sure
        valid_hotspots = [h for h in self.hotspots if h['inside_property']]
        
        # If no hotspots, use stands
        if not valid_hotspots:
            items = [s for s in self.all_stands if s['inside_property']]
            # Add dummy total_score if missing
            for i in items:
                if 'total_score' not in i: i['total_score'] = i['score'] * 10 # Rough conversion
        else:
            items = valid_hotspots
            
        # Sort by total score
        items.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        top_10 = items[:10]
        
        print("\n🌟 TOP 10 PREDICTED SITES (GLOBAL)")
        print("-" * 40)
        for i, item in enumerate(top_10, 1):
            lat = item.get('center_lat', item.get('lat'))
            lon = item.get('center_lon', item.get('lon'))
            score = item.get('total_score', 0)
            quad = self.get_quadrant(lat, lon)
            type_str = "Cluster" if 'num_predictions' in item else "Stand"
            best_time = item.get('best_time', 'Unknown')
            best_wind = item.get('best_wind', 'Unknown')
            # Get aspect if available (it's not stored in item directly, need to re-calculate or store it)
            # For now, we won't print aspect here to keep it simple, but the wind is based on the corrected aspect.
            print(f"   #{i} [{quad}] Score: {score:.1f} - ({lat:.5f}, {lon:.5f}) - {type_str}")
            print(f"       Time: {best_time} | Wind: {best_wind}")

        # 2. Identify "Best Area" (Quadrant with most in Top 5)
        quad_counts = {'NE': 0, 'NW': 0, 'SE': 0, 'SW': 0}
        for item in top_10[:5]:
            lat = item.get('center_lat', item.get('lat'))
            lon = item.get('center_lon', item.get('lon'))
            q = self.get_quadrant(lat, lon)
            quad_counts[q] += 1
            
        best_quad = max(quad_counts, key=quad_counts.get)
        print(f"\n   👉 Dominant Sector: {best_quad} ({quad_counts[best_quad]}/5 top spots)")
        
        # 3. Find best in other quadrants
        print(f"\n🌍 BEST LOCATION IN OTHER SECTORS")
        print("-" * 40)
        
        other_quads = [q for q in ['NE', 'NW', 'SE', 'SW'] if q != best_quad]
        
        for q in other_quads:
            # Find best item in this quadrant from ALL items (not just top 5)
            q_items = []
            for item in items:
                lat = item.get('center_lat', item.get('lat'))
                lon = item.get('center_lon', item.get('lon'))
                if self.get_quadrant(lat, lon) == q:
                    q_items.append(item)
            
            if q_items:
                best = q_items[0] # Already sorted
                lat = best.get('center_lat', best.get('lat'))
                lon = best.get('center_lon', best.get('lon'))
                score = best.get('total_score', 0)
                print(f"   📍 {q} Sector Best: Score {score:.1f} - ({lat:.5f}, {lon:.5f})")
            else:
                print(f"   ⚠️  {q} Sector: No huntable predictions found (Terrain score too low)")

    def generate_map(self, output_file: str = "hotspot_map.html"):
        """Generate interactive map showing analysis results."""
        print(f"\n🗺️  Generating map...")
        
        # Center map on property
        center_lat = np.mean([c[0] for c in self.corners.values()])
        center_lon = np.mean([c[1] for c in self.corners.values()])
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
        
        # Draw property boundary
        boundary_coords = [[c[0], c[1]] for c in [
            self.corners['NW'], self.corners['NE'], 
            self.corners['SE'], self.corners['SW']
        ]]
        folium.Polygon(
            locations=boundary_coords,
            color='black',
            weight=3,
            fill=False,
            popup='Property Boundary'
        ).add_to(m)
        
        # Add grid points
        for lat, lon in self.grid_points:
            folium.CircleMarker(
                location=[lat, lon],
                radius=3,
                color='blue',
                fill=True,
                popup=f'Prediction Point: ({lat:.5f}, {lon:.5f})'
            ).add_to(m)
        
        # Add all predicted stands (small dots)
        for stand in self.all_stands:
            color = 'green' if stand['inside_property'] else 'red'
            folium.CircleMarker(
                location=[stand['lat'], stand['lon']],
                radius=2,
                color=color,
                fill=True,
                opacity=0.3
            ).add_to(m)
        
        # Add top hotspots (large markers)
        top_hotspots = self.rank_hotspots()
        for i, hotspot in enumerate(top_hotspots, 1):
            folium.Marker(
                location=[hotspot['center_lat'], hotspot['center_lon']],
                popup=f"""
                    <b>Hotspot #{i}</b><br>
                    Predictions: {hotspot['num_predictions']}<br>
                    Avg Score: {hotspot['avg_score']:.1f}/10<br>
                    Strategies: {', '.join(hotspot['strategies'])}<br>
                    Best Time: {hotspot.get('best_time', 'Unknown')}<br>
                    Best Wind: {hotspot.get('best_wind', 'Unknown')}<br>
                    Score: {hotspot['total_score']:.1f}
                """,
                icon=folium.Icon(color='red', icon='star')
            ).add_to(m)
        
        # Save map
        output_path = Path(output_file)
        m.save(str(output_path))
        print(f"✅ Map saved to: {output_path.absolute()}")
        
        return str(output_path.absolute())
    
    def generate_report(self, output_file: str = "hotspot_report.json"):
        """Generate detailed JSON report of analysis."""
        top_hotspots = self.rank_hotspots()

        baseline = self.get_baseline_stand(epsilon_meters=60, min_samples=3)
        
        # Find nearby clusters (outside but close to boundary)
        nearby_clusters = self.find_nearby_clusters(max_distance_meters=500)
        
        report = {
            'analysis_date': datetime.now().isoformat(),
            'property_corners': self.corners,
            'grid_points_analyzed': len(self.grid_points),
            'successful_predictions': len(self.predictions),
            'total_stands_predicted': len(self.all_stands),
            'stands_inside_property': sum(1 for s in self.all_stands if s['inside_property']),
            'total_hotspots_found': len(self.hotspots),
            'hotspots_inside_property': len([h for h in self.hotspots if h['inside_property']]),
            'top_hotspots': [
                {
                    'rank': i,
                    'latitude': h['center_lat'],
                    'longitude': h['center_lon'],
                    'num_predictions': h['num_predictions'],
                    'api_confidence': h['avg_score'],
                    'terrain_quality': h.get('terrain_quality', 0),
                    'total_score': h['total_score'],
                    'strategies': h['strategies'],
                    'best_time': h.get('best_time', 'Unknown'),
                    'best_wind': h.get('best_wind', 'Unknown'),
                    'lidar_scores': h.get('lidar_scores', [])
                }
                for i, h in enumerate(top_hotspots, 1)
            ],
            'baseline_stand': baseline,
            'nearby_clusters_outside_boundary': [
                {
                    'latitude': c['center_lat'],
                    'longitude': c['center_lon'],
                    'distance_to_boundary_meters': round(c['distance_to_boundary'], 1),
                    'num_predictions': c['num_predictions'],
                    'average_score': c['avg_score'],
                    'strategies': c['strategies']
                }
                for c in nearby_clusters
            ]
        }
        
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print nearby clusters if any found
        if nearby_clusters:
            print(f"\n📍 Found {len(nearby_clusters)} cluster(s) outside but near property boundary (within 100m):")
            for i, cluster in enumerate(nearby_clusters, 1):
                print(f"\n   Nearby Cluster #{i}")
                print(f"   Location: ({cluster['center_lat']:.6f}, {cluster['center_lon']:.6f})")
                print(f"   Distance from boundary: {cluster['distance_to_boundary']:.1f}m")
                print(f"   Predictions: {cluster['num_predictions']}")
                print(f"   Avg Score: {cluster['avg_score']:.1f}/10")
                print(f"   Strategies: {', '.join(cluster['strategies'])}")
        
        print(f"✅ Report saved to: {output_path.absolute()}")

        if baseline:
            print(f"\n🎯 BASELINE CONSENSUS STAND")
            print(f"   Location: ({baseline['lat']:.6f}, {baseline['lon']:.6f})")
            print(f"   Support: {baseline.get('supporting_predictions', 0)} predictions")
            print(f"   Sources: {', '.join(baseline.get('sources', []))}")
            print(f"   Why: {baseline.get('reason', '')}")

        return str(output_path.absolute())


def main():
    """Run the complete two-phase analysis."""
    print("\n" + "=" * 70)
    print("🦌 PROPERTY HOTSPOT ANALYZER - Two-Phase Analysis")
    print("   800 Acres - LIDAR-First Approach")
    print("=" * 70)
    
    # Initialize analyzer
    analyzer = PropertyHotspotAnalyzer(PROPERTY_CORNERS)
    
    # PHASE 1: Grid Generation & LIDAR Terrain Analysis
    print("\n📍 PHASE 1: Dense Grid Generation & LIDAR Terrain Analysis")
    print("   Goal: Analyze 3000 sites using LIDAR (NO API calls yet)")
    print("-" * 70)
    
    # Generate 100,000 grid points across property (100 points/acre for 1000 acres)
    analyzer.generate_grid(num_points=100000)
    
    # Score all 1500 points with LIDAR
    if LIDAR_AVAILABLE:
        scored_points = analyzer.score_grid_with_lidar()
        
        if not scored_points or len(scored_points) == 0:
            print("\n❌ LIDAR scoring failed - cannot proceed without terrain data")
            print("   Please check that LIDAR DEM files exist in: data/lidar/raw/vermont/")
            return
        
        print(f"\n✅ LIDAR analysis complete: {len(scored_points)} points scored")
        
        # Take top 50 scored points
        top_50 = scored_points[:50]
        print(f"   Top 50 sites selected for land cover analysis")
        print(f"   Score range: {top_50[0]['score']:.1f} - {top_50[-1]['score']:.1f}")
        
    else:
        print("\n❌ LIDAR not available - cannot proceed")
        print("   This script requires LIDAR for terrain analysis")
        return
    
    # PHASE 1.5: GEE Land Cover Filtering on Top 50
    print("\n🌲 PHASE 1.5: Land Cover Analysis on Top 50 Sites")
    print("   Goal: Filter out roads, fields, and non-forest areas")
    print("-" * 70)
    
    forest_sites = []
    print(f"\n🔄 Checking land cover for top 50 sites...")
    
    for i, site in enumerate(top_50, 1):
        land_cover = analyzer.get_land_cover(site['lat'], site['lon'])
        
        if land_cover and land_cover.get('is_forest', False):
            # Thermal Cover Bonus (Evergreen/Mixed Forest)
            class_id = land_cover.get('class_id', -1)
            if class_id in [42, 43]: # Evergreen or Mixed
                site['score'] += 10
                print(f"   [{i}/50] ✅ Forest - {land_cover['class_name']} - Score: {site['score']:.1f} (Includes +10 Thermal Bonus)")
            else:
                print(f"   [{i}/50] ✅ Forest - {land_cover['class_name']} - Score: {site['score']:.1f}")
                
            forest_sites.append(site)
        else:
            cover_type = land_cover['class_name'] if land_cover else 'Unknown'
            print(f"   [{i}/50] ❌ Non-forest - {cover_type}")
            
    # Re-sort forest sites by new score (including thermal bonus)
    forest_sites.sort(key=lambda x: x['score'], reverse=True)
    
    if len(forest_sites) == 0:
        print("\n❌ No forest sites found in top 50 LIDAR points")
        print("   Try expanding search or adjusting terrain scoring")
        return
    
    print(f"\n✅ Land cover filtering complete!")
    print(f"   {len(forest_sites)} forest sites identified from top 50")
    print(f"   Taking top 20 for API predictions (with diversity check)")
    
    # Use top 20 forest sites for API predictions (with diversity check)
    analyzer.candidate_points = analyzer.select_diverse_candidates(forest_sites, total=20, min_per_quad=2)
    analyzer.grid_points = [(p['lat'], p['lon']) for p in analyzer.candidate_points]
    
    # PHASE 2: API Predictions for Top Candidates
    print("\n📍 PHASE 2: API Predictions for Top Candidates")
    print("-" * 70)
    
    analyzer.run_batch_predictions(delay=2.0)
    
    # PHASE 3: Clustering & Hotspot Identification
    print("\n📍 PHASE 3: Clustering & Hotspot Identification")
    print("-" * 70)
    
    analyzer.extract_all_stands()
    analyzer.find_clusters(epsilon_meters=75, min_samples=2)  # More lenient clustering
    
    # Generate outputs
    print("\n📍 Generating Outputs")
    print("-" * 70)
    
    analyzer.generate_map()
    analyzer.generate_report()
    analyzer.print_balanced_summary()
    
    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\n📊 Results:")
    print(f"   - Top 5 hotspots identified (all inside property)")
    print(f"   - Map: hotspot_map.html")
    print(f"   - Report: hotspot_report.json")
    print("\n🎯 Use the map to visualize hotspots and property boundary")
    print("📍 All top 5 locations are verified to be within your property")
    

if __name__ == "__main__":
    main()
