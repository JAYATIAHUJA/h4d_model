"""
Extract Delhi-specific features from OpenStreetMap data.
Filters large india.osm.pbf file to Delhi bounding box only.
"""

import osmium
import json
from pathlib import Path
from collections import defaultdict

# Delhi bounding box coordinates
DELHI_BBOX = {
    'min_lat': 28.404,
    'max_lat': 28.883,
    'min_lon': 76.838,
    'max_lon': 77.348
}


class DelhiExtractor(osmium.SimpleHandler):
    """Extract roads, drains, water bodies from Delhi area."""
    
    def __init__(self):
        super().__init__()
        self.drains = []
        self.water_bodies = []
        self.roads = []
        self.buildings = []
        
    def is_in_delhi(self, lat, lon):
        """Check if coordinates are within Delhi bounding box."""
        return (DELHI_BBOX['min_lat'] <= lat <= DELHI_BBOX['max_lat'] and
                DELHI_BBOX['min_lon'] <= lon <= DELHI_BBOX['max_lon'])
    
    def way(self, w):
        """Process OSM ways (roads, drains, etc)."""
        if len(w.nodes) < 2:
            return
        
        # Check if first node is in Delhi (rough filter)
        node = w.nodes[0]
        if not self.is_in_delhi(node.lat, node.lon):
            return
        
        tags = {tag.k: tag.v for tag in w.tags}
        
        # Extract drains and waterways
        if 'waterway' in tags:
            waterway_type = tags['waterway']
            if waterway_type in ['drain', 'ditch', 'canal', 'river', 'stream']:
                self.drains.append({
                    'id': w.id,
                    'type': waterway_type,
                    'name': tags.get('name', f'Unnamed {waterway_type}'),
                    'coordinates': [[node.lon, node.lat] for node in w.nodes]
                })
        
        # Extract water bodies
        if 'natural' in tags and tags['natural'] == 'water':
            self.water_bodies.append({
                'id': w.id,
                'name': tags.get('name', 'Unnamed water body'),
                'water_type': tags.get('water', 'unknown'),
                'coordinates': [[node.lon, node.lat] for node in w.nodes]
            })
        
        # Extract major roads
        if 'highway' in tags:
            road_type = tags['highway']
            if road_type in ['motorway', 'trunk', 'primary', 'secondary', 'tertiary']:
                self.roads.append({
                    'id': w.id,
                    'type': road_type,
                    'name': tags.get('name', f'Unnamed {road_type}'),
                    'coordinates': [[node.lon, node.lat] for node in w.nodes]
                })
    
    def area(self, a):
        """Process OSM areas (buildings, land use, etc)."""
        try:
            # Get first outer ring
            outer_rings = list(a.outer_rings())
            if len(outer_rings) == 0:
                return
            
            ring = outer_rings[0]
            if len(ring) < 3:
                return
            
            node = ring[0]
            if not self.is_in_delhi(node.lat, node.lon):
                return
            
            tags = {tag.k: tag.v for tag in a.tags}
            
            # Extract buildings (for flood impact assessment)
            if 'building' in tags:
                self.buildings.append({
                    'id': a.id,
                    'type': tags.get('building', 'yes'),
                    'name': tags.get('name', 'Unnamed building'),
                    'coordinates': [[node.lon, node.lat] for node in ring]
                })
        except Exception as e:
            # Skip problematic areas
            pass


def extract_delhi_data(input_file: str, output_dir: str = None):
    """
    Extract Delhi-specific features from OSM file.
    
    Args:
        input_file: Path to india.osm.pbf file
        output_dir: Output directory for extracted data (default: backend/data/processed/)
    """
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_file}")
        return
    
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "processed"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Extracting Delhi features from {input_file}...")
    print(f"Bounding box: {DELHI_BBOX}")
    
    # Extract features
    handler = DelhiExtractor()
    handler.apply_file(str(input_path))
    
    # Save results
    print(f"\nExtracted features:")
    print(f"  Drains/Waterways: {len(handler.drains)}")
    print(f"  Water bodies: {len(handler.water_bodies)}")
    print(f"  Major roads: {len(handler.roads)}")
    print(f"  Buildings: {len(handler.buildings)}")
    
    # Save as GeoJSON
    results = {
        'drains': {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'properties': {k: v for k, v in drain.items() if k != 'coordinates'},
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': drain['coordinates']
                    }
                }
                for drain in handler.drains
            ]
        },
        'water_bodies': {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'properties': {k: v for k, v in wb.items() if k != 'coordinates'},
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [wb['coordinates']]
                    }
                }
                for wb in handler.water_bodies
            ]
        },
        'roads': {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'properties': {k: v for k, v in road.items() if k != 'coordinates'},
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': road['coordinates']
                    }
                }
                for road in handler.roads
            ]
        }
    }
    
    # Save each category
    for category, geojson in results.items():
        output_file = output_dir / f"delhi_{category}.geojson"
        with open(output_file, 'w') as f:
            json.dump(geojson, f, indent=2)
        print(f"\nSaved: {output_file}")
    
    print("\n✓ Extraction complete!")


if __name__ == "__main__":
    # Extract from the large India file
    input_file = Path(__file__).parent / "raw" / "india-260110.osm.pbf"
    
    if not input_file.exists():
        print(f"OSM file not found: {input_file}")
        print("\nDownload it with:")
        print("  curl https://download.geofabrik.de/asia/india-latest.osm.pbf -o backend/data/raw/india-260110.osm.pbf")
    else:
        extract_delhi_data(str(input_file))
