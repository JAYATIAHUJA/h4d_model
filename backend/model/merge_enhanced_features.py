"""
Merge infrastructure features with existing ward data and retrain improved model.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Load datasets
data_dir = Path(__file__).parent.parent / "data" / "processed"

# Load existing features
static_features = pd.read_csv(data_dir / "ward_static_features.csv")
print(f"Loaded static features: {static_features.shape}")

# Load new infrastructure features
infra_features = pd.read_csv(data_dir / "ward_infrastructure_features.csv")
print(f"Loaded infrastructure features: {infra_features.shape}")

# Merge on ward_id
merged = static_features.merge(infra_features, on='ward_id', how='left')
print(f"Merged shape: {merged.shape}")

# Fill missing values with median
for col in infra_features.columns:
    if col != 'ward_id' and col in merged.columns:
        merged[col] = merged[col].fillna(merged[col].median())

# Add derived features for flood risk
merged['urbanization_index'] = (
    merged['building_density_per_km2'] / merged['building_density_per_km2'].max() * 0.5 +
    merged['road_density_km_per_km2'] / merged['road_density_km_per_km2'].max() * 0.3 +
    merged['building_coverage_pct'] / 100 * 0.2
)

# Flood vulnerability index (closer to Yamuna + high building density = higher risk)
merged['flood_vulnerability_index'] = (
    (1 / (merged['yamuna_distance_m'] / 1000 + 1)) * 0.4 +  # Proximity to Yamuna
    (merged['low_lying_pct'] / 100) * 0.3 +  # Low-lying areas
    (merged['building_density_per_km2'] / merged['building_density_per_km2'].max()) * 0.2 +  # Urbanization
    (1 - merged['drain_density'] / merged['drain_density'].max()) * 0.1  # Poor drainage
)

# Normalize flood vulnerability index to 0-1
merged['flood_vulnerability_index'] = (
    (merged['flood_vulnerability_index'] - merged['flood_vulnerability_index'].min()) /
    (merged['flood_vulnerability_index'].max() - merged['flood_vulnerability_index'].min())
)

# Save enhanced features
output_file = data_dir / "ward_static_features_enhanced.csv"
merged.to_csv(output_file, index=False)

print(f"\n✓ Saved enhanced features to: {output_file}")
print(f"\nNew features added:")
print(f"  - yamuna_distance_m: Distance to Yamuna River")
print(f"  - building_density_per_km2: Buildings per square km")
print(f"  - building_coverage_pct: % of ward covered by buildings")
print(f"  - road_density_km_per_km2: Road km per square km")
print(f"  - urbanization_index: Combined urbanization metric (0-1)")
print(f"  - flood_vulnerability_index: Flood risk indicator (0-1)")

print(f"\nFeature statistics:")
print(merged[['yamuna_distance_m', 'building_density_per_km2', 'road_density_km_per_km2', 
               'urbanization_index', 'flood_vulnerability_index']].describe())

print(f"\nTop 10 most flood-vulnerable wards:")
top_vulnerable = merged.nlargest(10, 'flood_vulnerability_index')[
    ['ward_id', 'ward_name', 'flood_vulnerability_index', 'yamuna_distance_m', 'low_lying_pct']
]
print(top_vulnerable.to_string(index=False))
