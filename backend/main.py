import asyncio
import math
import time
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.worker import send_telegram_alert  # only the Telegram sender lives in worker.py now

# ============================================================
# Initialize FastAPI App
# ============================================================
app = FastAPI(title="NH-7 Landslide Early Warning System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from Vercel/any domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Geographic coordinate path for NH-7 [longitude, latitude]
# ============================================================
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

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast?"
    "latitude=30.285&longitude=78.980"
    "&current=precipitation,rain"
    "&hourly=precipitation"
    "&past_days=1"
    "&timezone=auto"
)
OPEN_METEO_HEADERS = {
    "User-Agent": "NH7-Landslide-System/1.0 (Contact: aditya.bhatt.tech@gmail.com)"
}

REFRESH_INTERVAL_SECONDS = 300  # 5 minutes
REQUEST_TIMEOUT_SECONDS = 20    # was 10 — too tight for Render cold starts
MAX_RETRIES = 2
HIGH_RISK_THRESHOLD = 0.75

# ============================================================
# In-memory weather cache
# ============================================================
weather_cache = {
    "current_rain_mm_hr": 0.0,
    "rain_24h_mm": 0.0,
    "status": "initializing",   # "ok" | "stale" | "error"
    "last_updated_unix": None,
    "last_error": None,
}


async def fetch_weather_once():
    """Single attempt at hitting Open-Meteo. Uses to_thread to prevent server freeze."""
    response = await asyncio.to_thread(
        requests.get, OPEN_METEO_URL, headers=OPEN_METEO_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS
    )
    response.raise_for_status()
    res = response.json()

    current_rain = res.get("current", {}).get("precipitation", 0.0)
    hourly_precip = res.get("hourly", {}).get("precipitation", [])
    if len(hourly_precip) >= 24:
        rain_24h = round(sum(hourly_precip[-24:]), 1)
    else:
        rain_24h = round(sum(hourly_precip), 1)

    return current_rain, rain_24h


async def refresh_weather_cache():
    """Fetches live weather with retries and updates the cache in place asynchronously."""
    last_exception = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            current_rain, rain_24h = await fetch_weather_once()
            weather_cache["current_rain_mm_hr"] = current_rain
            weather_cache["rain_24h_mm"] = rain_24h
            weather_cache["status"] = "ok"
            weather_cache["last_updated_unix"] = time.time()
            weather_cache["last_error"] = None
            print(f"✅ Weather refreshed: current={current_rain}mm/hr, 24h={rain_24h}mm")
            return
        except Exception as e:
            last_exception = e
            print(f"⚠️ Weather fetch attempt {attempt}/{MAX_RETRIES} failed: {e}")

    # All retries failed
    weather_cache["status"] = "error" if weather_cache["last_updated_unix"] is None else "stale"
    weather_cache["last_error"] = str(last_exception)
    print(f"❌ Weather refresh failed after {MAX_RETRIES} attempts. Serving last known data. Error: {last_exception}")


async def weather_refresh_loop():
    """Background task: refreshes the weather cache every REFRESH_INTERVAL_SECONDS."""
    while True:
        await refresh_weather_cache()
        check_and_dispatch_alert()
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)


def check_and_dispatch_alert():
    """Uses the current cache to check for high-risk segments and fire a Telegram alert."""
    current_rain = weather_cache["current_rain_mm_hr"]
    rain_24h = weather_cache["rain_24h_mm"]

    micro_segments = generate_500m_segments(NH7_ANCHOR_WAYPOINTS, current_rain, rain_24h)
    high_risk_count = sum(1 for seg in micro_segments if seg["hazard_score"] >= HIGH_RISK_THRESHOLD)

    if high_risk_count > 0:
        alert_msg = (
            f"🚨 *NH-7 SAFETY ALERT* 🚨\n\n"
            f"*{high_risk_count} High-Risk landslide zones* detected between Rudraprayag and Chamoli.\n\n"
            f"🌧️ *Live Rain:* {current_rain} mm/hr\n"
            f"🌊 *24h Total:* {rain_24h} mm\n\n"
            f"⚠️ _Night travel is strictly restricted. Seek staging zones immediately._"
        )
        send_telegram_alert(alert_msg)


@app.on_event("startup")
async def start_background_refresh():
    # Await the first fetch so the cache is hot immediately, but asynchronously
    await refresh_weather_cache()
    asyncio.create_task(weather_refresh_loop())


# ============================================================
# Segment generation
# ============================================================
def generate_500m_segments(anchors, current_rain, rain_24h, target_segment_len_km=0.5):
    all_points = []
    for i in range(len(anchors) - 1):
        p1, p2 = anchors[i], anchors[i + 1]
        dx = (p2[0] - p1[0]) * 111 * math.cos(math.radians(p1[1]))
        dy = (p2[1] - p1[1]) * 111
        dist_km = math.sqrt(dx * dx + dy * dy)
        num_subdivisions = max(1, int(dist_km / target_segment_len_km))

        for step in range(num_subdivisions):
            t = step / num_subdivisions
            lon = p1[0] + t * (p2[0] - p1[0])
            lat = p1[1] + t * (p2[1] - p1[1])
            all_points.append([round(lon, 5), round(lat, 5)])

    last_anchor = anchors[-1]
    all_points.append([round(last_anchor[0], 5), round(last_anchor[1], 5)])

    segments = []
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
            "coords": [all_points[idx], all_points[idx + 1]]
        })

    return segments


# ============================================================
# Routes
# ============================================================
@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "NH-7 Landslide Early Warning System API",
        "docs": "/docs"
    }


@app.get("/ping")
async def ping():
    return {"status": "alive", "system": "NH-7 Early Warning API"}


@app.get("/api/segments")
def get_segments(simulate_rain: bool = False):
    """Provides segment data to the UI for mapping. Reads directly from cache."""
    current_rain = weather_cache["current_rain_mm_hr"]
    rain_24h = weather_cache["rain_24h_mm"]

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
            "rain_24h_mm": rain_24h,
            "status": weather_cache["status"],
            "last_updated_unix": weather_cache["last_updated_unix"],
            "last_error": weather_cache["last_error"] if simulate_rain is False else None,
        },
        "total_segments": len(features),
        "features": features
    }