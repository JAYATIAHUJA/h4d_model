"""
Extract infrastructure features for Delhi wards using OSMnx.
Much faster than parsing raw OSM files!
"""

import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from shapely.geometry import Point, LineString
import warnings
warnings.filterwarnings('ignore')

# Configuration
ox.settings.use_cache = True
ox.settings.log_console = True


def load_ward_boundaries():
    """Load Delhi ward boundaries."""
    wards_file = Path(__file__).parent / "raw" / "wards" / "delhi_ward.json"
    return gpd.read_file(wards_file)


def extract_yamuna_river():
    """Extract Yamuna river geometry."""
    print("\n1. Extracting Yamuna River...")
    
    try:
        # Query Yamuna river in Delhi area (updated API)
        yamuna = ox.features_from_place(
            'Delhi, India', 
            tags={'waterway': 'river', 'name': 'Yamuna'}
        )
        
        if len(yamuna) > 0:
            print(f"   ✓ Found {len(yamuna)} Yamuna segments")
            return yamuna
        else:
            print("   ! Yamuna not found, trying alternative query...")
            # Fallback: get all rivers
            rivers = ox.features_from_place('Delhi, India', tags={'waterway': 'river'})
            return rivers
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None


def extract_buildings():
    """Extract all buildings in Delhi."""
    print("\n2. Extracting Buildings...")
    
    try:
        buildings = ox.features_from_place('Delhi, India', tags={'building': True})
        print(f"   ✓ Found {len(buildings)} buildings")
        return buildings
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None


def extract_road_network():
    """Extract road network."""
    print("\n3. Extracting Road Network...")
    
    try:
        # Download road network graph
        G = ox.graph_from_place('Delhi, India', network_type='all')
        
        # Convert to GeoDataFrame
        edges = ox.graph_to_gdfs(G, nodes=False)
        print(f"   ✓ Found {len(edges)} road segments")
        
        return edges
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None


def calculate_ward_features(wards, yamuna, buildings, roads):
    """Calculate infrastructure features for each ward."""
    print("\n4. Calculating Ward Features...")
    
    features = []
    
    for idx, ward in wards.iterrows():
        ward_id = ward.get('unique', ward.get('id', idx))
        ward_geom = ward.geometry
        ward_area_km2 = ward_geom.area / 1e6  # Convert to km²
        
        ward_features = {
            'ward_id': ward_id,
            'ward_area_km2': ward_area_km2
        }
        
        # Distance to Yamuna
        if yamuna is not None and len(yamuna) > 0:
            try:
                min_dist = yamuna.geometry.distance(ward_geom.centroid).min()
                ward_features['yamuna_distance_m'] = min_dist
            except:
                ward_features['yamuna_distance_m'] = np.nan
        else:
            ward_features['yamuna_distance_m'] = np.nan
        
        # Building density
        if buildings is not None:
            try:
                # Find buildings within ward
                buildings_in_ward = buildings[buildings.intersects(ward_geom)]
                
                # Building count density
                ward_features['building_count'] = len(buildings_in_ward)
                ward_features['building_density_per_km2'] = len(buildings_in_ward) / ward_area_km2
                
                # Building area density (if available)
                if len(buildings_in_ward) > 0:
                    total_building_area = buildings_in_ward.geometry.area.sum() / 1e6  # km²
                    ward_features['building_area_km2'] = total_building_area
                    ward_features['building_coverage_pct'] = (total_building_area / ward_area_km2) * 100
                else:
                    ward_features['building_area_km2'] = 0
                    ward_features['building_coverage_pct'] = 0
            except Exception as e:
                ward_features['building_count'] = 0
                ward_features['building_density_per_km2'] = 0
                ward_features['building_area_km2'] = 0
                ward_features['building_coverage_pct'] = 0
        
        # Road network density
        if roads is not None:
            try:
                # Find roads within ward
                roads_in_ward = roads[roads.intersects(ward_geom)]
                
                # Total road length
                total_road_length_m = roads_in_ward.geometry.length.sum()
                total_road_length_km = total_road_length_m / 1000
                
                ward_features['road_length_km'] = total_road_length_km
                ward_features['road_density_km_per_km2'] = total_road_length_km / ward_area_km2
                
                # Road count
                ward_features['road_segment_count'] = len(roads_in_ward)
                
                # Road type breakdown
                if 'highway' in roads_in_ward.columns:
                    primary_roads = roads_in_ward[roads_in_ward['highway'].isin(['motorway', 'trunk', 'primary'])]
                    ward_features['primary_road_length_km'] = primary_roads.geometry.length.sum() / 1000
                else:
                    ward_features['primary_road_length_km'] = 0
                
            except Exception as e:
                ward_features['road_length_km'] = 0
                ward_features['road_density_km_per_km2'] = 0
                ward_features['road_segment_count'] = 0
                ward_features['primary_road_length_km'] = 0
        
        features.append(ward_features)
        
        if (idx + 1) % 50 == 0:
            print(f"   Processed {idx + 1}/{len(wards)} wards...")
    
    print(f"   ✓ Calculated features for {len(features)} wards")
    return pd.DataFrame(features)


def main():
    """Main extraction pipeline."""
    print("=" * 70)
    print("DELHI INFRASTRUCTURE FEATURE EXTRACTION")
    print("=" * 70)
    
    # Load ward boundaries
    print("\n0. Loading ward boundaries...")
    wards = load_ward_boundaries()
    print(f"   ✓ Loaded {len(wards)} wards")
    
    # Extract infrastructure
    yamuna = extract_yamuna_river()
    buildings = extract_buildings()
    roads = extract_road_network()
    
    # Calculate ward-level features
    ward_features = calculate_ward_features(wards, yamuna, buildings, roads)
    
    # Save results
    output_file = Path(__file__).parent / "processed" / "ward_infrastructure_features.csv"
    ward_features.to_csv(output_file, index=False)
    
    print("\n" + "=" * 70)
    print(f"✓ COMPLETE! Saved to: {output_file}")
    print("=" * 70)
    
    # Show summary
    print("\nFeature Summary:")
    print(ward_features.describe())
    
    return ward_features


if __name__ == "__main__":
    features = main()
