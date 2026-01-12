# 🚀 FastAPI Deployment Guide

## Quick Start

### 1. Run the MPI Calculator (Generate Data)
```bash
cd backend
python calculate_mpi.py
```

This generates 3 CSV files:
- `data/processed/mpi_scores_latest.csv` - Real-time flood risk
- `data/processed/monsoon_preparedness_latest.csv` - Infrastructure readiness
- `data/processed/zone_preparedness_latest.csv` - Zone-level aggregation

### 2. Start the FastAPI Server
```bash
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Or with Python directly:
```bash
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Server will be available at**: `http://localhost:8000`

### 3. View API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📡 API Endpoints Overview

### **Flood Risk APIs (MPI)**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/predict/all` | GET | All 272 wards with MPI scores |
| `/api/wards/{ward_id}` | GET | Detailed ward risk breakdown |
| `/api/mpi-summary` | GET | Top 10 high-risk wards + stats |
| `/api/test/prediction` | GET | Heavy rain scenario test |

### **Monsoon Preparedness APIs (NEW)**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/preparedness/all` | GET | All ward preparedness scores |
| `/api/preparedness/zones` | GET | Zone-level aggregation |
| `/api/preparedness/ward/{ward_id}` | GET | Detailed preparedness assessment |

### **Utility APIs**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | System health check |
| `/` | GET | API welcome message |

---

## 📊 JSON Response Formats

### 1. **MPI (Real-Time Flood Risk)** - `/api/predict/all`

```json
{
  "timestamp": "2026-01-12T08:30:45.123456",
  "total_wards": 272,
  "risk_summary": {
    "Low": 150,
    "Moderate": 100,
    "High": 20,
    "Critical": 2
  },
  "wards": [
    {
      "ward_id": "038E",
      "mpi_score": 55.8,
      "risk_level": "High",
      "model_prob": 0.019,
      "model_contribution": 0.8,
      "rainfall_contribution": 20.0,
      "historical_contribution": 15.0,
      "infrastructure_contribution": 12.0,
      "vulnerability_contribution": 8.0,
      "current_rain_mm": 25.0,
      "forecast_rain_mm": 50.0,
      "hist_flood_count": 8,
      "drain_density": 0.84,
      "mean_elevation": 209.5
    },
    {
      "ward_id": "042W",
      "mpi_score": 38.2,
      "risk_level": "Moderate",
      "model_prob": 0.017,
      "model_contribution": 0.7,
      "rainfall_contribution": 20.0,
      "historical_contribution": 10.0,
      "infrastructure_contribution": 5.5,
      "vulnerability_contribution": 2.0,
      "current_rain_mm": 25.0,
      "forecast_rain_mm": 50.0,
      "hist_flood_count": 4,
      "drain_density": 3.2,
      "mean_elevation": 218.3
    }
  ]
}
```

### 2. **Monsoon Preparedness Index** - `/api/preparedness/all`

```json
{
  "timestamp": "2026-01-12T08:30:45.123456",
  "total_wards": 272,
  "average_preparedness": 52.3,
  "preparedness_distribution": {
    "excellent": 15,
    "good": 45,
    "moderate": 120,
    "poor": 80,
    "critical": 12
  },
  "wards": [
    {
      "ward_id": "038E",
      "preparedness_score": 35.2,
      "preparedness_level": "Poor",
      "infra_capacity": 8.5,
      "historical_resilience": 6.0,
      "resource_readiness": 12.0,
      "vulnerability_gap": 5.7,
      "maintenance_score": 3.0,
      "weakest_component": "Infrastructure",
      "recommendation": "Critical improvements needed before monsoon.",
      "drain_density": 0.84,
      "hist_flood_count": 8
    },
    {
      "ward_id": "042W",
      "preparedness_score": 68.4,
      "preparedness_level": "Good",
      "infra_capacity": 22.0,
      "historical_resilience": 18.5,
      "resource_readiness": 15.0,
      "vulnerability_gap": 8.9,
      "maintenance_score": 4.0,
      "weakest_component": "Maintenance",
      "recommendation": "Adequate preparation. Minor improvements needed.",
      "drain_density": 3.2,
      "hist_flood_count": 4
    }
  ]
}
```

### 3. **Zone-Level Preparedness** - `/api/preparedness/zones`

```json
{
  "timestamp": "2026-01-12T08:30:45.123456",
  "total_zones": 12,
  "average_preparedness": 52.3,
  "priority_zones": [
    {
      "zone": "Zone_E",
      "avg_preparedness": 38.5,
      "min_preparedness": 22.3,
      "max_preparedness": 55.8,
      "ward_count": 25,
      "critical_wards": 3,
      "poor_wards": 18,
      "top_weakness": "Infrastructure",
      "avg_infra_capacity": 12.5,
      "avg_historical_resilience": 8.2
    },
    {
      "zone": "Zone_W",
      "avg_preparedness": 42.1,
      "min_preparedness": 28.7,
      "max_preparedness": 62.3,
      "ward_count": 23,
      "critical_wards": 1,
      "poor_wards": 15,
      "top_weakness": "Maintenance",
      "avg_infra_capacity": 15.8,
      "avg_historical_resilience": 12.3
    }
  ],
  "all_zones": [
    // ... all 12 zones
  ]
}
```

### 4. **Ward Details** - `/api/wards/{ward_id}`

```json
{
  "ward_id": "038E",
  "ward_info": {
    "ward_name": "Ward 038E",
    "area_sqkm": 2.34,
    "drain_density": 0.84,
    "mean_elevation": 209.5,
    "elevation_std": 3.2,
    "low_lying_pct": 28.5,
    "slope_mean": 1.2
  },
  "current_risk": {
    "mpi_score": 55.8,
    "risk_level": "High",
    "model_probability": 0.019,
    "rainfall_3h": 75.0,
    "explanation": "Heavy rainfall with poor drainage capacity"
  },
  "preparedness": {
    "preparedness_score": 35.2,
    "preparedness_level": "Poor",
    "recommendation": "Critical improvements needed before monsoon.",
    "weakest_component": "Infrastructure"
  },
  "historical": {
    "flood_count": 8,
    "monsoon_risk_score": 0.75,
    "last_major_flood": "2023-08-15"
  }
}
```

### 5. **MPI Summary** - `/api/mpi-summary`

```json
{
  "timestamp": "2026-01-12T08:30:45.123456",
  "total_wards": 272,
  "risk_distribution": {
    "Low": 150,
    "Moderate": 100,
    "High": 20,
    "Critical": 2
  },
  "average_mpi": 35.6,
  "top_10_high_risk": [
    {
      "ward_id": "038E",
      "mpi_score": 55.8,
      "risk_level": "High",
      "reason": "Heavy rain + poor drainage"
    },
    {
      "ward_id": "042W",
      "mpi_score": 48.2,
      "risk_level": "Moderate",
      "reason": "Historical flooding pattern"
    }
    // ... 8 more wards
  ],
  "critical_alerts": [
    {
      "ward_id": "038E",
      "mpi_score": 55.8,
      "message": "HIGH RISK: Deploy pumps and monitor drainage"
    }
  ]
}
```

---

## 💾 Downloading JSON Data for Your Friend

### **Method 1: Direct API Calls**

Your friend can use curl, wget, or browser:

```bash
# Get all ward MPI scores
curl http://your-server:8000/api/predict/all > mpi_data.json

# Get all preparedness scores
curl http://your-server:8000/api/preparedness/all > preparedness_data.json

# Get zone-level preparedness
curl http://your-server:8000/api/preparedness/zones > zone_preparedness.json
```

### **Method 2: Python Script**

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Get MPI data
mpi_response = requests.get(f"{BASE_URL}/api/predict/all")
mpi_data = mpi_response.json()

# Save to file
with open("mpi_scores.json", "w") as f:
    json.dump(mpi_data, f, indent=2)

# Get Preparedness data
prep_response = requests.get(f"{BASE_URL}/api/preparedness/all")
prep_data = prep_response.json()

with open("preparedness_scores.json", "w") as f:
    json.dump(prep_data, f, indent=2)

print(f"Downloaded {len(mpi_data['wards'])} ward MPI scores")
print(f"Downloaded {len(prep_data['wards'])} ward preparedness scores")
```

### **Method 3: JavaScript/Frontend**

```javascript
// Fetch MPI data
fetch('http://localhost:8000/api/predict/all')
  .then(response => response.json())
  .then(data => {
    console.log(`Loaded ${data.total_wards} wards`);
    console.log(`Critical risk wards: ${data.risk_summary.Critical}`);
    
    // Process ward data
    data.wards.forEach(ward => {
      if (ward.risk_level === 'Critical') {
        console.log(`ALERT: Ward ${ward.ward_id} has MPI ${ward.mpi_score}`);
      }
    });
  });

// Fetch Preparedness data
fetch('http://localhost:8000/api/preparedness/all')
  .then(response => response.json())
  .then(data => {
    console.log(`Average preparedness: ${data.average_preparedness}/100`);
    
    // Find poorly prepared wards
    const poorWards = data.wards.filter(w => w.preparedness_score < 30);
    console.log(`${poorWards.length} wards need urgent intervention`);
  });
```

---

## 📤 Sharing Data with Your Friend

### **Option 1: Host the API Online**

Deploy to:
- **Render.com** (Free tier): Already configured in `render.yaml`
- **Railway.app** (Free tier)
- **Heroku** (Paid)
- **DigitalOcean** (Paid)

Then share the URL: `https://your-app-name.onrender.com/api/predict/all`

### **Option 2: Export Static JSON Files**

```bash
# Run MPI calculator
cd backend
python calculate_mpi.py

# This creates files in backend/data/processed/:
# - mpi_scores_latest.csv
# - monsoon_preparedness_latest.csv
# - zone_preparedness_latest.csv

# Convert CSVs to JSON
python -c "
import pandas as pd
import json

# MPI data
mpi_df = pd.read_csv('data/processed/mpi_scores_latest.csv')
with open('mpi_export.json', 'w') as f:
    json.dump(mpi_df.to_dict('records'), f, indent=2)

# Preparedness data
prep_df = pd.read_csv('data/processed/monsoon_preparedness_latest.csv')
with open('preparedness_export.json', 'w') as f:
    json.dump(prep_df.to_dict('records'), f, indent=2)

print('✅ Exported JSON files')
"
```

Now send your friend:
- `mpi_export.json` (Real-time flood risk)
- `preparedness_export.json` (Infrastructure readiness)

### **Option 3: Create a Simple Data Package**

```python
# create_data_package.py
import pandas as pd
import json
from datetime import datetime

# Load data
mpi_df = pd.read_csv('backend/data/processed/mpi_scores_latest.csv')
prep_df = pd.read_csv('backend/data/processed/monsoon_preparedness_latest.csv')
zone_df = pd.read_csv('backend/data/processed/zone_preparedness_latest.csv')

# Create comprehensive package
data_package = {
    "metadata": {
        "generated_at": datetime.now().isoformat(),
        "version": "1.0",
        "total_wards": len(mpi_df),
        "data_sources": [
            "IMD Rainfall (2022-2025)",
            "CartoDEM Elevation",
            "INDOFLOODS Historical Data",
            "MCD Ward Boundaries",
            "Civic Complaints (2016-2022)"
        ]
    },
    "flood_risk": {
        "description": "Real-time flood risk scores (0-100) for next 3 hours",
        "wards": mpi_df.to_dict('records')
    },
    "preparedness": {
        "description": "Infrastructure readiness assessment (0-100)",
        "wards": prep_df.to_dict('records'),
        "zones": zone_df.to_dict('records')
    },
    "risk_thresholds": {
        "Low": "0-30 (Normal monitoring)",
        "Moderate": "30-50 (Increased vigilance)",
        "High": "50-70 (Pre-emptive alerts)",
        "Critical": "70-100 (Emergency response)"
    }
}

# Save comprehensive package
with open('delhi_flood_data_package.json', 'w') as f:
    json.dump(data_package, f, indent=2)

print(f"✅ Created data package with {len(mpi_df)} wards")
print(f"   File size: {len(json.dumps(data_package))/1024:.1f} KB")
```

---

## 🔐 Production Deployment Checklist

### 1. **Environment Variables**
Create `.env` file:
```bash
DATABASE_URL=postgresql://...
OPENWEATHER_API_KEY=your_key_here
ALLOWED_ORIGINS=https://your-frontend.com
DEBUG=False
```

### 2. **Update CORS Origins**
In `backend/api/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.com",
        "https://your-api-docs.com"
    ],  # Remove "*" in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. **Add Rate Limiting**
```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/predict/all")
@limiter.limit("100/hour")  # 100 requests per hour
async def get_all_predictions():
    ...
```

### 4. **Deploy to Render.com**

Your `render.yaml` is already configured. Just:

```bash
git add .
git commit -m "Add preparedness endpoints"
git push origin main
```

Render will auto-deploy to: `https://delhi-flood-api.onrender.com`

---

## 📊 Data Update Schedule

To keep data fresh:

### **Cron Job (Linux/Mac)**
```bash
# Add to crontab -e
0 */6 * * * cd /path/to/backend && python calculate_mpi.py
```

### **Task Scheduler (Windows)**
```powershell
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "calculate_mpi.py" -WorkingDirectory "C:\path\to\backend"
$trigger = New-ScheduledTaskTrigger -Once -At 6am -RepetitionInterval (New-TimeSpan -Hours 6)
Register-ScheduledTask -TaskName "UpdateMPI" -Action $action -Trigger $trigger
```

### **Background Task in FastAPI**
```python
from fastapi import BackgroundTasks
import subprocess

def update_mpi_scores():
    subprocess.run(["python", "calculate_mpi.py"], cwd="backend")

@app.post("/api/admin/refresh")
async def refresh_data(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_mpi_scores)
    return {"message": "Refresh started"}
```

---

## 🎯 Quick Test

Start server and test all endpoints:

```bash
# Terminal 1: Start server
cd backend
python -m uvicorn api.main:app --reload --port 8000

# Terminal 2: Test endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/predict/all | jq '.total_wards'
curl http://localhost:8000/api/preparedness/all | jq '.average_preparedness'
curl http://localhost:8000/api/preparedness/zones | jq '.priority_zones[0]'
```

Expected output:
```
✅ 272 wards loaded
✅ Average preparedness: 52.3/100
✅ Priority Zone: Zone_E (38.5/100)
```

---

## 📞 Support

For issues, check:
- Swagger UI: http://localhost:8000/docs
- Server logs in terminal
- CSV files in `backend/data/processed/`

**Both MPI and Preparedness data are now fully accessible via REST API!** 🚀
