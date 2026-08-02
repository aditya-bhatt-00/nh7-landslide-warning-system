from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import math
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for all origins so Vercel can fetch data smoothly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from Vercel/any domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your existing routes below...
# Initialize FastAPI App
app = FastAPI(title="NH-7 Landslide Early Warning System API")

# Configure CORS so your Next.js frontend can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Geographic coordinate path for NH-7
NH7_ANCHOR_WAYPOINTS = [
    (78.980, 30.285),  # Rudraprayag
    (79.030, 30.280),
    (79.070, 30.275),  # Raturi Sera
    (79.110, 30.280),
    (79.155, 30.288),  # Gauchar
    (79.180, 30.270),
    (79.218, 30.258),  # Karnaprayag
    (79.250, 30.280),
    (79.280, 30.300),  # Langasu
    (79.310, 30.325),
    (79.330, 30.338),  # Chamoli
]

def generate_500m_segments(anchors, current_rain, rain_24h, target_segment_len_km=0.5):
    all_points = []
    # Interpolate path into smaller discrete points
    for i in range(len(anchors) - 1):
        p1, p2 = anchors[i], anchors[i+1]
        dx = (p2[0] - p1[0]) * 111 * math.cos(math.radians(p1[1]))
        dy = (p2[1] - p1[1]) * 111
        dist_km = math.sqrt(dx*dx + dy*dy)
        num_subdivisions = max(1, int(dist_km / target_segment_len_km))
        
        for step in range(num_subdivisions):
            t = step / num_subdivisions
            lon = p1[0] + t * (p2[0] - p1[0])
            lat = p1[1] + t * (p2[1] - p1[1])
            all_points.append([round(lon, 5), round(lat, 5)])
            
    all_points.append(anchors[-1])
    
    segments = []
    # Generate 500m segments with Dynamic Hazard Scoring
    for idx in range(len(all_points) - 1):
        base_vulnerability = 0.20 + (math.sin(idx * 0.15) * 0.15)
        rain_factor = (rain_24h / 150.0) + (current_rain / 20.0)
        
        hazard_score = round(base_vulnerability + rain_factor, 2)
        hazard_score = max(0.1, min(0.95, hazard_score))
        
        chainage_start = idx * 0.5
        chainage_end = (idx + 1) * 0.5
        
        segments.append({
            "segment_id": f"NH7-KM-{chainage_start:.1f}to{chainage_end:.1f}",
            "chainage": f"KM {chainage_start:.1f} - {chainage_end:.1f}",
            "hazard_score": hazard_score,
            "coords": [all_points[idx], all_points[idx+1]]
        })
        
    return segments


@app.get("/ping")
async def ping():
    """Health check endpoint."""
    return {"status": "alive", "system": "NH-7 Early Warning API"}


@app.get("/api/segments")
def get_segments(simulate_rain: bool = False):
    """Provides segment data to the UI for mapping."""
    current_rain = 0.0
    rain_24h = 0.0
    
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast?"
            "latitude=30.285&longitude=78.980"
            "&current=precipitation,rain"
            "&hourly=precipitation"
            "&past_days=1"
            "&timezone=auto"
        )
        res = requests.get(url, timeout=5).json()
        current_rain = res.get("current", {}).get("precipitation", 0.0)
        
        hourly_precip = res.get("hourly", {}).get("precipitation", [])
        if len(hourly_precip) >= 24:
            rain_24h = round(sum(hourly_precip[-24:]), 1)
        else:
            rain_24h = round(sum(hourly_precip), 1)
            
    except Exception as e:
        print("Telemetry Fetch Error:", e)

    if simulate_rain:
        current_rain = 14.2  
        rain_24h = 48.5      

    micro_segments = generate_500m_segments(NH7_ANCHOR_WAYPOINTS, current_rain, rain_24h)

    features = []
    for seg in micro_segments:
        features.append({
            "type": "Feature",
            "properties": {
                "segment_id": seg["segment_id"],
                "chainage": seg["chainage"],
                "hazard_score": seg["hazard_score"],
                "current_rain": current_rain,
                "rain_24h": rain_24h,
                "weather_summary": f"Live Rain: {current_rain} mm/hr | 24h Total: {rain_24h} mm"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": seg["coords"]
            }
        })

    return {
        "type": "FeatureCollection",
        "telemetry": {
            "current_rain_mm_hr": current_rain,
            "rain_24h_mm": rain_24h
        },
        "total_segments": len(features),
        "features": features
    }