"""
Delhi Flood Monitor API
=======================

FastAPI backend for the Delhi Flood Early Warning System.
Serves Model 1 predictions and ward risk data.

Author: Delhi Flood Monitoring Team
Version: 1.0
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path
import numpy as np

# Import model components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "model"))
from flood_model import FloodFailureModel, FeatureEngineer, ModelConfig, ALL_FEATURES
from data_integration import DataPipeline, DataConfig

# =============================================================================
# APP SETUP
# =============================================================================

app = FastAPI(
    title="Delhi Flood Monitor API",
    description="Real-time flood risk prediction for Delhi wards",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model and data instances
model: Optional[FloodFailureModel] = None
pipeline: Optional[DataPipeline] = None
feature_engineer: Optional[FeatureEngineer] = None
ward_static_data: Optional[Dict] = None
ward_historical_data: Optional[Dict] = None


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class RainfallInput(BaseModel):
    """Input for rainfall-based prediction."""
    rain_1h: float = 0  # mm
    rain_3h: float = 0  # mm
    rain_6h: float = 0  # mm
    rain_24h: float = 0  # mm
    rain_forecast_3h: float = 0  # mm


class WardPredictionRequest(BaseModel):
    """Request for ward-specific prediction."""
    ward_id: str
    rainfall: RainfallInput
    timestamp: Optional[str] = None


class BatchPredictionRequest(BaseModel):
    """Request for batch ward predictions."""
    rainfall: RainfallInput  # Same rainfall for all wards (simplification)
    timestamp: Optional[str] = None


class WardRisk(BaseModel):
    """Risk assessment for a single ward."""
    ward_id: str
    probability: float
    risk_level: str  # low, moderate, high, critical
    rain_1h: float
    rain_3h: float
    explanation: str


class AllWardsResponse(BaseModel):
    """Response with all ward predictions."""
    timestamp: str
    total_wards: int
    risk_summary: Dict[str, int]
    wards: List[WardRisk]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    wards_count: int
    timestamp: str


class SimplePredictionRequest(BaseModel):
    """Simple prediction request for external integrations."""
    rainfall: float  # mm of rainfall
    water_logging_reports: int  # number of reports
    pothole_count: int  # number of potholes


class SimplePredictionResponse(BaseModel):
    """Simple prediction response."""
    mpi_score: float  # 0.0 to 1.0
    risk_level: str  # Low, Moderate, High, Critical


# =============================================================================
# STARTUP/SHUTDOWN
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Load model and data on startup."""
    global model, pipeline, feature_engineer, ward_static_data, ward_historical_data
    
    print("=" * 60)
    print("Starting Delhi Flood Monitor API...")
    print("=" * 60)
    
    # Load trained model
    model_path = Path(__file__).parent.parent / "model" / "artifacts" / "flood_model_v1.pkl"
    
    if model_path.exists():
        print(f"Loading model from {model_path}")
        model = FloodFailureModel.load(str(model_path))
        feature_engineer = model.feature_engineer
        print("  Model loaded successfully!")
    else:
        print(f"WARNING: Model not found at {model_path}")
        print("  Run train_model_1.py first to train the model.")
        model = None
    
    # Initialize data pipeline
    print("\nInitializing data pipeline...")
    try:
        pipeline = DataPipeline()
        pipeline.initialize()
        
        # Cache ward data as dictionaries for fast lookup
        ward_static, ward_historical = pipeline.get_ward_data()
        ward_static_data = ward_static.to_dict('index')
        ward_historical_data = ward_historical.to_dict('index')
        
        print(f"  Loaded {len(ward_static_data)} wards")
    except Exception as e:
        print(f"  Data pipeline initialization failed: {e}")
        ward_static_data = {}
        ward_historical_data = {}
    
    print("\nAPI ready!")
    print("=" * 60)


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        model_loaded=model is not None,
        wards_count=len(ward_static_data) if ward_static_data else 0,
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/health", response_model=HealthResponse)
async def api_health():
    """API health check."""
    return await health_check()


@app.post("/predict", response_model=SimplePredictionResponse)
async def simple_predict(request: SimplePredictionRequest):
    """
    Simple prediction endpoint for external integrations.
    
    Takes rainfall, water logging reports, and pothole count,
    returns MPI score (0-1) and risk level.
    
    Example:
        POST /predict
        {
          "rainfall": 42.5,
          "water_logging_reports": 12,
          "pothole_count": 5
        }
        
        Response:
        {
          "mpi_score": 0.87,
          "risk_level": "High"
        }
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Compute MPI score from inputs
    # Normalize inputs to 0-1 scale
    rainfall_norm = min(request.rainfall / 100.0, 1.0)  # Cap at 100mm
    logging_norm = min(request.water_logging_reports / 50.0, 1.0)  # Cap at 50 reports
    pothole_norm = min(request.pothole_count / 20.0, 1.0)  # Cap at 20 potholes
    
    # Calculate MPI with weighted components
    # 50% rainfall, 30% waterlogging, 20% infrastructure (potholes)
    mpi_score = (
        0.50 * rainfall_norm +
        0.30 * logging_norm +
        0.20 * pothole_norm
    )
    
    # Determine risk level
    if mpi_score >= 0.75:
        risk_level = "Critical"
    elif mpi_score >= 0.50:
        risk_level = "High"
    elif mpi_score >= 0.25:
        risk_level = "Moderate"
    else:
        risk_level = "Low"
    
    return SimplePredictionResponse(
        mpi_score=round(mpi_score, 2),
        risk_level=risk_level
    )


@app.get("/api/wards", response_model=List[str])
async def get_ward_ids():
    """Get list of all ward IDs."""
    if not ward_static_data:
        return []
    return list(ward_static_data.keys())


@app.get("/api/wards/{ward_id}")
async def get_ward_info(ward_id: str):
    """Get static information about a specific ward."""
    if not ward_static_data or ward_id not in ward_static_data:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")
    
    static = ward_static_data[ward_id]
    historical = ward_historical_data.get(ward_id, {})
    
    return {
        "ward_id": ward_id,
        "static_features": static,
        "historical_features": historical
    }


@app.post("/api/predict/ward", response_model=WardRisk)
async def predict_ward(request: WardPredictionRequest):
    """Predict flood risk for a specific ward."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if not ward_static_data or request.ward_id not in ward_static_data:
        raise HTTPException(status_code=404, detail=f"Ward {request.ward_id} not found")
    
    # Get ward features
    static_feats = ward_static_data[request.ward_id]
    hist_feats = ward_historical_data.get(request.ward_id, {
        'hist_flood_freq': 0,
        'monsoon_risk_score': 0.5,
        'complaint_baseline': 5
    })
    
    # Parse timestamp
    if request.timestamp:
        timestamp = datetime.fromisoformat(request.timestamp)
    else:
        timestamp = datetime.now()
    
    # Compute features
    rainfall_feats = {
        'rain_1h': request.rainfall.rain_1h,
        'rain_3h': request.rainfall.rain_3h,
        'rain_6h': request.rainfall.rain_6h,
        'rain_24h': request.rainfall.rain_24h,
        'rain_intensity': request.rainfall.rain_1h,
        'rain_forecast_3h': request.rainfall.rain_forecast_3h
    }
    
    temporal_feats = feature_engineer.compute_temporal_features(timestamp)
    
    # Create feature vector
    X = feature_engineer.create_feature_vector(
        rainfall_feats, static_feats, hist_feats, temporal_feats
    )
    
    # Predict
    probability = float(model.predict_proba(X)[0])
    risk_level = model.predict_risk_level(X.reshape(1, -1))[0]
    explanation_data = model.explain_prediction(X)
    
    return WardRisk(
        ward_id=request.ward_id,
        probability=probability,
        risk_level=risk_level,
        rain_1h=request.rainfall.rain_1h,
        rain_3h=request.rainfall.rain_3h,
        explanation=explanation_data['explanation']
    )


@app.post("/api/predict/all", response_model=AllWardsResponse)
async def predict_all_wards(request: BatchPredictionRequest):
    """Predict flood risk for all wards."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if not ward_static_data:
        raise HTTPException(status_code=503, detail="Ward data not loaded")
    
    # Parse timestamp
    if request.timestamp:
        timestamp = datetime.fromisoformat(request.timestamp)
    else:
        timestamp = datetime.now()
    
    # Compute temporal features once
    temporal_feats = feature_engineer.compute_temporal_features(timestamp)
    
    # Rainfall features (same for all wards in this simplified version)
    rainfall_feats = {
        'rain_1h': request.rainfall.rain_1h,
        'rain_3h': request.rainfall.rain_3h,
        'rain_6h': request.rainfall.rain_6h,
        'rain_24h': request.rainfall.rain_24h,
        'rain_intensity': request.rainfall.rain_1h,
        'rain_forecast_3h': request.rainfall.rain_forecast_3h
    }
    
    results = []
    risk_counts = {'low': 0, 'moderate': 0, 'high': 0, 'critical': 0}
    
    for ward_id, static_feats in ward_static_data.items():
        hist_feats = ward_historical_data.get(ward_id, {
            'hist_flood_freq': 0,
            'monsoon_risk_score': 0.5,
            'complaint_baseline': 5
        })
        
        # Create feature vector
        X = feature_engineer.create_feature_vector(
            rainfall_feats, static_feats, hist_feats, temporal_feats
        )
        
        # Predict
        probability = float(model.predict_proba(X)[0])
        risk_level = model.predict_risk_level(X.reshape(1, -1))[0]
        
        risk_counts[risk_level] += 1
        
        results.append(WardRisk(
            ward_id=ward_id,
            probability=probability,
            risk_level=risk_level,
            rain_1h=request.rainfall.rain_1h,
            rain_3h=request.rainfall.rain_3h,
            explanation=f"Risk: {risk_level.upper()} ({probability*100:.1f}%)"
        ))
    
    # Sort by probability descending
    results.sort(key=lambda x: x.probability, reverse=True)
    
    return AllWardsResponse(
        timestamp=timestamp.isoformat(),
        total_wards=len(results),
        risk_summary=risk_counts,
        wards=results
    )


@app.get("/api/risk-data")
async def get_risk_data():
    """
    Get current ward-wise MPI risk scores.
    Returns the latest MPI calculation results from calculate_mpi.py.
    """
    try:
        # Load latest MPI scores
        mpi_file = Path(__file__).parent.parent / "data" / "processed" / "mpi_scores_latest.csv"
        
        if not mpi_file.exists():
            # Fallback to static JSON if MPI not calculated yet
            risk_file = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "ward_risk.json"
            if risk_file.exists():
                with open(risk_file) as f:
                    return json.load(f)
            return {}
        
        import pandas as pd
        df = pd.read_csv(mpi_file)
        
        # Convert to frontend format
        risk_data = {}
        for _, row in df.iterrows():
            risk_data[row['ward_id']] = {
                "risk_score": float(row['mpi_score']),
                "rain_mm": float(row.get('current_rain_mm', 0) + row.get('forecast_rain_mm', 0)),
                "status": row['risk_level'],
                "model_prob": float(row['model_prob']) * 100,
                "flood_history": int(row['hist_flood_count']),
                "drain_density": float(row['drain_density'])
            }
        
        return risk_data
        
    except Exception as e:
        print(f"Error loading risk data: {e}")
        return {}


@app.get("/api/mpi-summary")
async def get_mpi_summary():
    """Get summary statistics of current MPI scores."""
    try:
        mpi_file = Path(__file__).parent.parent / "data" / "processed" / "mpi_scores_latest.csv"
        
        if not mpi_file.exists():
            raise HTTPException(status_code=404, detail="MPI data not found")
        
        import pandas as pd
        df = pd.read_csv(mpi_file)
        
        risk_counts = df['risk_level'].value_counts().to_dict()
        
        return {
            "total_wards": len(df),
            "risk_distribution": {
                "Low": risk_counts.get("Low", 0),
                "Moderate": risk_counts.get("Moderate", 0),
                "High": risk_counts.get("High", 0),
                "Critical": risk_counts.get("Critical", 0)
            },
            "mpi_stats": {
                "mean": float(df['mpi_score'].mean()),
                "min": float(df['mpi_score'].min()),
                "max": float(df['mpi_score'].max())
            },
            "updated_at": df['timestamp'].iloc[0] if 'timestamp' in df.columns else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# =============================================================================
# STARTUP & SHUTDOWN
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Load model and data on startup."""
    print("Loading model and data...")
    global model, pipeline, feature_engineer, ward_static_data, ward_historical_data
async def get_feature_importance():
    """Get feature importance from the trained model."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    importance = model.get_feature_importance()
    
    # Sort by importance
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "features": [
            {"name": name, "importance": round(imp, 4)}
            for name, imp in sorted_importance
        ]
    }


@app.get("/api/model-info")
async def get_model_info():
    """Get information about the trained model."""
    metrics_path = Path(__file__).parent.parent / "model" / "artifacts" / "training_metrics.json"
    
    if not metrics_path.exists():
        return {"error": "Metrics file not found"}
    
    with open(metrics_path) as f:
        metrics = json.load(f)
    
    return {
        "model_version": "1.0",
        "trained_at": metrics.get("trained_at"),
        "n_features": metrics.get("n_features"),
        "n_samples": metrics.get("n_samples"),
        "test_metrics": metrics.get("test_metrics"),
        "feature_names": metrics.get("feature_names")
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
