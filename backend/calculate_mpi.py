"""
Ward-wise MPI (Multi-Parameter Index) Calculator
=================================================

Combines multiple data sources to create comprehensive flood risk scores:
1. ML Model predictions (based on rainfall + ward features)
2. Real-time weather data (OpenWeather API)
3. Historical flood frequency (INDOFLOODS)
4. Civic complaints/infrastructure issues
5. Drainage capacity
6. Elevation vulnerability

MPI Score (0-100): Weighted combination of all factors
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "model"))

from flood_model import FloodFailureModel, FeatureEngineer
from data_integration import DataPipeline
sys.path.insert(0, str(Path(__file__).parent))
from weather_api import fetch_current_weather_delhi, fetch_forecast_delhi, calculate_rainfall_features


class MPICalculator:
    """
    Calculate Multi-Parameter Index (MPI) and Monsoon Preparedness Index.
    
    MPI: Real-time flood risk score (0-100)
    Monsoon Preparedness Index: Infrastructure readiness assessment (0-100)
    """
    
    def __init__(self):
        """Initialize MPI calculator with model and data."""
        self.model = None
        self.feature_engineer = None
        self.ward_static = None
        self.ward_historical = None
        self.civic_complaints = None
        self.zone_preparedness = None
        
    def load_model(self, model_path: str = None):
        """Load trained flood prediction model."""
        print("Loading flood prediction model...")
        try:
            if model_path is None:
                # Use absolute path
                model_path = Path(__file__).parent / "model" / "artifacts" / "flood_model_v1.pkl"
            
            if not Path(model_path).exists():
                print(f"[ERROR] Model file not found: {model_path}")
                print("[INFO] Please train the model first by running:")
                print("       cd backend/model")
                print("       python train_model_1.py")
                return False
            
            self.model = FloodFailureModel.load(str(model_path))
            self.feature_engineer = self.model.feature_engineer
            print("[OK] Model loaded")
            return True
        except Exception as e:
            print(f"[ERROR] Error loading model: {e}")
            return False
    
    def load_ward_data(self):
        """Load ward static and historical features."""
        print("Loading ward data...")
        try:
            pipeline = DataPipeline()
            pipeline.initialize()  # Initialize first to load everything
            
            # Override with enhanced features if available
            enhanced_path = Path(__file__).parent / "data" / "processed" / "ward_static_features_enhanced.csv"
            if enhanced_path.exists():
                print("  Using ENHANCED features (with Yamuna, buildings, roads)")
                pipeline.ward_processor.load_features(str(enhanced_path))
            
            self.ward_static, self.ward_historical = pipeline.get_ward_data()
            
            print(f"[OK] Loaded {len(self.ward_static)} wards with {len(self.ward_static.columns)} features")
            return True
        except Exception as e:
            print(f"[ERROR] Error loading ward data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_civic_complaints(self):
        """
        Load civic complaints data including:
        - Sewerage complaints (yearly trend showing 75% increase)
        - Zone-wise waste load (proxy for drain blockage)
        - Pothole reports (infrastructure degradation)
        """
        print("Loading civic complaints data...")
        
        # Load sewerage complaints trend (2016-2022)
        sewerage_path = Path(__file__).parent / "data" / "processed" / "sewerage_complaints_yearly.csv"
        if sewerage_path.exists():
            sewerage_df = pd.read_csv(sewerage_path)
            # Use latest year as baseline, calculate growth rate
            latest_complaints = sewerage_df.iloc[-1]['sewerage_complaints']
            baseline_complaints = sewerage_df.iloc[-4]['sewerage_complaints']  # 2019
            self.sewerage_growth_rate = (latest_complaints - baseline_complaints) / baseline_complaints
            self.avg_sewerage_complaints = sewerage_df['sewerage_complaints'].mean()
            print(f"  Sewerage complaints: {self.sewerage_growth_rate:.1%} increase (2019→2022)")
        else:
            self.sewerage_growth_rate = 0.75  # Default 75% increase
            self.avg_sewerage_complaints = 95000
        
        # Load zone waste load
        waste_path = Path(__file__).parent / "data" / "processed" / "zone_waste_load.csv"
        if waste_path.exists():
            self.zone_waste = pd.read_csv(waste_path)
            self.zone_waste['waste_per_capita'] = self.zone_waste['waste_tpd'] / self.zone_waste['population'] * 1000
            print(f"  Zone waste data: {len(self.zone_waste)} zones loaded")
        else:
            self.zone_waste = None
        
        # Load pothole reports
        pothole_path = Path(__file__).parent / "data" / "processed" / "pothole_reports.csv"
        if pothole_path.exists():
            pothole_df = pd.read_csv(pothole_path)
            # Aggregate by ward
            self.pothole_by_ward = pothole_df.groupby('ward_name').agg({
                'report_id': 'count',
                'severity': lambda x: (x == 'large').sum()
            }).rename(columns={'report_id': 'total_reports', 'severity': 'large_potholes'})
            print(f"  Pothole data: {len(pothole_df)} reports across {len(self.pothole_by_ward)} wards")
        else:
            self.pothole_by_ward = None
        
        # Legacy complaints data
        complaints_path = Path(__file__).parent / "data" / "processed" / "civic_complaints_ward.csv"
        if complaints_path.exists():
            self.civic_complaints = pd.read_csv(complaints_path, index_col='ward_id')
            print(f"  Legacy complaints: {len(self.civic_complaints)} wards")
        else:
            # Generate estimates using new data insights
            self.civic_complaints = self.ward_historical.copy()
            # High flood freq = high complaints (systemic correlation)
            self.civic_complaints['drainage_complaints'] = (
                self.civic_complaints['hist_flood_freq'] * 20 + 
                np.random.poisson(15, len(self.civic_complaints))
            )
            # Scale sewerage complaints by growth rate
            base_sewerage = np.random.poisson(12, len(self.civic_complaints))
            self.civic_complaints['sewerage_complaints'] = base_sewerage * (1 + self.sewerage_growth_rate)
            self.civic_complaints['pothole_complaints'] = np.random.poisson(10, len(self.civic_complaints))
            
        return True
    
    def calculate_monsoon_preparedness(self) -> pd.DataFrame:
        """
        Calculate Monsoon Preparedness Index for each ward/zone.
        
        Preparedness Components (0-100 scale):
        1. Infrastructure Capacity (30%): Drainage quality, maintenance
        2. Historical Resilience (25%): How well ward handled past monsoons
        3. Resource Readiness (20%): Emergency response capability
        4. Vulnerability Gap (15%): Population at risk vs protection
        5. Maintenance Score (10%): Recent infrastructure improvements
        
        Returns DataFrame with preparedness scores and recommendations
        """
        print("\n" + "=" * 70)
        print("CALCULATING MONSOON PREPAREDNESS INDEX")
        print("=" * 70)
        
        results = []
        
        for ward_id in self.ward_static.index:
            static_feats = self.ward_static.loc[ward_id].to_dict()
            hist_feats = self.ward_historical.loc[ward_id].to_dict()
            
            # 1. Infrastructure Capacity (30 points)
            drain_density = static_feats.get('drain_density', 0)
            drain_capacity = min(30, drain_density * 5)
            
            if self.civic_complaints is not None and ward_id in self.civic_complaints.index:
                drainage_complaints = self.civic_complaints.loc[ward_id, 'drainage_complaints']
                sewerage_complaints = self.civic_complaints.loc[ward_id, 'sewerage_complaints']
                complaint_penalty = min(10, (drainage_complaints / 30) + (sewerage_complaints / 20))
            else:
                complaint_penalty = 0
            
            infra_capacity = max(0, drain_capacity - complaint_penalty)
            
            # 2. Historical Resilience (25 points)
            hist_flood_freq = hist_feats.get('hist_flood_freq', 0)
            monsoon_risk = hist_feats.get('monsoon_risk_score', 0.5)
            
            flood_resilience = max(0, 25 - (hist_flood_freq * 4))
            risk_resilience = (1 - monsoon_risk) * 10
            historical_resilience = flood_resilience + risk_resilience
            
            # 3. Resource Readiness (20 points)
            if 'road_density' in static_feats:
                road_access = min(10, static_feats['road_density'] * 2)
            else:
                road_access = 5
            
            if 'building_density' in static_feats:
                building_factor = min(10, static_feats['building_density'] * 5)
            else:
                building_factor = 5
            
            resource_readiness = road_access + building_factor
            
            # 4. Vulnerability Gap (15 points)
            low_lying_pct = static_feats.get('low_lying_pct', 15)
            mean_elevation = static_feats.get('mean_elevation', 215)
            
            physical_vuln = (low_lying_pct / 30 * 8) + (max(0, 220 - mean_elevation) / 20 * 7)
            vuln_gap = max(0, 15 - (physical_vuln - (infra_capacity / 3)))
            
            # 5. Maintenance Score (10 points)
            if self.pothole_by_ward is not None:
                ward_name = static_feats.get('ward_name', f'Ward_{ward_id}')
                if ward_name in self.pothole_by_ward.index:
                    potholes = self.pothole_by_ward.loc[ward_name, 'total_reports']
                    maintenance_penalty = min(5, potholes / 4)
                else:
                    maintenance_penalty = 0
            else:
                maintenance_penalty = 0
            
            sewerage_penalty = self.sewerage_growth_rate * 3
            maintenance_score = max(0, 10 - maintenance_penalty - sewerage_penalty)
            
            # Total Preparedness Score (0-100)
            preparedness = (
                infra_capacity + 
                historical_resilience + 
                resource_readiness + 
                vuln_gap + 
                maintenance_score
            )
            
            # Preparedness Level
            if preparedness >= 75:
                prep_level = "Excellent"
                recommendation = "Well-prepared. Maintain current standards."
            elif preparedness >= 60:
                prep_level = "Good"
                recommendation = "Adequate preparation. Minor improvements needed."
            elif preparedness >= 45:
                prep_level = "Moderate"
                recommendation = "Significant gaps. Prioritize drainage maintenance."
            elif preparedness >= 30:
                prep_level = "Poor"
                recommendation = "Critical improvements needed before monsoon."
            else:
                prep_level = "Critical"
                recommendation = "Emergency intervention required. High failure risk."
            
            # Identify top priority action
            component_scores = {
                'Infrastructure': infra_capacity,
                'Resilience': historical_resilience,
                'Resources': resource_readiness,
                'Vulnerability': vuln_gap,
                'Maintenance': maintenance_score
            }
            weakest = min(component_scores, key=component_scores.get)
            
            results.append({
                'ward_id': ward_id,
                'preparedness_score': round(preparedness, 1),
                'preparedness_level': prep_level,
                'infra_capacity': round(infra_capacity, 1),
                'historical_resilience': round(historical_resilience, 1),
                'resource_readiness': round(resource_readiness, 1),
                'vulnerability_gap': round(vuln_gap, 1),
                'maintenance_score': round(maintenance_score, 1),
                'weakest_component': weakest,
                'recommendation': recommendation,
                'drain_density': drain_density,
                'hist_flood_count': hist_flood_freq,
            })
        
        df = pd.DataFrame(results)
        
        print(f"\nProcessed {len(df)} wards")
        print(f"\nPreparedness Distribution:")
        print(f"  Excellent (75-100): {len(df[df['preparedness_score'] >= 75])}")
        print(f"  Good (60-74):       {len(df[(df['preparedness_score'] >= 60) & (df['preparedness_score'] < 75)])}")
        print(f"  Moderate (45-59):   {len(df[(df['preparedness_score'] >= 45) & (df['preparedness_score'] < 60)])}")
        print(f"  Poor (30-44):       {len(df[(df['preparedness_score'] >= 30) & (df['preparedness_score'] < 45)])}")
        print(f"  Critical (<30):     {len(df[df['preparedness_score'] < 30])}")
        print(f"\nAverage Preparedness: {df['preparedness_score'].mean():.1f}/100")
        
        return df
    
    def calculate_zone_preparedness(self, ward_preparedness: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate ward preparedness to zone level (12 MCD zones).
        
        Returns zone-level preparedness scores and priorities.
        """
        print("\n" + "=" * 70)
        print("CALCULATING ZONE-LEVEL PREPAREDNESS")
        print("=" * 70)
        
        # Create zone mapping from ward IDs
        zone_mapping = {}
        for ward_id in ward_preparedness['ward_id']:
            zone_letter = ''.join(filter(str.isalpha, str(ward_id)))
            if zone_letter:
                zone_mapping[ward_id] = f"Zone_{zone_letter}"
            else:
                zone_mapping[ward_id] = "Zone_Unknown"
        
        ward_preparedness['zone'] = ward_preparedness['ward_id'].map(zone_mapping)
        
        # Aggregate by zone
        zone_results = []
        for zone_name, zone_df in ward_preparedness.groupby('zone'):
            zone_results.append({
                'zone': zone_name,
                'avg_preparedness': round(zone_df['preparedness_score'].mean(), 1),
                'min_preparedness': round(zone_df['preparedness_score'].min(), 1),
                'max_preparedness': round(zone_df['preparedness_score'].max(), 1),
                'ward_count': len(zone_df),
                'critical_wards': len(zone_df[zone_df['preparedness_score'] < 30]),
                'poor_wards': len(zone_df[zone_df['preparedness_score'] < 45]),
                'top_weakness': zone_df['weakest_component'].mode()[0] if len(zone_df) > 0 else 'Unknown',
                'avg_infra_capacity': round(zone_df['infra_capacity'].mean(), 1),
                'avg_historical_resilience': round(zone_df['historical_resilience'].mean(), 1),
            })
        
        zone_df = pd.DataFrame(zone_results).sort_values('avg_preparedness')
        
        print(f"\nZone Summary ({len(zone_df)} zones):")
        for _, row in zone_df.head(5).iterrows():
            print(f"  {row['zone']}: {row['avg_preparedness']}/100 "
                  f"({row['critical_wards']} critical wards, weakness: {row['top_weakness']})")
        
        return zone_df
    
    def get_real_time_rainfall(self) -> dict:
        """Fetch real-time rainfall from OpenWeather API."""
        print("Fetching real-time weather...")
        try:
            current = fetch_current_weather_delhi()
            forecast = fetch_forecast_delhi()
            rainfall_features = calculate_rainfall_features(current, forecast)
            print(f"[OK] Current rainfall: {rainfall_features['rain_1h']:.1f}mm/h")
            return rainfall_features
        except Exception as e:
            print(f"[WARNING] Weather API error: {e}")
            # Return default minimal rainfall
            return {
                'rain_1h': 0,
                'rain_3h': 0,
                'rain_6h': 0,
                'rain_24h': 0,
                'rain_intensity': 0,
                'rain_forecast_3h': 0
            }
    
    def calculate_mpi(self, rainfall_features: dict = None, timestamp: datetime = None) -> pd.DataFrame:
        """
        Calculate MPI for all wards.
        
        MPI Components (0-100 scale):
        1. Model Probability (40%): ML model prediction
        2. Rainfall Severity (20%): Current + forecast rainfall intensity
        3. Historical Risk (15%): Past flood frequency
        4. Infrastructure Stress (15%): Drainage capacity + complaints
        5. Vulnerability (10%): Elevation + low-lying areas
        
        Returns DataFrame with MPI scores and breakdown
        """
        print("\n" + "=" * 70)
        print("CALCULATING WARD-WISE MPI")
        print("=" * 70)
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # Get rainfall features
        if rainfall_features is None:
            rainfall_features = self.get_real_time_rainfall()
        
        # Temporal features
        temporal_features = self.feature_engineer.compute_temporal_features(timestamp)
        
        # Calculate MPI for each ward
        results = []
        
        for ward_id in self.ward_static.index:
            # 1. Get model prediction (40%)
            static_feats = self.ward_static.loc[ward_id].to_dict()
            hist_feats = self.ward_historical.loc[ward_id].to_dict()
            
            X = self.feature_engineer.create_feature_vector(
                rainfall_features, static_feats, hist_feats, temporal_features
            )
            
            model_prob = float(self.model.predict_proba(X.reshape(1, -1))[0])
            model_score = model_prob * 40  # 0-40 points
            
            # 2. Rainfall Severity (20%)
            rain_total = rainfall_features['rain_3h'] + rainfall_features['rain_forecast_3h']
            if rain_total < 5:
                rain_score = 0
            elif rain_total < 15:
                rain_score = 5
            elif rain_total < 35:
                rain_score = 10
            elif rain_total < 65:
                rain_score = 15
            else:
                rain_score = 20
            
            # 3. Historical Risk (15%)
            hist_flood_freq = hist_feats.get('hist_flood_freq', 0)
            hist_score = min(15, hist_flood_freq * 2.5)
            
            # 4. Enhanced Infrastructure Stress (15%)
            drain_density = static_feats.get('drain_density', 0)
            # Poor drainage = higher stress
            drain_stress = max(0, 10 - drain_density) / 10 * 6  # 0-6 points
            
            # Sewerage complaints (proxy for drainage failure)
            if self.civic_complaints is not None and ward_id in self.civic_complaints.index:
                sewerage_complaints = self.civic_complaints.loc[ward_id, 'sewerage_complaints']
                # Normalize by average, amplify by growth rate
                sewerage_stress = min(4, sewerage_complaints / 15 * (1 + self.sewerage_growth_rate))  # 0-4 points
                
                drainage_complaints = self.civic_complaints.loc[ward_id, 'drainage_complaints']
                drainage_stress = min(3, drainage_complaints / 25)  # 0-3 points
            else:
                sewerage_stress = 0
                drainage_stress = 0
            
            # Pothole density (infrastructure degradation)
            pothole_stress = 0
            if self.pothole_by_ward is not None:
                ward_name = static_feats.get('ward_name', f'Ward_{ward_id}')
                if ward_name in self.pothole_by_ward.index:
                    potholes = self.pothole_by_ward.loc[ward_name, 'total_reports']
                    large_potholes = self.pothole_by_ward.loc[ward_name, 'large_potholes']
                    pothole_stress = min(2, (potholes / 5) + (large_potholes / 2))  # 0-2 points
            
            infra_score = drain_stress + sewerage_stress + drainage_stress + pothole_stress  # 0-15 points
            
            # 5. Enhanced Vulnerability (10%) - now includes urbanization & Yamuna proximity
            low_lying_pct = static_feats.get('low_lying_pct', 15)
            mean_elevation = static_feats.get('mean_elevation', 215)
            
            # NEW: Use flood_vulnerability_index if available (incorporates Yamuna distance + urbanization)
            if 'flood_vulnerability_index' in static_feats:
                flood_vuln_idx = static_feats['flood_vulnerability_index']
                vuln_score = flood_vuln_idx * 10  # 0-10 points (pre-normalized)
            else:
                # Fallback: legacy calculation
                elev_vuln = max(0, (220 - mean_elevation) / 15 * 5)  # 0-5 points
                lowlying_vuln = low_lying_pct / 30 * 5  # 0-5 points
                vuln_score = elev_vuln + lowlying_vuln  # 0-10 points
            
            # NEW: Urban congestion penalty (if available)
            urban_penalty = 0
            if 'urbanization_index' in static_feats:
                # High urbanization + heavy rain = flash flood risk
                urban_idx = static_feats['urbanization_index']
                rain_intensity = rainfall_features.get('rain_1h', 0)
                if rain_intensity > 10:  # Heavy rain
                    urban_penalty = urban_idx * rain_intensity / 10 * 2  # 0-2 bonus points
            
            vuln_score = min(10, vuln_score + urban_penalty)  # Cap at 10
            
            # Total MPI (0-100)
            mpi = model_score + rain_score + hist_score + infra_score + vuln_score
            
            # Risk level
            if mpi < 30:
                risk_level = "Low"
            elif mpi < 50:
                risk_level = "Moderate"
            elif mpi < 70:
                risk_level = "High"
            else:
                risk_level = "Critical"
            
            results.append({
                'ward_id': ward_id,
                'mpi_score': round(mpi, 1),
                'risk_level': risk_level,
                'model_prob': round(model_prob, 3),
                'model_contribution': round(model_score, 1),
                'rainfall_contribution': round(rain_score, 1),
                'historical_contribution': round(hist_score, 1),
                'infrastructure_contribution': round(infra_score, 1),
                'vulnerability_contribution': round(vuln_score, 1),
                'current_rain_mm': rainfall_features['rain_1h'],
                'forecast_rain_mm': rainfall_features['rain_forecast_3h'],
                'hist_flood_count': hist_flood_freq,
                'drain_density': round(drain_density, 2),
                'elevation_m': round(mean_elevation, 1),
                # Infrastructure metrics
                'yamuna_distance_km': round(static_feats.get('yamuna_distance_m', 0) / 1000, 2),
                'building_density': round(static_feats.get('building_density_per_km2', 0), 1),
                'road_density': round(static_feats.get('road_density_km_per_km2', 0), 1),
                'urbanization_index': round(static_feats.get('urbanization_index', 0), 3),
                'flood_vuln_index': round(static_feats.get('flood_vulnerability_index', 0), 3),
                # Civic failure indicators
                'sewerage_complaints': round(sewerage_stress * 15, 0) if sewerage_stress > 0 else 0,
                'drainage_complaints': round(drainage_stress * 25, 0) if drainage_stress > 0 else 0,
                'pothole_count': int(pothole_stress * 5) if pothole_stress > 0 else 0
            })
        
        df = pd.DataFrame(results)
        df = df.sort_values('mpi_score', ascending=False)
        
        return df
    
    def generate_mpi_report(self, mpi_df: pd.DataFrame, save_path: str = None):
        """Generate comprehensive MPI report."""
        print("\n" + "=" * 70)
        print("MPI REPORT - WARD-WISE FLOOD RISK")
        print("=" * 70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Summary statistics
        print(f"\nTotal wards analyzed: {len(mpi_df)}")
        print(f"\nRisk Distribution:")
        for level in ['Critical', 'High', 'Moderate', 'Low']:
            count = len(mpi_df[mpi_df['risk_level'] == level])
            pct = count / len(mpi_df) * 100
            print(f"  {level:10s}: {count:3d} wards ({pct:5.1f}%)")
        
        print(f"\nMPI Statistics:")
        print(f"  Mean MPI: {mpi_df['mpi_score'].mean():.1f}")
        print(f"  Max MPI:  {mpi_df['mpi_score'].max():.1f}")
        print(f"  Min MPI:  {mpi_df['mpi_score'].min():.1f}")
        
        # Top 10 high-risk wards
        print(f"\n{'='*70}")
        print("TOP 10 HIGH-RISK WARDS")
        print(f"{'='*70}")
        top10 = mpi_df.head(10)
        
        for idx, row in top10.iterrows():
            print(f"\n{idx+1}. Ward {row['ward_id']} - MPI: {row['mpi_score']:.1f} ({row['risk_level']})")
            print(f"   Model Probability: {row['model_prob']:.1%}")
            print(f"   Contributions: Model={row['model_contribution']:.0f}, Rain={row['rainfall_contribution']:.0f}, History={row['historical_contribution']:.0f}, Infra={row['infrastructure_contribution']:.0f}, Vuln={row['vulnerability_contribution']:.0f}")
            print(f"   Flood History: {row['hist_flood_count']} events")
            print(f"   Drain Density: {row['drain_density']:.2f} points/km²")
        
        # Save to CSV
        if save_path:
            mpi_df.to_csv(save_path, index=False)
            print(f"\n[OK] Full MPI data saved to: {save_path}")
        
        return mpi_df


def main():
    """Main MPI calculation workflow."""
    print("=" * 70)
    print("DELHI FLOOD RISK - WARD-WISE MPI CALCULATOR")
    print("=" * 70)
    
    # Initialize
    calc = MPICalculator()
    
    # Load all required data
    if not calc.load_model():
        print("[ERROR] Cannot proceed without model")
        return
    
    if not calc.load_ward_data():
        print("[ERROR] Cannot proceed without ward data")
    
    calc.load_civic_complaints()
    
    # Calculate MPI with real-time weather
    mpi_df = calc.calculate_mpi()
    
    # Generate report
    output_path = Path(__file__).parent / "data" / "processed" / "mpi_scores_latest.csv"
    calc.generate_mpi_report(mpi_df, save_path=output_path)
    
    # Calculate Monsoon Preparedness Index
    print("\n")
    preparedness_df = calc.calculate_monsoon_preparedness()
    prep_output_path = Path(__file__).parent / "data" / "processed" / "monsoon_preparedness_latest.csv"
    preparedness_df.to_csv(prep_output_path, index=False)
    print(f"\n✅ Preparedness scores saved to: {prep_output_path}")
    
    # Calculate zone-level preparedness
    zone_prep_df = calc.calculate_zone_preparedness(preparedness_df)
    zone_output_path = Path(__file__).parent / "data" / "processed" / "zone_preparedness_latest.csv"
    zone_prep_df.to_csv(zone_output_path, index=False)
    print(f"✅ Zone preparedness saved to: {zone_output_path}")
    
    # Show priority zones for intervention
    print("\n" + "=" * 70)
    print("🎯 PRIORITY ZONES FOR MONSOON PREPARATION")
    print("=" * 70)
    worst_zones = zone_prep_df.head(3)
    for idx, row in worst_zones.iterrows():
        print(f"\n{idx+1}. {row['zone']}")
        print(f"   Preparedness: {row['avg_preparedness']}/100")
        print(f"   Critical Wards: {row['critical_wards']}/{row['ward_count']}")
        print(f"   Main Weakness: {row['top_weakness']}")
        print(f"   Action: Focus on {row['top_weakness'].lower()} improvements")
    
    # Also save for frontend
    frontend_path = Path(__file__).parent.parent / "frontend" / "public" / "data" / "ward_risk.json"
    mpi_json = {}
    for _, row in mpi_df.iterrows():
        mpi_json[row['ward_id']] = {
            "risk_score": row['mpi_score'],
            "rain_mm": row['current_rain_mm'] + row['forecast_rain_mm'],
            "status": row['risk_level']
        }
    
    frontend_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(frontend_path, 'w') as f:
        json.dump(mpi_json, f, indent=2)
    
    print(f"\n[OK] Frontend data updated: {frontend_path}")
    
    print("\n" + "=" * 70)
    print("MPI CALCULATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
