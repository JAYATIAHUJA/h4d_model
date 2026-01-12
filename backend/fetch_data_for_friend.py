"""
Script to fetch Delhi Flood Risk Data for sharing with friends
This script downloads both MPI and Monsoon Preparedness Index data in JSON format
"""
import requests
import json
from datetime import datetime

# API Base URL (make sure the server is running)
BASE_URL = "http://localhost:8000"

def fetch_and_save_data():
    """Fetch all data endpoints and save to JSON files"""
    
    print("=" * 70)
    print("DELHI FLOOD RISK DATA EXPORTER")
    print("=" * 70)
    print()
    
    # 1. Fetch MPI (Multi-Parameter Index - Real-time Flood Risk)
    print("1. Fetching MPI (Real-time Flood Risk) data...")
    try:
        # POST request with default rainfall values
        payload = {
            "rainfall": {
                "rain_1h": 0.0,
                "rain_3h": 0.0,
                "rain_6h": 0.0,
                "rain_24h": 0.0,
                "rain_forecast_3h": 0.0
            }
        }
        response = requests.post(f"{BASE_URL}/api/predict/all", json=payload)
        if response.status_code == 200:
            mpi_data = response.json()
            
            # Save to file
            filename = f"mpi_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(mpi_data, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ MPI data saved to: {filename}")
            print(f"   📊 Total wards: {mpi_data['total_wards']}")
            print(f"   📊 Risk summary:")
            for level, count in mpi_data['risk_summary'].items():
                print(f"      {level}: {count} wards")
        else:
            print(f"   ❌ Failed to fetch MPI data: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 2. Fetch Monsoon Preparedness Index (All Wards)
    print("2. Fetching Monsoon Preparedness Index (All Wards)...")
    try:
        response = requests.get(f"{BASE_URL}/api/preparedness/all")
        if response.status_code == 200:
            prep_data = response.json()
            
            # Save to file
            filename = f"preparedness_all_wards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(prep_data, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ Preparedness data saved to: {filename}")
            print(f"   📊 Total wards: {prep_data['total_wards']}")
            print(f"   📊 Average preparedness: {prep_data['average_preparedness']:.1f}/100")
            print(f"   📊 Distribution:")
            for level, count in prep_data['preparedness_distribution'].items():
                print(f"      {level}: {count} wards")
        else:
            print(f"   ❌ Failed to fetch preparedness data: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 3. Fetch Zone-level Preparedness
    print("3. Fetching Zone-level Preparedness...")
    try:
        response = requests.get(f"{BASE_URL}/api/preparedness/zones")
        if response.status_code == 200:
            zone_data = response.json()
            
            # Save to file
            filename = f"preparedness_zones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(zone_data, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ Zone preparedness saved to: {filename}")
            print(f"   📊 Total zones: {zone_data['total_zones']}")
            print(f"   📊 Average preparedness: {zone_data['average_preparedness']:.1f}/100")
            print(f"   📊 Priority zones:")
            for zone in zone_data['priority_zones'][:3]:
                print(f"      {zone['zone']}: {zone['avg_preparedness']:.1f}/100 ({zone['critical_wards']} critical)")
        else:
            print(f"   ❌ Failed to fetch zone data: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("=" * 70)
    print("✅ DATA EXPORT COMPLETE")
    print("=" * 70)
    print()
    print("📁 Files created:")
    print("   1. mpi_data_*.json - Real-time flood risk for all wards")
    print("   2. preparedness_all_wards_*.json - Infrastructure preparedness for all wards")
    print("   3. preparedness_zones_*.json - Zone-level preparedness summary")
    print()
    print("📧 Share these files with your friend!")
    print("   They contain complete Delhi flood risk and preparedness data in JSON format.")
    print()

def test_single_ward():
    """Example: Fetch data for a specific ward"""
    print("=" * 70)
    print("EXAMPLE: Fetching data for Ward 038E (highest MPI)")
    print("=" * 70)
    print()
    
    ward_id = "038E"
    
    # Get ward preparedness
    try:
        response = requests.get(f"{BASE_URL}/api/preparedness/ward/{ward_id}")
        if response.status_code == 200:
            ward_data = response.json()
            print(f"Ward: {ward_data['ward_id']}")
            print(f"Preparedness Score: {ward_data['preparedness_score']:.1f}/100 ({ward_data['preparedness_level']})")
            print(f"Weakest Component: {ward_data['weakest_component']}")
            print(f"Recommendation: {ward_data['recommendation']}")
            print()
            print("Component Scores:")
            for comp, score in ward_data['component_scores'].items():
                print(f"  {comp}: {score:.1f}/100")
        else:
            print(f"Failed to fetch ward data: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ API Server is running at {BASE_URL}")
        print()
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: API server is not running!")
        print(f"Please start the server first:")
        print(f"  cd backend")
        print(f"  python -m uvicorn api.main:app --reload --port 8000")
        print()
        exit(1)
    
    # Fetch all data
    fetch_and_save_data()
    
    # Example single ward query
    test_single_ward()
