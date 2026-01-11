"""
Integrate Civic Complaint Data into Ward Features
==================================================

This script enhances ward static features with civic infrastructure metrics:
1. Sewerage complaint trends (75% increase 2019-2022)
2. Zone-wise waste load (proxy for drain blockage)
3. Pothole density (infrastructure degradation)

These are KEY indicators of flood failure during rainfall events.

Usage:
    python backend/model/integrate_civic_data.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

def integrate_civic_data():
    """Integrate civic complaint data into ward static features."""
    
    print("="*70)
    print("INTEGRATING CIVIC INFRASTRUCTURE DATA INTO WARD FEATURES")
    print("="*70)
    
    # Load existing ward features
    ward_path = Path("backend/data/processed/ward_static_features_enhanced.csv")
    if not ward_path.exists():
        ward_path = Path("backend/data/processed/ward_static_features.csv")
    
    ward_df = pd.read_csv(ward_path)
    print(f"\n[1/5] Loaded {len(ward_df)} wards")
    
    # Load sewerage complaints trend
    sewerage_path = Path("backend/data/processed/sewerage_complaints_yearly.csv")
    if sewerage_path.exists():
        sewerage_df = pd.read_csv(sewerage_path)
        # Calculate growth rate 2019 -> 2022
        complaints_2019 = sewerage_df[sewerage_df['year'] == 2019]['sewerage_complaints'].values[0]
        complaints_2022 = sewerage_df[sewerage_df['year'] == 2022]['sewerage_complaints'].values[0]
        growth_rate = (complaints_2022 - complaints_2019) / complaints_2019
        print(f"\n[2/5] Sewerage complaints growth: {growth_rate:.1%} (2019→2022)")
    else:
        growth_rate = 0.75  # Default 75%
        print(f"\n[2/5] Using default sewerage growth rate: {growth_rate:.1%}")
    
    # Load zone waste data
    zone_waste_path = Path("backend/data/processed/zone_waste_load.csv")
    if zone_waste_path.exists():
        zone_waste = pd.read_csv(zone_waste_path)
        zone_waste['waste_per_ward'] = zone_waste['waste_tpd'] / zone_waste['wards']
        print(f"\n[3/5] Loaded waste data for {len(zone_waste)} zones")
        
        # Map zone names to ward (simplified mapping based on typical Delhi zones)
        zone_mapping = {
            'Central': range(0, 25),
            'City_SP': range(25, 37),
            'Civil_Line': range(37, 52),
            'Karol_Bagh': range(52, 65),
            'Keshavpuram': range(65, 80),
            'Najafgarh': range(80, 102),
            'Narela': range(102, 118),
            'Rohini': range(118, 141),
            'Shahdara_North': range(141, 176),
            'Shahdara_South': range(176, 202),
            'South': range(202, 225),
            'West': range(225, 250)
        }
        
        # Assign zone to each ward
        ward_df['zone'] = 'Unknown'
        ward_df['zone_waste_tpd'] = 0
        ward_df['zone_waste_per_ward'] = 0
        
        for zone_name, ward_range in zone_mapping.items():
            zone_data = zone_waste[zone_waste['zone'] == zone_name]
            if len(zone_data) > 0:
                waste_tpd = zone_data.iloc[0]['waste_tpd']
                waste_per_ward = zone_data.iloc[0]['waste_per_ward']
                mask = ward_df.index.isin(ward_range)
                ward_df.loc[mask, 'zone'] = zone_name
                ward_df.loc[mask, 'zone_waste_tpd'] = waste_tpd
                ward_df.loc[mask, 'zone_waste_per_ward'] = waste_per_ward
    else:
        print(f"\n[3/5] Zone waste data not found")
        ward_df['zone_waste_per_ward'] = 0
    
    # Load pothole reports
    pothole_path = Path("backend/data/processed/pothole_reports.csv")
    if pothole_path.exists():
        pothole_df = pd.read_csv(pothole_path)
        
        # Aggregate by ward
        pothole_stats = pothole_df.groupby('ward_id').agg({
            'report_id': 'count',
            'severity': lambda x: (x == 'large').sum() / len(x) if len(x) > 0 else 0
        }).rename(columns={'report_id': 'pothole_count', 'severity': 'pothole_severity_ratio'})
        
        ward_df['pothole_count'] = 0
        ward_df['pothole_severity_ratio'] = 0
        
        for ward_id in pothole_stats.index:
            mask = ward_df['ward_id'] == ward_id
            if mask.any():
                ward_df.loc[mask, 'pothole_count'] = pothole_stats.loc[ward_id, 'pothole_count']
                ward_df.loc[mask, 'pothole_severity_ratio'] = pothole_stats.loc[ward_id, 'pothole_severity_ratio']
        
        print(f"\n[4/5] Integrated {len(pothole_df)} pothole reports")
    else:
        print(f"\n[4/5] Pothole data not found")
        ward_df['pothole_count'] = 0
        ward_df['pothole_severity_ratio'] = 0
    
    # Generate sewerage stress index for each ward
    # Based on: historical floods + urbanization + sewerage growth trend
    ward_df['sewerage_stress_index'] = 0.0
    
    # High sewerage stress = high flood freq + high urbanization + high waste
    if 'hist_flood_freq' in ward_df.columns:
        # Normalize factors
        flood_norm = ward_df.get('hist_flood_freq', 0) / 10  # 0-1 scale
    else:
        flood_norm = 0.3  # Default moderate risk
    
    urban_norm = ward_df.get('urbanization_index', 0.5)  # Already 0-1
    
    # Waste per ward normalized
    if ward_df['zone_waste_per_ward'].max() > 0:
        waste_norm = ward_df['zone_waste_per_ward'] / ward_df['zone_waste_per_ward'].max()
    else:
        waste_norm = 0.5
    
    # Pothole density (infrastructure degradation)
    if ward_df['pothole_count'].max() > 0:
        pothole_norm = ward_df['pothole_count'] / ward_df['pothole_count'].max()
    else:
        pothole_norm = 0
    
    # Composite sewerage stress index
    # This captures systemic drainage failure risk
    ward_df['sewerage_stress_index'] = np.clip(
        0.35 * flood_norm + 
        0.25 * urban_norm + 
        0.25 * waste_norm + 
        0.15 * pothole_norm,
        0, 1
    )
    
    # Apply sewerage growth trend (75% increase means higher stress)
    ward_df['sewerage_stress_index'] *= (1 + growth_rate * 0.3)  # Amplify by 30% of growth
    ward_df['sewerage_stress_index'] = np.clip(ward_df['sewerage_stress_index'], 0, 1)
    
    print(f"\n[5/5] Computed sewerage stress index")
    print(f"  Mean: {ward_df['sewerage_stress_index'].mean():.3f}")
    print(f"  Max:  {ward_df['sewerage_stress_index'].max():.3f}")
    print(f"  High risk wards (>0.7): {(ward_df['sewerage_stress_index'] > 0.7).sum()}")
    
    # Update flood vulnerability index to include sewerage stress
    if 'flood_vulnerability_index' in ward_df.columns:
        # Blend existing vulnerability with sewerage stress
        ward_df['flood_vulnerability_index'] = np.clip(
            0.7 * ward_df['flood_vulnerability_index'] + 
            0.3 * ward_df['sewerage_stress_index'],
            0, 1
        )
        print(f"\n  Updated flood vulnerability index with sewerage stress")
    
    # Save enhanced features
    output_path = Path("backend/data/processed/ward_static_features_civic_enhanced.csv")
    ward_df.to_csv(output_path, index=False)
    print(f"\n[OK] Saved enhanced features to: {output_path}")
    
    # Generate summary report
    print(f"\n{'='*70}")
    print("CIVIC DATA INTEGRATION SUMMARY")
    print(f"{'='*70}")
    print(f"Total wards: {len(ward_df)}")
    print(f"\nNew features added:")
    print(f"  - zone_waste_per_ward (drainage blockage proxy)")
    print(f"  - pothole_count (infrastructure degradation)")
    print(f"  - pothole_severity_ratio (severe infrastructure failure)")
    print(f"  - sewerage_stress_index (composite failure indicator)")
    print(f"\nHigh-risk wards (sewerage stress > 0.7):")
    high_risk = ward_df[ward_df['sewerage_stress_index'] > 0.7].sort_values('sewerage_stress_index', ascending=False).head(10)
    for idx, row in high_risk.iterrows():
        print(f"  Ward {row['ward_id']}: {row['sewerage_stress_index']:.3f}")
    
    print(f"\n{'='*70}")
    return ward_df


if __name__ == "__main__":
    integrate_civic_data()
