# API Contract: Frontend ↔ Backend

## For Dashboard Developer 📊

This document explains exactly what data to send and what you'll receive for the Delhi flood prediction dashboard.

**API Base URL (Local)**: `http://localhost:8000`
**API Base URL (Production)**: `https://your-app-name.onrender.com`

---

## 🎯 Main Dashboard Use Cases

### 1. **Get Current MPI Scores (Flood Risk Assessment)**
**Endpoint**: `GET /api/mpi-summary`

**What Frontend Sends**: Nothing (GET request)

**What Backend Returns**:
```json
{
  "timestamp": "2026-01-12T10:30:00",
  "total_wards": 272,
  "risk_distribution": {
    "Low": 242,
    "Moderate": 30,
    "High": 0,
    "Critical": 0
  },
  "statistics": {
    "mean_mpi": 23.0,
    "max_mpi": 36.7,
    "min_mpi": 10.0
  },
  "top_10_high_risk": [
    {
      "ward_id": "038E",
      "mpi_score": 36.7,
      "risk_level": "Moderate",
      "flood_history": 8.0
    }
  ]
}
```

**Use in Dashboard**:
- Plot all 272 wards on map with color coding based on MPI scores
- Show risk summary counts in legend
- Display Top 10 high-risk wards
- Auto-refresh every 30 minutes

---

### 2. **Get Ward Details (Click on Map)**
**Endpoint**: `GET /api/wards/{ward_id}`

**What Frontend Sends**: Ward ID in URL
```
GET /api/wards/038E
```

**What Backend Returns**:
```json
{
  "ward_id": "038E",
  "static_features": {
    "area_sqkm": 8.93,
    "drain_density": 0.84,
    "mean_elevation": 206.2,
    "elevation_std": 12.5,
    "low_lying_pct": 22.9,
    "slope_mean": 1.2
  },
  "historical": {
    "hist_flood_freq": 8.0,
    "monsoon_risk_score": 0.72,
    "complaint_baseline": 145
  }
}
```

**Use in Dashboard**:
- Show detailed ward popup/sidebar
- Display infrastructure metrics
- Show historical flood patterns

---

### 3. **Get Monsoon Preparedness - All Wards (Infrastructure Readiness)**
**Endpoint**: `GET /api/preparedness/all`

**What Frontend Sends**: Nothing (GET request)

**What Backend Returns**:
```json
{
  "timestamp": "2026-01-12T08:25:22",
  "total_wards": 272,
  "average_preparedness": 47.9,
  "preparedness_distribution": {
    "excellent": 0,
    "good": 24,
    "moderate": 154,
    "poor": 78,
    "critical": 16
  },
  "wards": [
    {
      "ward_id": "038E",
      "preparedness_score": 25.5,
      "preparedness_level": "Critical",
      "infra_capacity": 0.0,
      "historical_resilience": 5.8,
      "resource_readiness": 10,
      "vulnerability_gap": 2.0,
      "maintenance_score": 7.7,
      "weakest_component": "Infrastructure",
      "recommendation": "Emergency intervention required. High failure risk.",
      "drain_density": 0.84,
      "hist_flood_count": 8.0
    }
  ]
}
```

**Use in Dashboard**:
- Show infrastructure preparedness heatmap
- Identify wards needing urgent improvements
- Display component breakdown

---

### 4. **Get Zone-level Preparedness**
**Endpoint**: `GET /api/preparedness/zones`

**What Frontend Sends**: Nothing (GET request)

**What Backend Returns**:
```json
{
  "timestamp": "2026-01-12T08:25:24",
  "total_zones": 3,
  "average_preparedness": 47.6,
  "priority_zones": [
    {
      "zone": "Zone_E",
      "avg_preparedness": 45.2,
      "min_preparedness": 25.5,
      "max_preparedness": 65.7,
      "ward_count": 64,
      "critical_wards": 4,
      "poor_wards": 33,
      "top_weakness": "Infrastructure",
      "avg_infra_capacity": 2.7,
      "avg_historical_resilience": 18.0
    },
    {
      "zone": "Zone_S",
      "avg_preparedness": 47.7,
      "critical_wards": 11
    },
    {
      "zone": "Zone_N",
      "avg_preparedness": 49.8,
      "critical_wards": 1
    }
  ]
}
```

**Use in Dashboard**:
- Zone-level aggregation for planning
- Priority rankings for intervention
- Compare zones performance

---

### 5. **Get GeoJSON for Map Visualization**
**Endpoint**: `GET /api/risk-data`

**What Frontend Sends**: Nothing (GET request)

**What Backend Returns**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [77.2090, 28.6139]
      },
      "properties": {
        "ward_id": "038E",
        "ward_name": "Ward_038E",
        "mpi_score": 36.7,
        "risk_level": "moderate",
        "probability": 0.023
      }
    }
  ]
}
```

**Use in Dashboard**:
- Direct Leaflet/Mapbox integration
- Color-coded markers
- Popup on click

---

## 📊 Dashboard Features to Build

### Required Components:

1. **Map View** (Main Screen)
   - 272 ward markers color-coded by MPI risk scores
   - Legend: Low (green), Moderate (yellow), High (orange), Critical (red)
   - Click ward → show popup with details
   - Data from: `GET /api/mpi-summary`

2. **Ward Details Sidebar**
   - Click ward → GET `/api/wards/{ward_id}`
   - Show:
     - Ward name, elevation, drainage
     - Historical floods count
     - Infrastructure metrics
     - Current MPI score

3. **Top 10 High-Risk List**
   - From `/api/mpi-summary`
   - Auto-refresh every 30 mins
   - Sort by MPI score

4. **Preparedness Dashboard**
   - From `/api/preparedness/all`
   - Show infrastructure gaps
   - Recommendations for each ward
   - Color-code by preparedness level

5. **Zone Comparison View**
   - From `/api/preparedness/zones`
   - Compare 3 zones (North, South, East)
   - Show priority areas for intervention

---

## 🎨 Color Coding

```javascript
function getRiskColor(risk_level) {
  const colors = {
    'low': '#4CAF50',      // Green
    'moderate': '#FFC107', // Yellow
    'high': '#FF9800',     // Orange
    'critical': '#F44336'  // Red
  };
  return colors[risk_level.toLowerCase()] || '#999';
}

function getPreparednessColor(score) {
  if (score >= 75) return '#4CAF50';  // Excellent - Green
  if (score >= 60) return '#8BC34A';  // Good - Light Green
  if (score >= 45) return '#FFC107';  // Moderate - Yellow
  if (score >= 30) return '#FF9800';  // Poor - Orange
  return '#F44336';                   // Critical - Red
}
```

---

## 🔄 Recommended Update Intervals

- **Map data**: Every 30 minutes (real-time weather changes)
- **Ward details**: On-demand (when user clicks)
- **Scenario testing**: On-demand (when user adjusts sliders)
- **Top 10 list**: Every 30 minutes
- **Preparedness data**: Daily (infrastructure doesn't change frequently)

---

## 📱 ExaMPI Data and Display on Map:
```javascript
async function loadMPIData() {
  const response = await fetch('http://localhost:8000/api/mpi-summary');
  const data = await response.json();
  
  console.log(`Total wards: ${data.total_wards}`);
  console.log(`Risk distribution:`, data.risk_distribution);
  
  // Display top 10 high-risk wards
  data.top_10_high_risk.forEach(ward => {
    console.log(`${ward.ward_id}: MPI ${ward.mpi_score} - ${ward.risk_level}`);
  });
  
  // For map visualization, use GeoJSON endpoint
  const geoResponse = await fetch('http://localhost:8000/api/risk-data');
  const geoData = await geoResponse.json();
  
  // Add markers to map
  geoData.features.forEach(feature => {
    const color = getRiskColor(feature.properties.risk_level);
    // Add marker to map with color
  });
}
```

### Get Ward Details on Click:
```javascript
async function showWardDetails(wardId) {
  const response = await fetch(`http://localhost:8000/api/wards/${wardId}`);
  const ward = await response.json();
  
  console.log(`Ward ${ward.ward_id}:`);
  console.log(`- Area: ${ward.static_features.area_sqkm} km²`);
  console.log(`- Drain Density: ${ward.static_features.drain_density}`);
  console.log(`- Historical Floods: ${ward.historical.hist_flood_freq}`
  const data = await response.json();
  updateMap(data.wards);
}
```

### Get Preparedness Data:
```javascript
async function loadPreparedness() {
  const response = await fetch('http://localhost:8000/api/preparedness/all');
  const data = await response.json();
  
  console.log(`Average preparedness: ${data.average_preparedness}/100`);
  console.log(`Critical wards: ${data.preparedness_distribution.critical}`);
  
  // Display on dashboard
  data.wards.forEach(ward => {
    if (ward.preparedness_level === 'Critical') {
      console.log(`${ward.ward_id}: ${ward.recommendation}`);
    }
  });
}
```

---
critical wards on dashboard
  data.wards.forEach(ward => {
    if (ward.preparedness_level === 'Critical') {
      console.log(`${ward.ward_id}: ${ward.recommendation}`);
    }
  });
}
```

### Get Zone-level Preparedness:
```javascript
async function loadZonePreparedness() {
  const response = await fetch('http://localhost:8000/api/preparedness/zones');
  const data = await response.json();
  
  **MPI Risk Scores** | GET | /api/mpi-summary | Nothing | Current flood risk for all wards |
| **Ward Details** | GET | /api/wards/{id} | Ward ID | Full ward infrastructure info |
| **Preparedness (Wards)** | GET | /api/preparedness/all | Nothing | Infrastructure readiness scores |
| **Preparedness (Zones)** | GET | /api/preparedness/zones | Nothing | Zone-level aggregation |
| **GeoJSON Map Data** | GET | /api/risk-data | Nothing | Map features with risk level------|--------|----------|----------------|-----------------|
| Load map | POST | /api/predict/all | Rainfall values | All 272 wards with risk |
| Ward details | GET | /api/wards/{id} | Ward ID | Full ward info |
| Scenario test | POST | /api/predict/all | Custom rainfall | Updated predictions |
| Single ward | POST | /api/predict/ward | Ward ID + rainfall | Ward prediction |
| Live updates | GET | /api/mpi-summary | Nothing | Current MPI summary |
| Preparedness | GET | /api/preparedness/all | Nothing | Infrastructure scores |
| Zones | GET | /api/preparedness/zones | Nothing | Zone aggregation |
| GeoJSON | GET | /api/risk-data | Nothing | Map features |

---

## 📦 Pre-Generated JSON Files

If API is not accessible, use these pre-generated files in `/backend` folder:

1. **`mpi_data_20260112_082520.json`** (53 KB)
   - Real-time flood risk for all 272 wards
   - Current status: All wards LOW risk (0mm rainfall)

2. **`preparedness_all_wards_20260112_082522.json`** (126 KB)
   - Monsoon preparedness for all 272 wards
   - Average: 47.9/100
   - 16 critical wards, 78 poor wards

3. **`preparedness_zones_20260112_082524.json`** (2 KB)
   - Zone-level summary for 3 MCD zones
   - Priority: Zone_E (45.2), Zone_S (47.7), Zone_N (49.8)
**MPI (Monsoon Preparedness Index)** - Real-time flood risk assessment
✅ **Preparedness Scores** - Infrastructure readiness metrics
✅ All endpoints working locally
✅ CORS enabled for frontend
✅ Real-time weather integration (OpenWeather API)
✅ 272 wards with civic data (sewerage, drainage, potholes, historical floods)
✅ Zone-level aggregation (North, South, East zones)

**Local API URL**: `http://localhost:8000`

Test with:
```bash
curl http://localhost:8000/api/mpi-summary
# Returns current MPI scores for all 272 wards

curl http://localhost:8000/api/preparedness/all
# Returns preparedness scores for all wards

curl http://localhost:8000/api/preparedness/zones
# Returns zone-level preparedness summary

Test with:
```bash
curl http://localhost:8000/
# Should return: {"status": "healthy", "model_loaded": true, "wards_count": 272}
```

---

## 🔄 How to Update Data

**Generate fresh MPI and Preparedness scores:**
```bash
cd backend
python calculate_mpi.py
```

This will:
- Fetch real-time weather from OpenWeather API
- Calculate MPI scores for all wards
- Generate monsoon preparedness scores
- Update CSV and JSON files

---

## 🛠️ Production Deployment (Render)

To deploy to Render.com:

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "FastAPI deployment ready"
   git push origin main
   ```

2. **Connect to Render:**
   - Go to https://render.com
   - Create new Web Service
   - Connect your GitHub repo
   - Render will auto-detect `render.yaml`
   - Click "Create Web Service"

3. **Environment Variables:**
   Set in Render dashboard:
   - `OPENWEATHER_API_KEY` = your OpenWeather API key
   - `PYTHON_VERSION` = 3.13.0

4. **Access your API:**
   Your API will be available at: `https://your-app-name.onrender.com`

---

## 📊 Sample Data for Testing

**Ward 038E (Highest Risk)**:
- MPI Score: 36.7/100 (Moderate)
- Preparedness: 25.5/100 (Critical)
- Historical Floods: 8 events
- Drain Density: 0.84 points/km²
- Infrastructure Capacity: 0.0 (needs emergency intervention)

**City-wide Stats**:
- Average MPI: 23.0/100
- Average Preparedness: 47.9/100
- Critical Wards (Preparedness < 30): 16
- High-Risk Wards (MPI > 50): 0 (currently no rainfall)

---

🎉 **Ready for frontend integration!** Your friend has everything needed to build a comprehensive flood prediction dashboard.
