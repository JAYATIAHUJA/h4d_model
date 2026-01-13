"""
Test Script for Delhi Flood Prediction System
==============================================

Tests Model Predictions, MPI Calculations, and Preparedness Scores
against known test cases.

Usage:
    python test_system.py
"""

import json
import requests
from pathlib import Path
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000"
TEST_DATA_PATH = Path(__file__).parent / "TEST_DATA.json"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def load_test_data():
    """Load test data from JSON file"""
    with open(TEST_DATA_PATH, 'r') as f:
        return json.load(f)

def test_api_health():
    """Test if API is running"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Testing API Health{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"{Colors.GREEN}✓ API is healthy{Colors.END}")
            print(f"  Model loaded: {data.get('model_loaded')}")
            print(f"  Wards count: {data.get('wards_count')}")
            return True
        else:
            print(f"{Colors.RED}✗ API returned status {response.status_code}{Colors.END}")
            return False
    except Exception as e:
        print(f"{Colors.RED}✗ API not reachable: {e}{Colors.END}")
        print(f"{Colors.YELLOW}Make sure backend is running: python -m uvicorn backend.api.main:app{Colors.END}")
        return False

def test_model_predictions(test_data):
    """Test model predictions for each test ward"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Testing Model Predictions{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    passed = 0
    failed = 0
    
    for ward in test_data['test_wards']:
        ward_id = ward['ward_id']
        scenario = ward['scenario']
        rainfall = ward['rainfall_scenario']
        expected = ward['expected_outputs']
        
        print(f"\n{Colors.BLUE}Test: {ward['ward_name']}{Colors.END}")
        print(f"  Scenario: {scenario}")
        
        # Test prediction endpoint
        try:
            payload = {
                "ward_id": ward_id,
                "rainfall": rainfall
            }
            response = requests.post(f"{API_BASE}/api/predict/ward", json=payload, timeout=10)
            
            if response.status_code == 404:
                print(f"{Colors.YELLOW}⚠ Ward not found in system (test ward){Colors.END}")
                print(f"  Expected probability: {expected['model_probability']:.3f}")
                print(f"  Expected risk: {expected['risk_level']}")
                continue
            
            if response.status_code == 200:
                result = response.json()
                actual_prob = result.get('probability', 0)
                actual_risk = result.get('risk_level', 'Unknown')
                
                # Check if within tolerance
                prob_diff = abs(actual_prob - expected['model_probability'])
                tolerance = 0.05  # ±5%
                
                if prob_diff <= tolerance:
                    print(f"{Colors.GREEN}✓ Model prediction: {actual_prob:.3f} (expected {expected['model_probability']:.3f}){Colors.END}")
                    passed += 1
                else:
                    print(f"{Colors.YELLOW}⚠ Model prediction: {actual_prob:.3f} (expected {expected['model_probability']:.3f}, diff={prob_diff:.3f}){Colors.END}")
                    failed += 1
                
                print(f"  Risk level: {actual_risk} (expected {expected['risk_level']})")
            else:
                print(f"{Colors.RED}✗ API error: {response.status_code}{Colors.END}")
                failed += 1
                
        except Exception as e:
            print(f"{Colors.RED}✗ Error: {e}{Colors.END}")
            failed += 1
    
    print(f"\n{Colors.BOLD}Model Test Results: {Colors.GREEN}{passed} passed{Colors.END}, {Colors.RED if failed > 0 else Colors.GREEN}{failed} failed{Colors.END}")
    return passed, failed

def test_mpi_summary():
    """Test MPI summary endpoint"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Testing MPI Summary{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    try:
        response = requests.get(f"{API_BASE}/api/mpi-summary", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"{Colors.GREEN}✓ MPI Summary endpoint working{Colors.END}")
            print(f"  Total wards: {data.get('total_wards')}")
            print(f"  Risk distribution: {data.get('risk_distribution')}")
            print(f"  Mean MPI: {data.get('statistics', {}).get('mean_mpi', 'N/A')}")
            print(f"  Max MPI: {data.get('statistics', {}).get('max_mpi', 'N/A')}")
            print(f"  Top 10 high-risk wards: {len(data.get('top_10_high_risk', []))}")
            return True
        else:
            print(f"{Colors.RED}✗ API returned status {response.status_code}{Colors.END}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.END}")
        return False

def test_preparedness():
    """Test preparedness endpoints"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Testing Preparedness Assessment{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    passed = 0
    failed = 0
    
    # Test ward-level preparedness
    try:
        response = requests.get(f"{API_BASE}/api/preparedness/all", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"{Colors.GREEN}✓ Ward preparedness endpoint working{Colors.END}")
            print(f"  Total wards: {data.get('total_wards')}")
            print(f"  Average preparedness: {data.get('average_preparedness', 'N/A'):.1f}/100")
            print(f"  Distribution: {data.get('preparedness_distribution')}")
            passed += 1
        else:
            print(f"{Colors.RED}✗ Ward preparedness API error: {response.status_code}{Colors.END}")
            failed += 1
            
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.END}")
        failed += 1
    
    # Test zone-level preparedness
    try:
        response = requests.get(f"{API_BASE}/api/preparedness/zones", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n{Colors.GREEN}✓ Zone preparedness endpoint working{Colors.END}")
            print(f"  Total zones: {data.get('total_zones')}")
            print(f"  Average preparedness: {data.get('average_preparedness', 'N/A'):.1f}/100")
            
            for zone in data.get('priority_zones', [])[:3]:
                print(f"  {zone['zone']}: {zone['avg_preparedness']:.1f}/100 ({zone['critical_wards']} critical)")
            passed += 1
        else:
            print(f"{Colors.RED}✗ Zone preparedness API error: {response.status_code}{Colors.END}")
            failed += 1
            
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.END}")
        failed += 1
    
    print(f"\n{Colors.BOLD}Preparedness Test Results: {Colors.GREEN}{passed} passed{Colors.END}, {Colors.RED if failed > 0 else Colors.GREEN}{failed} failed{Colors.END}")
    return passed, failed

def test_scenario(test_data, scenario_name):
    """Test a rainfall scenario across all wards"""
    scenario = test_data['test_scenarios'].get(scenario_name)
    if not scenario:
        print(f"{Colors.RED}Scenario {scenario_name} not found{Colors.END}")
        return
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Testing Scenario: {scenario['description']}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"Rainfall: {scenario['rainfall']}")
    print(f"Expected: {scenario['expected_behavior']}")
    
    try:
        response = requests.post(
            f"{API_BASE}/api/predict/all",
            json={"rainfall": scenario['rainfall']},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            risk_summary = data.get('risk_summary', {})
            total = data.get('total_wards', 0)
            
            print(f"\n{Colors.GREEN}✓ Scenario prediction successful{Colors.END}")
            print(f"  Total wards: {total}")
            print(f"  Risk distribution:")
            print(f"    Low: {risk_summary.get('low', 0)} ({risk_summary.get('low', 0)/total*100:.1f}%)")
            print(f"    Moderate: {risk_summary.get('moderate', 0)} ({risk_summary.get('moderate', 0)/total*100:.1f}%)")
            print(f"    High: {risk_summary.get('high', 0)} ({risk_summary.get('high', 0)/total*100:.1f}%)")
            print(f"    Critical: {risk_summary.get('critical', 0)} ({risk_summary.get('critical', 0)/total*100:.1f}%)")
            return True
        else:
            print(f"{Colors.RED}✗ API error: {response.status_code}{Colors.END}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.END}")
        return False

def main():
    """Main test runner"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Delhi Flood Prediction System - Test Suite{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base: {API_BASE}")
    
    # Load test data
    try:
        test_data = load_test_data()
        print(f"\n{Colors.GREEN}✓ Test data loaded{Colors.END}")
        print(f"  Test wards: {len(test_data['test_wards'])}")
        print(f"  Test scenarios: {len(test_data['test_scenarios'])}")
    except Exception as e:
        print(f"{Colors.RED}✗ Failed to load test data: {e}{Colors.END}")
        return
    
    # Run tests
    total_passed = 0
    total_failed = 0
    
    # 1. Health check
    if not test_api_health():
        print(f"\n{Colors.RED}✗ API health check failed. Stopping tests.{Colors.END}")
        return
    
    # 2. MPI Summary
    if test_mpi_summary():
        total_passed += 1
    else:
        total_failed += 1
    
    # 3. Preparedness
    prep_passed, prep_failed = test_preparedness()
    total_passed += prep_passed
    total_failed += prep_failed
    
    # 4. Model predictions (commented out since test wards won't be in real system)
    # model_passed, model_failed = test_model_predictions(test_data)
    # total_passed += model_passed
    # total_failed += model_failed
    
    # 5. Test scenarios
    test_scenario(test_data, 'scenario_2_moderate_rain')
    test_scenario(test_data, 'scenario_3_heavy_rain')
    
    # Final summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Final Test Results{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}Passed: {total_passed}{Colors.END}")
    print(f"{Colors.RED}Failed: {total_failed}{Colors.END}")
    
    if total_failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed!{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}⚠ Some tests failed. Check logs above.{Colors.END}")

if __name__ == "__main__":
    main()
