import os
import pickle
import numpy as np
import pandas as pd
import geopandas as gpd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.weather_service import get_live_precipitation

app = FastAPI(
    title="NH-58 Landslide Early Warning System API",
    description="Backend service serving real-time hazard scores and spatial predictions.",
    version="1.0.0"
)

# Enable CORS for frontend dashboard (Next.js / Leaflet)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Trained XGBoost Model
MODEL_PATH = os.path.join("models", "xgboost_landslide_model.pkl")
GEOJSON_PATH = os.path.join("data", "processed", "nh58_segments_features.geojson")

try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    print("✅ Successfully loaded XGBoost Model.")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    model = None

# Pydantic Input Model for Custom Segment Inference
class RiskPredictionRequest(BaseModel):
    mean_elevation_m: float
    mean_slope_deg: float
    max_slope_deg: float
    dist_to_river_m: float
    dist_to_landslide_m: float


@app.get("/")
def read_root():
    return {
        "system": "NH-58 Landslide Early Warning Service",
        "corridor": "Rudraprayag - Chamoli (50km)",
        "status": "OPERATIONAL"
    }


@app.get("/api/weather")
def fetch_weather():
    """Fetch live weather and rain hazard metrics from Open-Meteo."""
    return get_live_precipitation()


@app.get("/api/segments")
def get_all_segments():
    """Returns all 131 corridor segments enriched with live dynamic risk scores."""
    if not os.path.exists(GEOJSON_PATH):
        raise HTTPException(status_code=44, detail="Segments GeoJSON not found.")
    
    gdf = gpd.read_file(GEOJSON_PATH)
    weather_info = get_live_precipitation()
    rain_factor = weather_info["rain_hazard_factor"]

    # Extract features for batch model prediction
    features = gdf[['mean_elevation_m', 'mean_slope_deg', 'max_slope_deg', 'dist_to_river_m', 'dist_to_landslide_m']]
    
    # Calculate static XGBoost risk probability
    static_probs = model.predict_proba(features)[:, 1] if model else np.zeros(len(gdf))
    
    # Compute Dynamic Landslide Risk Index (DLRI)
    dlri_scores = (static_probs * 0.6) + (rain_factor * 0.4)
    
    # Add metrics to response GeoJSON
    gdf['static_risk_prob'] = np.round(static_probs, 3)
    gdf['dynamic_risk_score'] = np.round(dlri_scores, 3)
    
    # Assign Hazard Categories
    def assign_category(score):
        if score >= 0.70: return "HIGH HAZARD"
        elif score >= 0.40: return "MODERATE HAZARD"
        else: return "LOW RISK"
        
    gdf['hazard_category'] = gdf['dynamic_risk_score'].apply(assign_category)

    return {
        "type": "FeatureCollection",
        "weather_summary": weather_info,
        "features": gdf.__geo_interface__["features"]
    }


@app.post("/api/predict")
def predict_hazard(data: RiskPredictionRequest):
    """Calculates risk score for custom terrain input values."""
    if not model:
        raise HTTPException(status_code=500, detail="Model is not initialized.")
    
    input_data = pd.DataFrame([[
        data.mean_elevation_m,
        data.mean_slope_deg,
        data.max_slope_deg,
        data.dist_to_river_m,
        data.dist_to_landslide_m
    ]], columns=['mean_elevation_m', 'mean_slope_deg', 'max_slope_deg', 'dist_to_river_m', 'dist_to_landslide_m'])

    prob = float(model.predict_proba(input_data)[0, 1])
    weather_info = get_live_precipitation()
    rain_factor = weather_info["rain_hazard_factor"]
    
    dynamic_dlri = (prob * 0.6) + (rain_factor * 0.4)

    return {
        "static_xgb_probability": round(prob, 4),
        "rain_hazard_factor": rain_factor,
        "dynamic_landslide_risk_index": round(dynamic_dlri, 4),
        "hazard_category": "HIGH HAZARD" if dynamic_dlri >= 0.7 else ("MODERATE HAZARD" if dynamic_dlri >= 0.4 else "LOW RISK")
    }

from pydantic import BaseModel

class AlertSubscription(BaseModel):
    phone: str
    preferred_zone: str

@app.post("/api/subscribe-alerts")
def subscribe_alerts(sub: AlertSubscription):
    # Here you can store phone numbers in a lightweight database (SQLite/PostgreSQL)
    # or integrate directly with Twilio API for sending WhatsApp/SMS messages
    print(f"[NEW SUBSCRIPTION] Registered phone: {sub.phone} for zone: {sub.preferred_zone}")
    return {
        "status": "success", 
        "message": f"Alert subscription confirmed for {sub.phone} on route {sub.preferred_zone}"
    }