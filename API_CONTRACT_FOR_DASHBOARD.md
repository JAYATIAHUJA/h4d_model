# API Contract: Frontend ↔ Backend

## For Dashboard Developer 📊

This document explains exactly what data to send and what you'll receive for the flood prediction dashboard.

---

## 🎯 Main Dashboard Use Cases

### 1. **Load All Wards on Map (Initial Load)**
**Endpoint**: `GET /api/predict/all`

**What Frontend Sends**: Nothing (GET request)

**What Backend Returns**:
```json
{
  "timestamp": "2026-01-12T10:30:00",
  "total_wards": 272,
  "risk_summary": {
    "low": 196,
    "moderate": 76,
    "high": 0,
    "critical": 0
  },
  "wards": [
    {
      "ward_id": "038E",
      "mpi_score": 39.7,
      "probability": 0.019,
      "risk_level": "moderate",
      "rain_current": 0.0,
      "rain_forecast": 0.0,
      "explanation": "Moderate risk: 8 historical floods, poor drainage (0.84)",
      "lat": 28.6139,
      "lon": 77.2090,
      "ward_name": "Ward_038E"
    },
    // ... 271 more wards
  ]
}
```

**Use in Dashboard**:
- Plot all 272 wards on map with color coding
- Show risk summary counts
- Update every 30 minutes

---

### 2. **Get Single Ward Details (Click on Map)**
**Endpoint**: `GET /api/wards/{ward_id}`

**What Frontend Sends**: Ward ID in URL
```
GET /api/wards/038E
```

**What Backend Returns**:
```json
{
  "ward_id": "038E",
  "ward_name": "Karol Bagh Ward 038E",
  "static_features": {
    "area_km2": 8.93,
    "mean_elevation": 206.2,
    "low_lying_pct": 22.9,
    "drain_density": 0.84,
    "yamuna_distance_km": 0.087,
    "building_density": 1250.5,
    "urbanization_index": 0.75,
    "flood_vulnerability_index": 0.65
  },
  "historical": {
    "flood_count": 8,
    "last_flood": "2023-08-15",
    "monsoon_risk_score": 0.72
  },
  "infrastructure": {
    "sewerage_complaints": 145,
    "drainage_complaints": 98,
    "pothole_count": 12,
    "sewerage_stress_index": 0.68
  },
  "current_risk": {
    "mpi_score": 39.7,
    "probability": 0.019,
    "risk_level": "moderate"
  }
}
```

**Use in Dashboard**:
- Show detailed ward popup/sidebar
- Display infrastructure metrics
- Show historical flood patterns

---

### 3. **Predict with Custom Rainfall (Scenario Testing)**
**Endpoint**: `POST /api/predict/all`

**What Frontend Sends**:
```json
{
  "rainfall": {
    "rain_1h": 25.0,
    "rain_3h": 45.0,
    "rain_6h": 60.0,
    "rain_24h": 75.0,
    "rain_forecast_3h": 15.0
  },
  "timestamp": "2026-01-12T10:30:00"
}
```

**What Backend Returns**:
```json
{
  "timestamp": "2026-01-12T10:30:00",
  "total_wards": 272,
  "risk_summary": {
    "low": 120,
    "moderate": 98,
    "high": 45,
    "critical": 9
  },
  "wards": [
    {
      "ward_id": "038E",
      "mpi_score": 76.2,
      "probability": 0.65,
      "risk_level": "high",
      "rain_current": 25.0,
      "rain_forecast": 15.0,
      "model_contribution": 26.0,
      "rainfall_contribution": 15.0,
      "historical_contribution": 15.0,
      "infrastructure_contribution": 12.4,
      "vulnerability_contribution": 7.8,
      "explanation": "HIGH RISK: Heavy rainfall (45mm/3h) + poor drainage + 8 past floods"
    },
    // ... all wards with updated predictions
  ]
}
```

**Use in Dashboard**:
- "What-if" scenario slider
- User adjusts rainfall values → see impact on all wards
- Show MPI breakdown (pie chart of 5 components)

---

### 4. **Get Ward Prediction (Single Ward with Rainfall)**
**Endpoint**: `POST /api/predict/ward`

**What Frontend Sends**:
```json
{
  "ward_id": "038E",
  "rainfall": {
    "rain_1h": 25.0,
    "rain_3h": 45.0,
    "rain_6h": 60.0,
    "rain_24h": 75.0,
    "rain_forecast_3h": 15.0
  }
}
```

**What Backend Returns**:
```json
{
  "ward_id": "038E",
  "probability": 0.65,
  "risk_level": "high",
  "mpi_score": 76.2,
  "rain_1h": 25.0,
  "rain_3h": 45.0,
  "model_contribution": 26.0,
  "rainfall_contribution": 15.0,
  "historical_contribution": 15.0,
  "infrastructure_contribution": 12.4,
  "vulnerability_contribution": 7.8,
  "explanation": "High flood risk: Heavy rainfall (45mm/3h) combined with poor drainage (0.84) and 8 historical flood events"
}
```

**Use in Dashboard**:
- Detailed ward analysis
- Show MPI breakdown components
- Explain risk factors

---

## 🔥 Real-Time Updates

### 5. **Get Current MPI Scores (Live Weather)**
**Endpoint**: `GET /api/mpi-summary`

**What Frontend Sends**: Nothing (GET request)

**What Backend Returns**:
```json
{
  "timestamp": "2026-01-12T10:30:00",
  "weather": {
    "current_rain_mm": 12.5,
    "forecast_3h_mm": 8.0,
    "intensity": "moderate"
  },
  "risk_distribution": {
    "low": 196,
    "moderate": 76,
    "high": 0,
    "critical": 0
  },
  "top_10_high_risk": [
    {
      "ward_id": "038E",
      "mpi_score": 39.7,
      "risk_level": "moderate",
      "probability": 0.019
    },
    // ... 9 more
  ],
  "avg_mpi": 26.7,
  "max_mpi": 39.7
}
```

**Use in Dashboard**:
- Auto-refresh every 30 mins
- Show current weather data
- Alert if high-risk wards increase

---

### 6. **Get GeoJSON for Map**
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
        "ward_name": "Karol Bagh 038E",
        "mpi_score": 39.7,
        "risk_level": "moderate",
        "probability": 0.019,
        "color": "#FFA500"
      }
    },
    // ... 271 more wards
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
   - 272 ward markers color-coded by risk
   - Legend: Low (green), Moderate (yellow), High (orange), Critical (red)
   - Click ward → show popup with details

2. **Rainfall Slider** (Scenario Testing)
   - Sliders for: rain_1h, rain_3h, rain_6h
   - "Calculate" button → POST to `/api/predict/all`
   - Map updates with new risk levels

3. **Ward Details Sidebar**
   - Click ward → GET `/api/wards/{ward_id}`
   - Show:
     - Ward name, elevation, drainage
     - Historical floods count
     - Civic complaints (sewerage, drainage, potholes)
     - Current MPI breakdown (pie chart)

4. **Top 10 High-Risk List**
   - From `/api/mpi-summary`
   - Auto-refresh every 30 mins
   - Sort by MPI score

5. **MPI Breakdown Chart** (for selected ward)
   - Pie chart showing:
     - Model Prediction: 40%
     - Rainfall: 20%
     - History: 15%
     - Infrastructure: 15%
     - Vulnerability: 10%

---

## 🎨 Color Coding

```javascript
function getRiskColor(mpi_score) {
  if (mpi_score < 30) return '#4CAF50';      // Green - Low
  if (mpi_score < 50) return '#FFC107';      // Yellow - Moderate
  if (mpi_score < 70) return '#FF9800';      // Orange - High
  return '#F44336';                          // Red - Critical
}

function getRiskLevel(mpi_score) {
  if (mpi_score < 30) return 'Low';
  if (mpi_score < 50) return 'Moderate';
  if (mpi_score < 70) return 'High';
  return 'Critical';
}
```

---

## 🔄 Recommended Update Intervals

- **Map data**: Every 30 minutes (real-time weather changes)
- **Ward details**: On-demand (when user clicks)
- **Scenario testing**: On-demand (when user adjusts sliders)
- **Top 10 list**: Every 30 minutes

---

## 📱 Example Frontend Code

### Load All Wards on Map:
```javascript
async function loadWards() {
  const response = await fetch('https://delhi-flood-api.onrender.com/api/predict/all');
  const data = await response.json();
  
  data.wards.forEach(ward => {
    const marker = L.marker([ward.lat, ward.lon], {
      icon: L.icon({
        iconUrl: getRiskColor(ward.mpi_score)
      })
    });
    
    marker.bindPopup(`
      <h3>${ward.ward_name}</h3>
      <p>MPI Score: ${ward.mpi_score}</p>
      <p>Risk: ${ward.risk_level}</p>
      <p>${ward.explanation}</p>
    `);
    
    marker.addTo(map);
  });
}
```

### Scenario Testing:
```javascript
async function testScenario() {
  const rain_1h = document.getElementById('rain-slider').value;
  
  const response = await fetch('https://delhi-flood-api.onrender.com/api/predict/all', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      rainfall: {
        rain_1h: parseFloat(rain_1h),
        rain_3h: parseFloat(rain_1h) * 2,
        rain_6h: parseFloat(rain_1h) * 3,
        rain_24h: parseFloat(rain_1h) * 4,
        rain_forecast_3h: parseFloat(rain_1h) * 0.5
      }
    })
  });
  
  const data = await response.json();
  updateMap(data.wards);
}
```

---

## ⚡ Quick Reference Table

| Use Case | Method | Endpoint | Frontend Sends | Backend Returns |
|----------|--------|----------|----------------|-----------------|
| Load map | GET | `/api/predict/all` | Nothing | All 272 wards with MPI |
| Ward details | GET | `/api/wards/{id}` | Ward ID | Full ward info |
| Scenario test | POST | `/api/predict/all` | Rainfall values | Updated predictions |
| Single ward | POST | `/api/predict/ward` | Ward ID + rainfall | Ward prediction |
| Live updates | GET | `/api/mpi-summary` | Nothing | Current MPI summary |
| GeoJSON | GET | `/api/risk-data` | Nothing | Map features |

---

## 🚀 Backend Status

✅ Model deployed (cross-platform compatible)
✅ All endpoints working
✅ CORS enabled for frontend
✅ Real-time weather integration
✅ 272 wards with civic data

**API Base URL**: `https://delhi-flood-api.onrender.com`

Tell your friend to test with:
```bash
curl https://delhi-flood-api.onrender.com/api/health
```

Should return: `"model_loaded": true` ✅
