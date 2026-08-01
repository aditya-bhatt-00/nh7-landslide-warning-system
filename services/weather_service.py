import requests
from typing import Dict, Any

# Rudraprayag Corridor Coordinates
LATITUDE = 30.285
LONGITUDE = 78.981

def get_live_precipitation() -> Dict[str, Any]:
    """
    Fetches real-time precipitation and 24h forecast rainfall from Open-Meteo API.
    Zero-cost, no API key required.
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current=precipitation,rain&hourly=precipitation&forecast_days=1"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        current_precip = data.get("current", {}).get("precipitation", 0.0)
        hourly_precip = data.get("hourly", {}).get("precipitation", [])
        tot_24h_precip = sum(hourly_precip[:24]) if hourly_precip else 0.0
        
        # Calculate dynamic rain risk factor (0.0 to 1.0 scale)
        # >50mm in 24h is severe monsoon risk in the Himalayas
        rain_hazard_factor = min(tot_24h_precip / 50.0, 1.0)
        
        return {
            "status": "success",
            "current_rain_mm_hr": current_precip,
            "accumulated_24h_rain_mm": round(tot_24h_precip, 2),
            "rain_hazard_factor": round(rain_hazard_factor, 2)
        }
    except Exception as e:
        # Fallback in case of network issue
        return {
            "status": "fallback",
            "current_rain_mm_hr": 0.0,
            "accumulated_24h_rain_mm": 5.0, # Normal nominal baseline
            "rain_hazard_factor": 0.10,
            "error": str(e)
        }