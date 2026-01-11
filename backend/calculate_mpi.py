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
    """Calculate Multi-Parameter Index for each ward."""
    
    def __init__(self):
        """Initialize MPI calculator with model and data."""
        self.model = None
        self.feature_engineer = None
        self.ward_static = None
        self.ward_historical = None
        self.civic_complaints = None
        
    def load_model(self, model_path: str = "backend/model/artifacts/flood_model_v1.pkl"):
        """Load trained flood prediction model."""
        print("Loading flood prediction model...")
        try:
            self.model = FloodFailureModel.load(model_path)
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
            enhanced_path = Path("backend/data/processed/ward_static_features_enhanced.csv")
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
        sewerage_path = Path("backend/data/processed/sewerage_complaints_yearly.csv")
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
        waste_path = Path("backend/data/processed/zone_waste_load.csv")
        if waste_path.exists():
            self.zone_waste = pd.read_csv(waste_path)
            self.zone_waste['waste_per_capita'] = self.zone_waste['waste_tpd'] / self.zone_waste['population'] * 1000
            print(f"  Zone waste data: {len(self.zone_waste)} zones loaded")
        else:
            self.zone_waste = None
        
        # Load pothole reports
        pothole_path = Path("backend/data/processed/pothole_reports.csv")
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
        complaints_path = Path("backend/data/processed/civic_complaints_ward.csv")
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
    output_path = Path("backend/data/processed/mpi_scores_latest.csv")
    calc.generate_mpi_report(mpi_df, save_path=output_path)
    
    # Also save for frontend
    frontend_path = Path("frontend/public/data/ward_risk.json")
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
